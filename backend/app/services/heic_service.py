from pathlib import Path

from PIL import Image


def _register_heif() -> None:
    try:
        from pillow_heif import register_heif_opener
    except ImportError as exc:
        raise ValueError("Install pillow-heif for HEIC conversion.") from exc
    register_heif_opener()


def _ensure_non_empty(output_path: Path, message: str) -> Path:
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError(message)
    return output_path


def heic_to_jpg(input_path: Path, output_path: Path) -> Path:
    _register_heif()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        image.convert("RGB").save(output_path, "JPEG", quality=92, optimize=True)

    return _ensure_non_empty(output_path, "HEIC to JPG output is blank. The file may be corrupt.")


def heic_to_png(input_path: Path, output_path: Path) -> Path:
    _register_heif()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        image.save(output_path, "PNG")
    return _ensure_non_empty(output_path, "HEIC to PNG output is blank. The file may be corrupt.")


def image_to_heic(input_path: Path, output_path: Path) -> Path:
    _register_heif()
    if input_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise ValueError("Upload a JPG, JPEG, or PNG file for HEIC output.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        image.convert("RGB").save(output_path, "HEIF", quality=90)
    return _ensure_non_empty(output_path, "Image to HEIC output is blank.")
