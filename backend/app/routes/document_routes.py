from pathlib import Path
import csv

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config.settings import OUTPUT_DIR, UPLOAD_DIR


router = APIRouter(prefix="/documents", tags=["documents"])


def media_type_for(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return f"image/{'jpeg' if suffix in {'.jpg', '.jpeg'} else suffix.lstrip('.')}"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if suffix == ".csv":
        return "text/csv"
    if suffix == ".xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if suffix == ".pptx":
        return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if suffix == ".txt":
        return "text/plain; charset=utf-8"
    if suffix == ".html":
        return "text/html; charset=utf-8"
    if suffix == ".zip":
        return "application/zip"
    if suffix in {".heic", ".heif"}:
        return "image/heic"
    return "application/octet-stream"


def _read_csv_rows(file_path: Path) -> list[list[str]]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return [row for row in csv.reader(csv_file)]


def _read_xlsx_rows(file_path: Path) -> list[list[str]]:
    from openpyxl import load_workbook

    workbook = load_workbook(file_path, read_only=True, data_only=True)
    try:
        return [["" if value is None else str(value) for value in row] for row in workbook.worksheets[0].iter_rows(values_only=True)]
    finally:
        workbook.close()


def read_table_rows(file_path: Path) -> list[list[str]]:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return _read_csv_rows(file_path)
    if suffix == ".xlsx":
        return _read_xlsx_rows(file_path)
    raise ValueError("Table preview is only available for CSV and Excel outputs")


@router.get("/download/{filename}")
def download_document(filename: str):
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(path=file_path, filename=safe_name)


@router.get("/preview/{filename}")
def preview_document(filename: str):
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    media_type = media_type_for(file_path)
    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@router.get("/table-preview/{filename}")
def table_preview_document(filename: str):
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    try:
        rows = read_table_rows(file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read table preview: {exc}") from exc
    return {
        "filename": safe_name,
        "rows": rows[:80],
        "row_count": len(rows),
        "truncated": len(rows) > 80,
    }


@router.get("/source-preview/{filename}")
def preview_source_document(filename: str):
    safe_name = Path(filename).name
    file_path = UPLOAD_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    media_type = media_type_for(file_path)
    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )
