import json
import re
import shutil
from difflib import SequenceMatcher
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config.settings import OUTPUT_DIR, UPLOAD_DIR
from app.database.db import get_db
from app.models.document_model import Document
from app.models.guest_usage_model import GuestUsage
from app.models.history_model import History
from app.models.user_model import User
from app.services.pdf_service import extract_text_from_pdf, replace_text_in_pdf_with_count, replace_text_pairs_in_pdf_with_count
from app.services.powerpoint_edit_service import extract_powerpoint_blocks, save_powerpoint_blocks
from app.services.storage_service import save_upload
from app.services.table_edit_service import extract_csv_blocks, extract_excel_blocks, save_csv_blocks, save_excel_blocks
from app.services.word_service import (
    extract_text_from_word,
    extract_word_blocks,
    extract_word_paragraphs,
    save_word_blocks_preserving_format,
    save_word_paragraphs_preserving_format,
    text_to_word,
)
from app.utils.file_detector import detect_file_type
from app.utils.validators import validate_filename


router = APIRouter(prefix="/editor", tags=["editor"])
GUEST_EDIT_LIMIT = 3


def guest_limit_error(guest_usage: GuestUsage | None = None) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "message": "Guest limit reached. Login is required after 3 free edits.",
            "code": "guest_edit_limit_reached",
            "guest_edit_limit": GUEST_EDIT_LIMIT,
            "guest_edit_count": guest_usage.edit_count if guest_usage else GUEST_EDIT_LIMIT,
            "guest_edit_remaining": 0,
        },
    )


def register_edit_usage(db: Session, user_id: str = "", guest_id: str = "") -> dict:
    normalized_user_id = (user_id or "").strip()
    if normalized_user_id.isdigit():
        user = db.query(User).filter(User.id == int(normalized_user_id)).first()
        if user:
            return {"is_guest": False, "guest_edit_limit": GUEST_EDIT_LIMIT, "guest_edit_count": None, "guest_edit_remaining": None}

    normalized_guest_id = re.sub(r"[^A-Za-z0-9_-]+", "", (guest_id or "").strip())[:120]
    if not normalized_guest_id:
        raise guest_limit_error()

    guest_usage = db.query(GuestUsage).filter(GuestUsage.guest_id == normalized_guest_id).first()
    if not guest_usage:
        guest_usage = GuestUsage(guest_id=normalized_guest_id, edit_count=0)
        db.add(guest_usage)
        db.flush()

    if guest_usage.edit_count >= GUEST_EDIT_LIMIT:
        raise guest_limit_error(guest_usage)

    guest_usage.edit_count += 1
    db.commit()
    db.refresh(guest_usage)
    return {
        "is_guest": True,
        "guest_edit_limit": GUEST_EDIT_LIMIT,
        "guest_edit_count": guest_usage.edit_count,
        "guest_edit_remaining": max(0, GUEST_EDIT_LIMIT - guest_usage.edit_count),
    }


def ensure_edit_allowed(db: Session, user_id: str = "", guest_id: str = "") -> None:
    normalized_user_id = (user_id or "").strip()
    if normalized_user_id.isdigit() and db.query(User).filter(User.id == int(normalized_user_id)).first():
        return

    normalized_guest_id = re.sub(r"[^A-Za-z0-9_-]+", "", (guest_id or "").strip())[:120]
    if not normalized_guest_id:
        raise guest_limit_error()
    guest_usage = db.query(GuestUsage).filter(GuestUsage.guest_id == normalized_guest_id).first()
    if guest_usage and guest_usage.edit_count >= GUEST_EDIT_LIMIT:
        raise guest_limit_error(guest_usage)


def flatten_word_blocks(blocks: list[dict]) -> str:
    lines = []
    for block in blocks:
        if block.get("type") == "paragraph":
            lines.append(block.get("text", ""))
        elif block.get("type") == "table":
            for row in block.get("rows", []):
                lines.append("\t".join(cell.get("text", "") for cell in row))
    return "\n".join(lines)


def build_pdf_replacements(original_text: str, edited_text: str) -> list[tuple[str, str]]:
    original_lines = original_text.splitlines()
    edited_lines = edited_text.splitlines()
    matcher = SequenceMatcher(None, original_lines, edited_lines)
    replacements = []
    for tag, original_start, original_end, edited_start, edited_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_lines = [line.strip() for line in original_lines[original_start:original_end] if line.strip()]
        new_lines = [line.strip() for line in edited_lines[edited_start:edited_end] if line.strip()]
        if tag == "replace" and len(old_lines) == len(new_lines):
            replacements.extend((old_line, new_line) for old_line, new_line in zip(old_lines, new_lines) if old_line != new_line)
        elif tag == "delete":
            replacements.extend((old_line, "") for old_line in old_lines)
        elif tag == "replace" and old_lines:
            replacements.append(("\n".join(old_lines), "\n".join(new_lines)))
    return replacements


def make_safe_pdf_name(filename: str | None, fallback_stem: str) -> str:
    raw_name = (filename or "").strip()
    if not raw_name:
        raw_name = f"{fallback_stem}_manual_edit"
    stem = re.sub(r"[^A-Za-z0-9._ -]+", "", raw_name).strip(" .")
    if not stem:
        stem = f"{fallback_stem}_manual_edit"
    if stem.lower().endswith(".pdf"):
        stem = stem[:-4]
    return f"{stem[:80]}.pdf"


def make_safe_document_name(filename: str | None, fallback_stem: str, extension: str) -> str:
    raw_name = (filename or "").strip()
    if not raw_name:
        raw_name = f"{fallback_stem}_manual_edit"
    stem = re.sub(r"[^A-Za-z0-9._ -]+", "", raw_name).strip(" .")
    if not stem:
        stem = f"{fallback_stem}_manual_edit"
    if stem.lower().endswith((".pdf", ".docx", ".csv", ".xlsx", ".pptx")):
        stem = stem.rsplit(".", 1)[0]
    return f"{stem[:80]}.{extension.lstrip('.')}"


def resolve_uploaded_file(stored_filename: str) -> Path | None:
    safe_name = Path(stored_filename).name
    if not safe_name:
        return None
    for candidate in (UPLOAD_DIR / safe_name, OUTPUT_DIR / "uploads" / safe_name):
        if candidate.exists():
            return candidate
    return None


@router.get("/tools")
def editor_tools():
    return {
        "tools": [
            "text_replace",
            "image_replace_placeholder",
            "manual_editor_placeholder",
        ]
    }


@router.post("/open")
def open_document_for_edit(file: UploadFile = File(...), expected_file_type: str = Form("")):
    try:
        validate_filename(file.filename or "")
        file_type = detect_file_type(file.filename or "", file.content_type)
        if file_type not in {"pdf", "word", "csv", "excel", "powerpoint"}:
            raise ValueError("Manual open editor supports PDF, Word, CSV, Excel, and PowerPoint files")
        expected = expected_file_type.lower().strip()
        if expected and expected not in {"pdf", "word", "csv", "excel", "powerpoint"}:
            raise ValueError("Expected file type must be pdf, word, csv, excel, or powerpoint")
        if expected and file_type != expected:
            raise ValueError(f"Upload only a {expected.upper()} file for the {expected.upper()} editor.")
        if file_type == "word" and not (file.filename or "").lower().endswith(".docx"):
            raise ValueError("Word editor currently supports .docx files only")
        if file_type == "powerpoint" and not (file.filename or "").lower().endswith(".pptx"):
            raise ValueError("PowerPoint editor currently supports .pptx files only")

        saved_path = save_upload(file, UPLOAD_DIR)
        word_blocks = []
        if file_type == "word":
            word_blocks = extract_word_blocks(saved_path)
            extracted_text = flatten_word_blocks(word_blocks)
        elif file_type == "csv":
            extracted_text, word_blocks = extract_csv_blocks(saved_path)
        elif file_type == "excel":
            extracted_text, word_blocks = extract_excel_blocks(saved_path)
        elif file_type == "powerpoint":
            extracted_text, word_blocks = extract_powerpoint_blocks(saved_path)
        else:
            extracted_text = extract_text_from_pdf(saved_path)
        word_paragraphs = [block for block in word_blocks if block.get("type") == "paragraph"]
        if not extracted_text.strip():
            raise ValueError("No editable text found. Scanned PDFs need OCR first.")

        return {
            "success": True,
            "message": "Document opened for manual editing",
            "original_filename": file.filename,
            "stored_filename": saved_path.name,
            "detected_file_type": file_type,
            "text": extracted_text,
            "blocks": word_blocks,
            "paragraphs": word_paragraphs,
            "source_preview_file_url": f"/api/documents/source-preview/{saved_path.name}" if file_type == "pdf" else "",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document open failed: {exc}") from exc


@router.post("/save")
def save_open_document_edit(
    original_filename: str = Form(...),
    stored_filename: str = Form(""),
    detected_file_type: str = Form(...),
    edited_text: str = Form(...),
    edited_blocks: str = Form(""),
    edited_paragraphs: str = Form(""),
    output_name: str = Form(""),
    output_format: str = Form("pdf"),
    user_id: str = Form(""),
    guest_id: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        ensure_edit_allowed(db, user_id=user_id, guest_id=guest_id)
        normalized_format = output_format.lower().strip()
        if normalized_format not in {"pdf", "docx", "csv", "xlsx", "pptx"}:
            raise ValueError("Output format must be pdf, docx, csv, xlsx, or pptx")
        if detected_file_type not in {"pdf", "word", "csv", "excel", "powerpoint"}:
            raise ValueError("Only PDF, Word, CSV, Excel, and PowerPoint documents can be saved from manual editor")
        if detected_file_type == "pdf" and normalized_format != "pdf":
            raise ValueError("A PDF upload can only be saved as PDF.")
        if detected_file_type == "word" and normalized_format != "docx":
            raise ValueError("A Word upload can only be saved as Word (.docx).")
        if detected_file_type == "csv" and normalized_format != "csv":
            raise ValueError("A CSV upload can only be saved as CSV.")
        if detected_file_type == "excel" and normalized_format != "xlsx":
            raise ValueError("An Excel upload can only be saved as Excel (.xlsx).")
        if detected_file_type == "powerpoint" and normalized_format != "pptx":
            raise ValueError("A PowerPoint upload can only be saved as PowerPoint (.pptx).")
        if not edited_text.strip() and not edited_blocks.strip() and not edited_paragraphs.strip():
            raise ValueError("Edited text cannot be empty")

        fallback_stem = Path(original_filename).stem or "edited_document"
        output_filename = make_safe_document_name(output_name, fallback_stem, normalized_format)
        output_path = OUTPUT_DIR / output_filename
        if detected_file_type == "word":
            template_name = Path(stored_filename).name
            template_path = resolve_uploaded_file(template_name)
            if not template_path:
                raise ValueError("Original Word file not found. Please upload the Word file again.")
            try:
                blocks = json.loads(edited_blocks) if edited_blocks.strip() else []
                paragraphs = json.loads(edited_paragraphs) if edited_paragraphs.strip() else []
            except json.JSONDecodeError as exc:
                raise ValueError("Edited Word content is invalid") from exc
            if blocks:
                save_word_blocks_preserving_format(template_path, output_path, blocks)
            else:
                save_word_paragraphs_preserving_format(template_path, output_path, paragraphs)
        elif detected_file_type in {"csv", "excel", "powerpoint"}:
            template_name = Path(stored_filename).name
            template_path = resolve_uploaded_file(template_name)
            if not template_path:
                raise ValueError("Original file not found. Please upload the file again.")
            try:
                blocks = json.loads(edited_blocks) if edited_blocks.strip() else []
            except json.JSONDecodeError as exc:
                raise ValueError("Edited content is invalid") from exc
            if detected_file_type == "csv":
                save_csv_blocks(output_path, blocks)
            elif detected_file_type == "excel":
                save_excel_blocks(output_path, blocks, template_path)
            else:
                save_powerpoint_blocks(template_path, output_path, blocks)
        elif normalized_format == "pdf":
            template_name = Path(stored_filename).name
            template_path = resolve_uploaded_file(template_name)
            if not template_path:
                raise ValueError("Original PDF file not found. Please upload the PDF file again.")
            original_text = extract_text_from_pdf(template_path)
            if edited_text == original_text:
                shutil.copyfile(template_path, output_path)
            else:
                replacements = build_pdf_replacements(original_text, edited_text)
                if not replacements:
                    raise ValueError("No changed text was detected in the PDF. Please edit the text before saving.")
                replace_text_pairs_in_pdf_with_count(template_path, output_path, replacements)
        else:
            text_to_word(f"Edited from {original_filename}", edited_text, output_path)

        document = Document(
            original_filename=original_filename,
            stored_filename=original_filename,
            file_type=detected_file_type,
            file_size=0,
            status="processed",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        history = History(
            document_id=document.id,
            command="Manual open document edit",
            detected_task="manual_open_editor",
            output_filename=output_path.name,
            status="completed",
        )
        db.add(history)
        db.commit()
        usage = register_edit_usage(db, user_id=user_id, guest_id=guest_id)

        return {
            "success": True,
            "message": "Document saved successfully",
            "original_filename": original_filename,
            "detected_file_type": detected_file_type,
            "detected_task": "manual_open_editor",
            "preview_file_url": f"/api/documents/preview/{output_path.name}",
            "output_file_url": f"/api/documents/download/{output_path.name}",
            "output_filename": output_path.name,
            **usage,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document save failed: {exc}") from exc


@router.post("/pdf/replace")
def replace_pdf_text(
    file: UploadFile = File(...),
    old_text: str = Form(...),
    new_text: str = Form(...),
    output_name: str = Form(""),
    user_id: str = Form(""),
    guest_id: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        ensure_edit_allowed(db, user_id=user_id, guest_id=guest_id)
        validate_filename(file.filename or "")
        file_type = detect_file_type(file.filename or "", file.content_type)
        if file_type != "pdf":
            raise ValueError("Manual PDF editor only accepts PDF files")

        saved_path = save_upload(file, UPLOAD_DIR)
        output_filename = make_safe_pdf_name(output_name, saved_path.stem)
        output_path, replaced = replace_text_in_pdf_with_count(
            saved_path,
            OUTPUT_DIR / output_filename,
            old_text.strip(),
            new_text.strip(),
        )

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
            command=f"Manual PDF replace: {old_text} -> {new_text}",
            detected_task="manual_pdf_text_replace",
            output_filename=output_path.name,
            status="completed",
        )
        db.add(history)
        db.commit()
        usage = register_edit_usage(db, user_id=user_id, guest_id=guest_id)

        return {
            "success": True,
            "message": f"PDF edited successfully. Replaced {replaced} match(es).",
            "original_filename": file.filename,
            "detected_file_type": file_type,
            "detected_task": "manual_pdf_text_replace",
            "matches_replaced": replaced,
            "preview_file_url": f"/api/documents/preview/{output_path.name}",
            "output_file_url": f"/api/documents/download/{output_path.name}",
            "output_filename": output_path.name,
            **usage,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF edit failed: {exc}") from exc
