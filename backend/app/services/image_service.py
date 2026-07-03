from pathlib import Path

from PIL import Image


def _register_heif_if_needed(image_path: Path) -> None:
    if image_path.suffix.lower() not in {".heic", ".heif"}:
        return
    try:
        from pillow_heif import register_heif_opener
    except ImportError as exc:
        raise ValueError("Install pillow-heif to process HEIC images.") from exc
    register_heif_opener()


def image_to_pdf(image_path: Path, output_path: Path) -> Path:
    _register_heif_if_needed(image_path)
    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB")
        rgb_image.save(output_path, "PDF", resolution=100.0)
    return output_path


def multiple_images_to_pdf(image_paths: list[Path], output_path: Path) -> Path:
    if not image_paths:
        raise ValueError("Select at least one image to create a PDF.")

    if any(path.suffix.lower() in {".heic", ".heif"} for path in image_paths):
        try:
            from pillow_heif import register_heif_opener
        except ImportError as exc:
            raise ValueError("Install pillow-heif to convert HEIC images to PDF.") from exc
        register_heif_opener()

    pages = []
    try:
        for image_path in image_paths:
            with Image.open(image_path) as image:
                pages.append(image.convert("RGB").copy())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        first_page, rest_pages = pages[0], pages[1:]
        first_page.save(output_path, "PDF", save_all=True, append_images=rest_pages, resolution=100.0)
    finally:
        for page in pages:
            page.close()

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError("The PDF output created from images is blank.")
    return output_path


def jpg_to_png(image_path: Path, output_path: Path) -> Path:
    if image_path.suffix.lower() not in {".jpg", ".jpeg"}:
        raise ValueError("Upload a .jpg or .jpeg file for JPG to PNG.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as image:
        image.save(output_path, "PNG")
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError("JPG to PNG output is blank.")
    return output_path


def png_to_jpg(image_path: Path, output_path: Path) -> Path:
    if image_path.suffix.lower() != ".png":
        raise ValueError("Upload a .png file for PNG to JPG.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as image:
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode in {"RGBA", "LA"}:
            background.paste(image, mask=image.getchannel("A"))
        else:
            background.paste(image.convert("RGB"))
        background.save(output_path, "JPEG", quality=92, optimize=True)
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError("PNG to JPG output is blank.")
    return output_path


def image_crop(image_path: Path, output_path: Path, crop_width: int, crop_height: int, crop_x: int | None = None, crop_y: int | None = None) -> Path:
    if crop_width <= 0 or crop_height <= 0:
        raise ValueError("Crop width and height must be at least 1 pixel.")

    _register_heif_if_needed(image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as image:
        if crop_width > image.width or crop_height > image.height:
            raise ValueError(f"Crop size is larger than the original image. Image size is {image.width}x{image.height}px.")

        if crop_x is None:
            crop_x = max(0, (image.width - crop_width) // 2)
        if crop_y is None:
            crop_y = max(0, (image.height - crop_height) // 2)
        if crop_x < 0 or crop_y < 0:
            raise ValueError("Crop X/Y cannot be negative.")
        if crop_x + crop_width > image.width or crop_y + crop_height > image.height:
            raise ValueError(f"Crop area is outside the image. Image size is {image.width}x{image.height}px.")

        cropped = image.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
        suffix = output_path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            if cropped.mode in {"RGBA", "LA"}:
                background = Image.new("RGB", cropped.size, (255, 255, 255))
                background.paste(cropped, mask=cropped.getchannel("A"))
                cropped = background
            else:
                cropped = cropped.convert("RGB")
            cropped.save(output_path, "JPEG", quality=95, optimize=True)
        else:
            cropped.save(output_path, "PNG")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError("Image crop output is blank.")
    return output_path
