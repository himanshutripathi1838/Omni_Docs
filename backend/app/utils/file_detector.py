import mimetypes
from pathlib import Path


EXTENSION_MAP = {
    ".pdf": "pdf",
    ".doc": "word",
    ".docx": "word",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".webp": "image",
    ".tif": "image",
    ".tiff": "image",
    ".heic": "heic",
    ".heif": "heic",
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "csv",
    ".md": "markdown",
    ".markdown": "markdown",
    ".ppt": "powerpoint",
    ".pptx": "powerpoint",
    ".txt": "text",
}


def detect_file_type(filename: str, content_type: str | None = None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in EXTENSION_MAP:
        return EXTENSION_MAP[suffix]
    guessed_type = content_type or mimetypes.guess_type(filename)[0] or ""
    if "pdf" in guessed_type:
        return "pdf"
    if "word" in guessed_type or "document" in guessed_type:
        return "word"
    if "image" in guessed_type:
        return "image"
    if "sheet" in guessed_type or "excel" in guessed_type:
        return "excel"
    if "presentation" in guessed_type or "powerpoint" in guessed_type:
        return "powerpoint"
    if "markdown" in guessed_type:
        return "markdown"
    return "unknown"
