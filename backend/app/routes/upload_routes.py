import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.settings import OUTPUT_DIR, UPLOAD_DIR
from app.database.db import get_db
from app.models.document_model import Document
from app.models.history_model import History
from app.models.user_model import User
from app.routes.editor_routes import ensure_edit_allowed, register_edit_usage
from app.services.command_service import normalize_task, parse_command
from app.services.convert_service import process_document, process_multiple_images_to_pdf
from app.services.storage_service import save_upload
from app.utils.file_detector import detect_file_type
from app.utils.validators import validate_filename


router = APIRouter(tags=["upload"])

GUEST_UPLOAD_LIMIT_BYTES = 3 * 1024 * 1024
USER_UPLOAD_LIMIT_BYTES = 70 * 1024 * 1024

TASK_FILE_TYPES = {
    "pdf_to_word": {"pdf"},
    "pdf_to_csv": {"pdf"},
    "pdf_to_excel": {"pdf"},
    "pdf_to_powerpoint": {"pdf"},
    "word_to_pdf": {"word"},
    "powerpoint_to_pdf": {"powerpoint"},
    "heic_to_jpg": {"heic"},
    "heic_to_png": {"heic"},
    "jpg_to_heic": {"image"},
    "png_to_heic": {"image"},
    "excel_to_csv": {"excel"},
    "excel_to_pdf": {"excel"},
    "csv_to_excel": {"csv"},
    "csv_to_pdf": {"csv"},
    "markdown_to_pdf": {"markdown"},
    "markdown_to_word": {"markdown"},
    "markdown_to_html": {"markdown"},
    "markdown_to_text": {"markdown"},
    "markdown_to_powerpoint": {"markdown"},
    "jpg_to_png": {"image"},
    "png_to_jpg": {"image"},
    "pdf_to_zip": {"pdf"},
    "pdf_compress": {"pdf"},
    "image_compress": {"image", "heic"},
    "image_crop": {"image", "heic"},
    "scanned_pdf_to_editable_text": {"pdf"},
    "ocr_extract": {"pdf", "image", "heic"},
}


def parse_positive_float(value: str = "", field_name: str = "value") -> float | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    try:
        parsed = float(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number.") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")
    return parsed


def parse_non_negative_int(value: str = "", field_name: str = "value", required: bool = False) -> int | None:
    normalized = (value or "").strip()
    if not normalized:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    try:
        parsed = int(float(normalized))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number.") from exc
    if parsed < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    if required and parsed == 0:
        raise ValueError(f"{field_name} must be greater than 0.")
    return parsed


def upload_size(upload_file: UploadFile) -> int:
    current_position = upload_file.file.tell()
    upload_file.file.seek(0, 2)
    size = upload_file.file.tell()
    upload_file.file.seek(current_position)
    return size


def is_valid_user(db: Session, user_id: str = "") -> bool:
    normalized_user_id = (user_id or "").strip()
    return normalized_user_id.isdigit() and db.query(User).filter(User.id == int(normalized_user_id)).first() is not None


def enforce_upload_access(db: Session, file: UploadFile, user_id: str = "", guest_id: str = "") -> bool:
    size = upload_size(file)
    if is_valid_user(db, user_id):
        if size > USER_UPLOAD_LIMIT_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "message": "The maximum upload size for logged-in users is 70 MB.",
                    "code": "upload_too_large",
                    "max_upload_mb": 70,
                },
            )
        return False

    normalized_guest_id = re.sub(r"[^A-Za-z0-9_-]+", "", (guest_id or "").strip())[:120]
    if not normalized_guest_id:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "A browser guest ID is required for guest processing. Please refresh the page or log in.",
                "code": "guest_id_required",
            },
        )

    if size > GUEST_UPLOAD_LIMIT_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "message": "Guest mode allows uploads up to 3 MB only. Log in for larger files.",
                "code": "guest_upload_limit",
                "max_upload_mb": 3,
            },
        )

    ensure_edit_allowed(db, user_id="", guest_id=normalized_guest_id)
    return True


