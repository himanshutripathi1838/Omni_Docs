import re


def normalize_task(task: str | None) -> str | None:
    if not task:
        return None
    normalized = task.lower().strip().replace("-", "_")
    aliases = {
        "pdf_to_doc": "pdf_to_word",
        "pdf_to_docx": "pdf_to_word",
        "pdf_to_xls": "pdf_to_excel",
        "pdf_to_xlsx": "pdf_to_excel",
        "pdf_to_ppt": "pdf_to_powerpoint",
        "pdf_to_pptx": "pdf_to_powerpoint",
        "ppt_to_pdf": "powerpoint_to_pdf",
        "pptx_to_pdf": "powerpoint_to_pdf",
        "word_to_pdf": "word_to_pdf",
        "doc_to_pdf": "word_to_pdf",
        "docx_to_pdf": "word_to_pdf",
        "compress_pdf": "pdf_compress",
        "pdf_compression": "pdf_compress",
        "compress_image": "image_compress",
        "image_compression": "image_compress",
        "crop_image": "image_crop",
        "image_cropping": "image_crop",
        "image_croping": "image_crop",
        "image_crop": "image_crop",
        "scanned_pdf_ocr": "scanned_pdf_to_editable_text",
        "md_to_pdf": "markdown_to_pdf",
        "md_to_word": "markdown_to_word",
        "md_to_docx": "markdown_to_word",
        "md_to_html": "markdown_to_html",
        "md_to_txt": "markdown_to_text",
        "md_to_text": "markdown_to_text",
        "md_to_ppt": "markdown_to_powerpoint",
        "md_to_pptx": "markdown_to_powerpoint",
        "markdown_to_docx": "markdown_to_word",
        "markdown_to_txt": "markdown_to_text",
        "markdown_to_ppt": "markdown_to_powerpoint",
        "markdown_to_pptx": "markdown_to_powerpoint",
        "heic_to_jpeg": "heic_to_jpg",
        "jpeg_to_heic": "jpg_to_heic",
        "jpg_to_heif": "jpg_to_heic",
        "jpeg_to_heif": "jpg_to_heic",
        "png_to_heif": "png_to_heic",
        "heif_to_jpg": "heic_to_jpg",
        "heif_to_png": "heic_to_png",
        "multiple_images_to_pdf": "images_to_pdf",
        "images_to_pdf": "images_to_pdf",
        "pdf_zip": "pdf_to_zip",
    }
    return aliases.get(normalized, normalized)


