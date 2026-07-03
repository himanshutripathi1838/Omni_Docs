import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def save_upload(upload_file: UploadFile, upload_dir: Path) -> Path:
    suffix = Path(upload_file.filename or "uploaded.bin").suffix
    stored_name = f"{uuid4().hex}{suffix.lower()}"
    fallback_dir = upload_dir.parent.parent / "outputs" / "uploads"
    last_error = None

    for directory in (upload_dir, fallback_dir):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            destination = directory / stored_name
            upload_file.file.seek(0)
            with destination.open("wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            return destination
        except PermissionError as exc:
            last_error = exc

    raise last_error or PermissionError(f"Could not save upload: {stored_name}")