def enforce_multiple_upload_access(db: Session, files: list[UploadFile], user_id: str = "", guest_id: str = "") -> bool:
    total_size = sum(upload_size(file) for file in files)
    if is_valid_user(db, user_id):
        if total_size > USER_UPLOAD_LIMIT_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "message": "Logged-in users can upload up to 70 MB combined.",
                    "code": "upload_too_large",
                    "max_upload_mb": 70,
                },
            )
        return False

    normalized_guest_id = re.sub(r"[^A-Za-z0-9_-]+", "", (guest_id or "").strip())[:120]
    if not normalized_guest_id:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "A browser guest ID is required for guest processing. Please refresh the page or log in.",
                "code": "guest_id_required",
            },
        )
    if total_size > GUEST_UPLOAD_LIMIT_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "message": "Guest mode allows combined image uploads up to 3 MB only. Log in for larger files.",
                "code": "guest_upload_limit",
                "max_upload_mb": 3,
            },
        )
    ensure_edit_allowed(db, user_id="", guest_id=normalized_guest_id)
    return True


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    command: str = Form(""),
    task: str = Form(""),
    target_size_mb: str = Form(""),
    crop_width: str = Form(""),
    crop_height: str = Form(""),
    crop_x: str = Form(""),
    crop_y: str = Form(""),
    user_id: str = Form(""),
    guest_id: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        is_guest = enforce_upload_access(db, file, user_id=user_id, guest_id=guest_id)
        validate_filename(file.filename or "")
        file_type = detect_file_type(file.filename or "", file.content_type)
        saved_path = save_upload(file, UPLOAD_DIR)
        detected = parse_command(command, file_type)
        explicit_task = normalize_task(task)
        if explicit_task:
            allowed_types = TASK_FILE_TYPES.get(explicit_task)
            if allowed_types and file_type not in allowed_types:
                allowed_label = ", ".join(sorted(allowed_types))
                raise ValueError(f"Upload a {allowed_label} file for {explicit_task}.")
            detected["task"] = explicit_task
        target_size = parse_positive_float(target_size_mb, "Target size MB")
        options = {
            "target_size_bytes": int(target_size * 1024 * 1024) if target_size else None,
            "crop_width": parse_non_negative_int(crop_width, "Crop width", required=detected["task"] == "image_crop"),
            "crop_height": parse_non_negative_int(crop_height, "Crop height", required=detected["task"] == "image_crop"),
            "crop_x": parse_non_negative_int(crop_x, "Crop X"),
            "crop_y": parse_non_negative_int(crop_y, "Crop Y"),
        }
        result = process_document(
            input_path=saved_path,
            output_dir=OUTPUT_DIR,
            file_type=file_type,
            task=detected["task"],
            old_text=detected.get("old_text"),
            new_text=detected.get("new_text"),
            options=options,
        )
        output_path = result["output_path"]

        history_saved = True
        try:
            document = Document(
                original_filename=file.filename or saved_path.name,
                stored_filename=saved_path.name,
                file_type=file_type,
                file_size=saved_path.stat().st_size,
                status="processed",
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            history = History(
                document_id=document.id,
                command=command or "No command provided",
                detected_task=detected["task"],
                output_filename=output_path.name,
                status="completed",
            )
            db.add(history)
            db.commit()
        except SQLAlchemyError:
            history_saved = False
            db.rollback()

        usage = register_edit_usage(db, user_id=user_id, guest_id=guest_id) if is_guest else {
            "is_guest": False,
            "guest_edit_limit": 3,
            "guest_edit_count": None,
            "guest_edit_remaining": None,
        }

        return {
            "success": True,
            "message": "Document processed successfully" if history_saved else "Document processed successfully. History could not be saved.",
            "original_filename": file.filename,
            "detected_file_type": file_type,
            "detected_task": detected["task"],
            "preview_file_url": f"/api/documents/preview/{output_path.name}",
            "output_file_url": f"/api/documents/download/{output_path.name}",
            "output_filename": output_path.name,
            "original_size": saved_path.stat().st_size,
            "output_size": result.get("output_size"),
            "warning": result.get("warning"),
            "compressed_size": result.get("compressed_size"),
            "reduction_percent": result.get("reduction_percent"),
            "target_size": result.get("target_size"),
            "target_achieved": result.get("target_achieved"),
            **usage,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc


@router.post("/upload/images-to-pdf")
def upload_images_to_pdf(
    files: list[UploadFile] = File(...),
    output_name: str = Form("images_combined.pdf"),
    user_id: str = Form(""),
    guest_id: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        if not files:
            raise ValueError("Select images.")
        is_guest = enforce_multiple_upload_access(db, files, user_id=user_id, guest_id=guest_id)
        saved_paths = []
        original_names = []
        for upload_file in files:
            validate_filename(upload_file.filename or "")
            file_type = detect_file_type(upload_file.filename or "", upload_file.content_type)
            if file_type not in {"image", "heic"}:
                raise ValueError("Upload image files only for Multiple Images to PDF.")
            original_names.append(upload_file.filename or "image")
            saved_paths.append(save_upload(upload_file, UPLOAD_DIR))

        result = process_multiple_images_to_pdf(saved_paths, OUTPUT_DIR, output_name=output_name)
        output_path = result["output_path"]

        usage = register_edit_usage(db, user_id=user_id, guest_id=guest_id) if is_guest else {
            "is_guest": False,
            "guest_edit_limit": 3,
            "guest_edit_count": None,
            "guest_edit_remaining": None,
        }

        return {
            "success": True,
            "message": "Images converted to PDF successfully",
            "original_filename": f"{len(files)} images",
            "original_filenames": original_names,
            "detected_file_type": "image",
            "detected_task": "images_to_pdf",
            "preview_file_url": f"/api/documents/preview/{output_path.name}",
            "output_file_url": f"/api/documents/download/{output_path.name}",
            "output_filename": output_path.name,
            "original_size": sum(path.stat().st_size for path in saved_paths),
            "output_size": result.get("output_size"),
            **usage,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc
