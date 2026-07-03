import re
from pathlib import Path

from docx import Document as WordDocument
from docx.shared import Inches
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.config.settings import OUTPUT_DIR, UPLOAD_DIR
from app.database.db import get_db
from app.models.document_model import Document
from app.models.history_model import History
from app.routes.editor_routes import ensure_edit_allowed, register_edit_usage
from app.services.image_service import image_to_pdf
from app.services.ocr_service import extract_text_from_image
from app.services.storage_service import save_upload
from app.utils.file_detector import detect_file_type
from app.utils.validators import validate_filename


router = APIRouter(prefix="/ocr", tags=["ocr"])


def make_safe_output_name(filename: str | None, fallback_stem: str, extension: str) -> str:
    raw_name = (filename or "").strip()
    if not raw_name:
        raw_name = f"{fallback_stem}_edited"
    stem = re.sub(r"[^A-Za-z0-9._ -]+", "", raw_name).strip(" .")
    if not stem:
        stem = f"{fallback_stem}_edited"
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    return f"{stem[:80]}.{extension.lstrip('.')}"


def image_to_word(image_path: Path, output_path: Path, ocr_text: str) -> Path:
    document = WordDocument()
    document.add_heading("Image OCR Result", level=1)
    document.add_picture(str(image_path), width=Inches(6.2))
    if ocr_text.strip():
        document.add_heading("Extracted text", level=2)
        for paragraph in ocr_text.splitlines() or [""]:
            document.add_paragraph(paragraph)
    document.save(output_path)
    return output_path


def save_image_output(image_path: Path, output_path: Path) -> Path:
    with Image.open(image_path) as image:
        image.convert("RGB").save(output_path, "PNG")
    return output_path


@router.get("/status")
def ocr_status():
    return {
        "engine": "placeholder",
        "message": "PaddleOCR or Tesseract can be connected here for production OCR.",
    }


@router.post("/image/save")
def save_edited_image(
    file: UploadFile = File(...),
    output_format: str = Form("pdf"),
    output_name: str = Form(""),
    ocr_text: str = Form(""),
    user_id: str = Form(""),
    guest_id: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        ensure_edit_allowed(db, user_id=user_id, guest_id=guest_id)
        validate_filename(file.filename or "edited-image.png")
        file_type = detect_file_type(file.filename or "", file.content_type)
        if file_type != "image":
            raise ValueError("Upload only an image file in the Image OCR editor.")

        normalized_format = output_format.lower().strip()
        if normalized_format not in {"pdf", "docx", "image"}:
            raise ValueError("Output format must be pdf, docx, or image.")

        saved_path = save_upload(file, UPLOAD_DIR)
        fallback_stem = saved_path.stem or "edited_image"
        extracted_text = ocr_text.strip() or extract_text_from_image(saved_path)

        if normalized_format == "pdf":
            output_filename = make_safe_output_name(output_name, fallback_stem, "pdf")
            output_path = image_to_pdf(saved_path, OUTPUT_DIR / output_filename)
        elif normalized_format == "docx":
            output_filename = make_safe_output_name(output_name, fallback_stem, "docx")
            output_path = image_to_word(saved_path, OUTPUT_DIR / output_filename, extracted_text)
        else:
            output_filename = make_safe_output_name(output_name, fallback_stem, "png")
            output_path = save_image_output(saved_path, OUTPUT_DIR / output_filename)

        document = Document(
            original_filename=file.filename or saved_path.name,
            stored_filename=saved_path.name,
            file_type="image",
            file_size=saved_path.stat().st_size,
            status="processed",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        history = History(
            document_id=document.id,
            command=f"Image OCR editor export as {normalized_format}",
            detected_task="image_ocr_editor",
            output_filename=output_path.name,
            status="completed",
        )
        db.add(history)
        db.commit()
        usage = register_edit_usage(db, user_id=user_id, guest_id=guest_id)

        return {
            "success": True,
            "message": "Image edited and exported successfully",
            "original_filename": file.filename,
            "detected_file_type": "image",
            "detected_task": "image_ocr_editor",
            "preview_file_url": f"/api/documents/preview/{output_path.name}",
            "output_file_url": f"/api/documents/download/{output_path.name}",
            "output_filename": output_path.name,
            "ocr_text": extracted_text,
            **usage,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image OCR save failed: {exc}") from exc
