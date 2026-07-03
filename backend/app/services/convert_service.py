from pathlib import Path

from app.services.compression_service import image_compress, pdf_compress
from app.services.excel_csv_service import csv_to_excel, csv_to_pdf, excel_to_csv, excel_to_pdf
from app.services.heic_service import heic_to_jpg, heic_to_png, image_to_heic
from app.services.image_service import image_crop, image_to_pdf, jpg_to_png, multiple_images_to_pdf, png_to_jpg
from app.services.markdown_service import markdown_to_html, markdown_to_pdf, markdown_to_powerpoint, markdown_to_text, markdown_to_word
from app.services.ocr_service import extract_text_from_image, scanned_pdf_to_editable_text, write_text_output
from app.services.pdf_service import pdf_to_csv, pdf_to_excel, pdf_to_word, pdf_to_zip, placeholder_pdf_tool, replace_text_in_pdf
from app.services.powerpoint_service import pdf_to_powerpoint, powerpoint_to_pdf
from app.services.word_service import replace_text_in_word, text_to_word, word_to_pdf


def _result(output_path: Path, metadata: dict | None = None) -> dict:
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError("Output file is blank. Please check the input file.")
    payload = {
        "output_path": output_path,
        "output_size": output_path.stat().st_size,
    }
    if metadata:
        payload.update(metadata)
    return payload


def process_document(
    input_path: Path,
    output_dir: Path,
    file_type: str,
    task: str,
    old_text: str | None = None,
    new_text: str | None = None,
    options: dict | None = None,
) -> dict:
    stem = input_path.stem
    options = options or {}
    target_size_bytes = options.get("target_size_bytes")

    if task == "image_to_word":
        text = extract_text_from_image(input_path)
        return _result(text_to_word("Image OCR Result", text, output_dir / f"{stem}_ocr.docx"))
    if task == "image_to_pdf":
        return _result(image_to_pdf(input_path, output_dir / f"{stem}.pdf"))
    if task == "pdf_to_word":
        return _result(pdf_to_word(input_path, output_dir / f"{stem}.docx"))
    if task == "pdf_to_csv":
        return _result(pdf_to_csv(input_path, output_dir / f"{stem}.csv"))
    if task == "pdf_to_excel":
        return _result(pdf_to_excel(input_path, output_dir / f"{stem}.xlsx"))
    if task == "pdf_to_powerpoint":
        return _result(pdf_to_powerpoint(input_path, output_dir / f"{stem}.pptx"))
    if task == "word_to_pdf":
        return _result(word_to_pdf(input_path, output_dir / f"{stem}.pdf"))
    if task == "powerpoint_to_pdf":
        return _result(powerpoint_to_pdf(input_path, output_dir / f"{stem}.pdf"))
    if task == "heic_to_jpg":
        return _result(heic_to_jpg(input_path, output_dir / f"{stem}.jpg"))
    if task == "heic_to_png":
        return _result(heic_to_png(input_path, output_dir / f"{stem}.png"))
    if task == "jpg_to_heic":
        return _result(image_to_heic(input_path, output_dir / f"{stem}.heic"))
    if task == "png_to_heic":
        return _result(image_to_heic(input_path, output_dir / f"{stem}.heic"))
    if task == "excel_to_csv":
        return _result(excel_to_csv(input_path, output_dir / f"{stem}.csv"))
    if task == "excel_to_pdf":
        return _result(excel_to_pdf(input_path, output_dir / f"{stem}.pdf"))
    if task == "csv_to_excel":
        return _result(csv_to_excel(input_path, output_dir / f"{stem}.xlsx"))
    if task == "csv_to_pdf":
        return _result(csv_to_pdf(input_path, output_dir / f"{stem}.pdf"))
    if task == "pdf_compress":
        output_path, metadata = pdf_compress(input_path, output_dir / f"{stem}_compressed.pdf", target_size_bytes=target_size_bytes)
        return _result(output_path, metadata)
    if task == "pdf_to_zip":
        return _result(pdf_to_zip(input_path, output_dir / f"{stem}.zip"))
    if task == "image_compress":
        output_suffix = ".webp" if input_path.suffix.lower() == ".webp" else ".jpg"
        output_path, metadata = image_compress(input_path, output_dir / f"{stem}_compressed{output_suffix}", target_size_bytes=target_size_bytes)
        return _result(output_path, metadata)
    if task == "scanned_pdf_to_editable_text":
        return _result(scanned_pdf_to_editable_text(input_path, output_dir / f"{stem}_editable_text.txt"))
    if task == "markdown_to_pdf":
        return _result(markdown_to_pdf(input_path, output_dir / f"{stem}.pdf"))
    if task == "markdown_to_word":
        return _result(markdown_to_word(input_path, output_dir / f"{stem}.docx"))
    if task == "markdown_to_html":
        return _result(markdown_to_html(input_path, output_dir / f"{stem}.html"))
    if task == "markdown_to_text":
        return _result(markdown_to_text(input_path, output_dir / f"{stem}.txt"))
    if task == "markdown_to_powerpoint":
        return _result(markdown_to_powerpoint(input_path, output_dir / f"{stem}.pptx"))
    if task == "jpg_to_png":
        return _result(jpg_to_png(input_path, output_dir / f"{stem}.png"))
    if task == "png_to_jpg":
        return _result(png_to_jpg(input_path, output_dir / f"{stem}.jpg"))
    if task == "image_crop":
        crop_width = int(options.get("crop_width") or 0)
        crop_height = int(options.get("crop_height") or 0)
        crop_x = options.get("crop_x")
        crop_y = options.get("crop_y")
        output_suffix = ".jpg" if input_path.suffix.lower() in {".jpg", ".jpeg"} else ".png"
        return _result(image_crop(input_path, output_dir / f"{stem}_cropped{output_suffix}", crop_width, crop_height, crop_x, crop_y))
    if task == "text_replace":
        if file_type == "word":
            return _result(replace_text_in_word(input_path, output_dir / f"{stem}_replaced.docx", old_text, new_text))
        if file_type == "pdf":
            return _result(replace_text_in_pdf(input_path, output_dir / f"{stem}_replaced.pdf", old_text, new_text))
        text = f"Text replacement placeholder for {input_path.name}: {old_text} -> {new_text}"
        return _result(write_text_output(text, output_dir / f"{stem}_replaced.txt"))
    if task == "ocr_extract":
        if file_type == "pdf":
            return _result(scanned_pdf_to_editable_text(input_path, output_dir / f"{stem}_extracted.txt"))
        text = extract_text_from_image(input_path) if file_type == "image" else f"OCR/text extraction placeholder for {input_path.name}"
        return _result(write_text_output(text, output_dir / f"{stem}_extracted.txt"))
    if task in {"pdf_merge", "pdf_split"}:
        return _result(placeholder_pdf_tool(output_dir / f"{stem}_{task}.txt", task))

    return _result(write_text_output(f"Unsupported task: {task}", output_dir / f"{stem}_unsupported.txt"))


def process_multiple_images_to_pdf(input_paths: list[Path], output_dir: Path, output_name: str = "images_combined.pdf") -> dict:
    safe_name = Path(output_name).name
    if not safe_name.lower().endswith(".pdf"):
        safe_name = f"{Path(safe_name).stem or 'images_combined'}.pdf"
    return _result(multiple_images_to_pdf(input_paths, output_dir / safe_name))
