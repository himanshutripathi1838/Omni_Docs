from pathlib import Path

import fitz


def extract_text_from_image(image_path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image, ImageOps

        languages = set(pytesseract.get_languages(config=""))
        selected = [lang for lang in ("eng", "hin") if lang in languages]
        if not selected:
            raise ValueError("OCR language data is missing. Install English or Hindi Tesseract language data.")
        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            text = pytesseract.image_to_string(image, lang="+".join(selected), config="--psm 3").strip()
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
    selectable_text = extract_selectable_text_from_pdf(pdf_path)
    if selectable_text:
        return write_text_output(selectable_text, output_path)

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        text = (
            f"Scanned PDF detected: {pdf_path.name}\n\n"
            "No selectable text was found. Install and configure pytesseract and Pillow for OCR.\n"
            "Future upgrade: searchable PDF and editable DOCX support will be added here."
        )
        return write_text_output(text, output_path)

    output_lines = [f"Scanned PDF OCR result: {pdf_path.name}"]
    with fitz.open(pdf_path) as document:
        if document.page_count == 0:
            raise ValueError("No pages were found in the PDF.")
        for page_index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            text = pytesseract.image_to_string(image, lang="eng+hin").strip()
            output_lines.append(f"\n--- Page {page_index} ---\n{text or '[OCR text not detected on this page]'}")

    # Future upgrade: searchable PDF and editable DOCX generation can reuse these OCR page blocks.
    return write_text_output("\n".join(output_lines), output_path)


def write_text_output(text: str, output_path: Path) -> Path:
    if not text.strip():
        text = "No text was extracted. Scanned or image-only documents need OCR configuration."
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    if output_path.stat().st_size == 0:
        raise ValueError("Text output is blank.")
    return output_path