def parse_command(command: str, file_type: str) -> dict:
    normalized = command.lower().strip()

    wants_pdf = "pdf" in normalized
    wants_csv = "csv" in normalized
    wants_excel = "excel" in normalized or "excl" in normalized or "xlsx" in normalized or "xls" in normalized
    wants_ppt = "ppt" in normalized or "pptx" in normalized or "powerpoint" in normalized or "presentation" in normalized
    wants_jpg = "jpg" in normalized or "jpeg" in normalized
    wants_png = "png" in normalized
    wants_word = "word" in normalized or "doc" in normalized or "docx" in normalized
    wants_html = "html" in normalized
    wants_text = "txt" in normalized or "text" in normalized
    wants_heic = "heic" in normalized or "heif" in normalized
    wants_zip = "zip" in normalized
    wants_compress = "compress" in normalized or "reduce size" in normalized or "smaller size" in normalized
    wants_crop = "crop" in normalized or "cropping" in normalized or "croping" in normalized

    if file_type == "image" and wants_word:
        return {"task": "image_to_word", "old_text": None, "new_text": None}
    if file_type in {"image", "heic"} and wants_crop:
        return {"task": "image_crop", "old_text": None, "new_text": None}
    if file_type == "pdf" and wants_zip:
        return {"task": "pdf_to_zip", "old_text": None, "new_text": None}
    if file_type == "heic" and wants_png:
        return {"task": "heic_to_png", "old_text": None, "new_text": None}
    if file_type == "markdown" and wants_pdf:
        return {"task": "markdown_to_pdf", "old_text": None, "new_text": None}
    if file_type == "markdown" and wants_word:
        return {"task": "markdown_to_word", "old_text": None, "new_text": None}
    if file_type == "markdown" and wants_html:
        return {"task": "markdown_to_html", "old_text": None, "new_text": None}
    if file_type == "markdown" and wants_ppt:
        return {"task": "markdown_to_powerpoint", "old_text": None, "new_text": None}
    if file_type == "markdown" and wants_text:
        return {"task": "markdown_to_text", "old_text": None, "new_text": None}
    if file_type == "image" and wants_heic and ("png" in normalized):
        return {"task": "png_to_heic", "old_text": None, "new_text": None}
    if file_type == "image" and wants_heic:
        return {"task": "jpg_to_heic", "old_text": None, "new_text": None}
    is_jpg_source = "jpg to png" in normalized or "jpeg to png" in normalized
    is_png_source = "png to jpg" in normalized or "png to jpeg" in normalized
    if file_type == "image" and (is_jpg_source or (wants_png and not is_png_source)):
        return {"task": "jpg_to_png", "old_text": None, "new_text": None}
    if file_type == "image" and (is_png_source or (wants_jpg and not is_jpg_source)):
        return {"task": "png_to_jpg", "old_text": None, "new_text": None}
    if file_type == "excel" and wants_pdf:
        return {"task": "excel_to_pdf", "old_text": None, "new_text": None}
    if file_type == "pdf" and wants_ppt:
        return {"task": "pdf_to_powerpoint", "old_text": None, "new_text": None}
    if file_type == "powerpoint" and wants_pdf:
        return {"task": "powerpoint_to_pdf", "old_text": None, "new_text": None}
    if file_type == "heic" and wants_jpg:
        return {"task": "heic_to_jpg", "old_text": None, "new_text": None}
    if file_type == "excel" and wants_csv:
        return {"task": "excel_to_csv", "old_text": None, "new_text": None}
    if file_type == "csv" and wants_excel:
        return {"task": "csv_to_excel", "old_text": None, "new_text": None}
    if file_type == "csv" and wants_pdf:
        return {"task": "csv_to_pdf", "old_text": None, "new_text": None}
    if file_type == "pdf" and wants_compress:
        return {"task": "pdf_compress", "old_text": None, "new_text": None}
    if file_type == "image" and wants_compress:
        return {"task": "image_compress", "old_text": None, "new_text": None}
    if file_type == "pdf" and ("scanned" in normalized or "editable text" in normalized or "editable" in normalized):
        return {"task": "scanned_pdf_to_editable_text", "old_text": None, "new_text": None}
    if "ocr" in normalized or "extract text" in normalized:
        return {"task": "ocr_extract", "old_text": None, "new_text": None}

    if file_type == "pdf" and ("csv" in normalized or "comma" in normalized):
        return {"task": "pdf_to_csv", "old_text": None, "new_text": None}
    if file_type == "pdf" and wants_excel:
        return {"task": "pdf_to_excel", "old_text": None, "new_text": None}
    if file_type == "pdf" and ("word" in normalized or "doc" in normalized):
        return {"task": "pdf_to_word", "old_text": None, "new_text": None}
    if file_type == "word" and "pdf" in normalized:
        return {"task": "word_to_pdf", "old_text": None, "new_text": None}

    old_text = None
    new_text = None
    replacement_match = re.search(r"replace\s+(.+?)\s+with\s+(.+)", command, flags=re.IGNORECASE)
    change_match = re.search(r"(.+?)\s+(?:change|replace)\s+(.+)", normalized)
    if replacement_match:
        old_text = replacement_match.group(1).strip()
        new_text = replacement_match.group(2).strip()
    elif "mobile" in normalized and "change" in normalized:
        old_text = "mobile number"
        new_text = "new mobile number"
    elif change_match and "convert" not in normalized:
        old_text = change_match.group(1).strip()
        new_text = change_match.group(2).strip()

    if "merge" in normalized:
        return {"task": "pdf_merge", "old_text": old_text, "new_text": new_text}
    if "split" in normalized:
        return {"task": "pdf_split", "old_text": old_text, "new_text": new_text}
    if wants_compress and file_type in {"pdf", "image", "heic"}:
        return {"task": "pdf_compress" if file_type == "pdf" else "image_compress", "old_text": old_text, "new_text": new_text}
    if old_text or "change" in normalized or "replace" in normalized:
        return {"task": "text_replace", "old_text": old_text, "new_text": new_text}
    if file_type == "image" and ("word" in normalized or "doc" in normalized):
        return {"task": "image_to_word", "old_text": old_text, "new_text": new_text}
    if file_type == "image" and "pdf" in normalized:
        return {"task": "image_to_pdf", "old_text": old_text, "new_text": new_text}
    if file_type == "image":
        return {"task": "ocr_extract", "old_text": old_text, "new_text": new_text}
    return {"task": "ocr_extract", "old_text": old_text, "new_text": new_text}
