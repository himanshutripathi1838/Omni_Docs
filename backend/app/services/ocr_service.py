from pathlib import Path

import fitz


def extract_text_from_pil_image(image) -> str:
    try:
        import pytesseract
        languages = set(pytesseract.get_languages(config=""))
        selected = [lang for lang in ("eng", "hin") if lang in languages]
        if not selected:
            raise ValueError("OCR language data is missing. Install English or Hindi Tesseract language data.")
        return pytesseract.image_to_string(image, lang="+".join(selected), config="--psm 3").strip()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("OCR is unavailable. Check the Tesseract installation and language data.") from exc


def extract_text_from_image(image_path: Path) -> str:
    try:
        from PIL import Image, ImageOps

        if image_path.suffix.lower() in {".heic", ".heif"}:
            from pillow_heif import register_heif_opener
            register_heif_opener()

        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            text = extract_text_from_pil_image(image)
        if not text:
            raise ValueError("No readable text was found in this image. Try a clearer image.")
        return text
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Image OCR is unavailable. Check the Tesseract installation and language data.") from exc


def extract_selectable_text_from_pdf(pdf_path: Path) -> str:
    pages = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(f"--- Page {page_index} ---\n{text}")
    return "\n\n".join(pages).strip()


def scanned_pdf_to_editable_text(pdf_path: Path, output_path: Path) -> Path:
    from PIL import Image

    output_lines = []
    with fitz.open(pdf_path) as document:
        if document.page_count == 0:
            raise ValueError("No pages were found in the PDF.")
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if not text:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False, colorspace=fitz.csRGB)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                text = extract_text_from_pil_image(image)
            output_lines.append(f"--- Page {page_index} ---\n{text or '[No readable text detected on this page]'}")

    return write_text_output("\n".join(output_lines), output_path)


def write_text_output(text: str, output_path: Path) -> Path:
    if not text.strip():
        text = "No text was extracted. Scanned or image-only documents need OCR configuration."
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    if output_path.stat().st_size == 0:
        raise ValueError("Text output is blank.")
    return output_path
