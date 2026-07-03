from pathlib import Path

import fitz
from PIL import Image


def _compression_metadata(original_path: Path, output_path: Path) -> dict:
    original_size = original_path.stat().st_size
    output_size = output_path.stat().st_size if output_path.exists() else 0
    if output_size == 0:
        raise ValueError("Compressed output is blank.")
    reduction = ((original_size - output_size) / original_size * 100) if original_size else 0
    return {
        "original_size": original_size,
        "output_size": output_size,
        "compressed_size": output_size,
        "reduction_percent": round(reduction, 2),
    }


def _target_metadata(metadata: dict, target_size_bytes: int | None) -> dict:
    if not target_size_bytes:
        return metadata
    metadata["target_size"] = target_size_bytes
    metadata["target_achieved"] = metadata["output_size"] <= target_size_bytes
    return metadata


def _save_raster_pdf(input_path: Path, output_path: Path, quality: int, scale: float) -> None:
    compressed = fitz.open()
    try:
        with fitz.open(input_path) as source:
            for page in source:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                image_bytes = pixmap.pil_tobytes(format="JPEG", quality=quality)
                target_page = compressed.new_page(width=page.rect.width, height=page.rect.height)
                target_page.insert_image(target_page.rect, stream=image_bytes)
        compressed.save(output_path, garbage=4, deflate=True, clean=True)
    finally:
        compressed.close()


def pdf_compress(input_path: Path, output_path: Path, target_size_bytes: int | None = None) -> tuple[Path, dict]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(input_path) as document:
        if document.page_count == 0:
            raise ValueError("No pages were found in the PDF.")
        document.save(output_path, garbage=4, deflate=True, clean=True)

    if target_size_bytes and output_path.stat().st_size > target_size_bytes:
        best_path = output_path
        best_size = output_path.stat().st_size
        attempts = [(82, 1.5), (68, 1.3), (55, 1.15), (42, 1.0)]
        for index, (quality, scale) in enumerate(attempts, start=1):
            candidate = output_path.with_name(f"{output_path.stem}_target_{index}{output_path.suffix}")
            _save_raster_pdf(input_path, candidate, quality=quality, scale=scale)
            candidate_size = candidate.stat().st_size if candidate.exists() else 0
            if candidate_size and candidate_size < best_size:
                best_path = candidate
                best_size = candidate_size
            if candidate_size and candidate_size <= target_size_bytes:
                best_path = candidate
                break
        if best_path != output_path:
            output_path.unlink(missing_ok=True)
            best_path.replace(output_path)

    return output_path, _target_metadata(_compression_metadata(input_path, output_path), target_size_bytes)


def image_compress(
    input_path: Path,
    output_path: Path,
    quality: int = 72,
    max_dimension: int | None = None,
    target_size_bytes: int | None = None,
) -> tuple[Path, dict]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if input_path.suffix.lower() in {".heic", ".heif"}:
        try:
            from pillow_heif import register_heif_opener
        except ImportError as exc:
            raise ValueError("Install pillow-heif to compress HEIC images.") from exc
        register_heif_opener()

    with Image.open(input_path) as image:
        if max_dimension:
            image.thumbnail((max_dimension, max_dimension))

        suffix = output_path.suffix.lower()
        attempts = [quality]
        if target_size_bytes:
            attempts = [92, 82, 72, 62, 52, 42, 34, 28]
        for attempt_quality in attempts:
            if suffix == ".webp":
                image.save(output_path, "WEBP", quality=attempt_quality, method=6)
            else:
                image.convert("RGB").save(output_path, "JPEG", quality=attempt_quality, optimize=True)
            if not target_size_bytes or output_path.stat().st_size <= target_size_bytes:
                break

    return output_path, _target_metadata(_compression_metadata(input_path, output_path), target_size_bytes)
