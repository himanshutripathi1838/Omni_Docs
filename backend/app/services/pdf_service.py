from pathlib import Path
import csv
import re
from xml.sax.saxutils import escape
import zipfile

import fitz


def int_to_rgb(color_value: int) -> tuple[float, float, float]:
    red = (color_value >> 16) & 255
    green = (color_value >> 8) & 255
    blue = color_value & 255
    return red / 255, green / 255, blue / 255


def find_text_style(page: fitz.Page, rect: fitz.Rect) -> dict:
    default_style = {
        "font_size": max(7, rect.height * 0.72),
        "font_name": "helv",
        "color": (0, 0, 0),
        "origin": fitz.Point(rect.x0, rect.y1 - 2),
    }

    text_dict = page.get_text("dict")
    best_span = None
    best_overlap = 0
    for block in text_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span_rect = fitz.Rect(span["bbox"])
                overlap = span_rect & rect
                if overlap.is_empty:
                    continue
                overlap_area = overlap.get_area()
                if overlap_area > best_overlap:
                    best_overlap = overlap_area
                    best_span = span

    if not best_span:
        return default_style

    span_rect = fitz.Rect(best_span["bbox"])
    baseline_y = best_span.get("origin", (rect.x0, rect.y1 - 2))[1]
    if baseline_y < rect.y0 or baseline_y > rect.y1 + rect.height:
        baseline_y = rect.y0 + (baseline_y - span_rect.y0)

    return {
        "font_size": best_span.get("size", default_style["font_size"]),
        "font_name": "helv",
        "color": int_to_rgb(best_span.get("color", 0)),
        "origin": fitz.Point(rect.x0, baseline_y),
    }


def fit_font_size(text: str, max_width: float, font_size: float) -> float:
    fitted_size = font_size
    while fitted_size > 5:
        if fitz.get_text_length(text, fontname="helv", fontsize=fitted_size) <= max_width:
            return fitted_size
        fitted_size -= 0.5
    return fitted_size


def pdf_to_word(pdf_path: Path, output_path: Path) -> Path:
    from pdf2docx import Converter

    with fitz.open(pdf_path) as pdf:
        if not pdf.page_count:
            raise ValueError("No pages found in this PDF.")
        if not any(page.get_text("text").strip() for page in pdf):
            raise ValueError("This PDF has no selectable text. Scanned PDFs need OCR before editable Word conversion.")

    converter = Converter(str(pdf_path))
    try:
        converter.convert(str(output_path))
    finally:
        converter.close()
    return output_path


def _split_pdf_line(line: str) -> list[str]:
    clean_line = line.strip()
    if not clean_line:
        return []
    if "\t" in clean_line:
        return [part.strip() for part in clean_line.split("\t")]
    spaced_parts = [part.strip() for part in re.split(r"\s{2,}", clean_line) if part.strip()]
    if len(spaced_parts) > 1:
        return spaced_parts
    comma_parts = [part.strip() for part in clean_line.split(",") if part.strip()]
    if len(comma_parts) > 1:
        return comma_parts
    return [clean_line]


def extract_rows_from_pdf(pdf_path: Path) -> list[list[str]]:
    rows = []
    with fitz.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            page_rows = []
            find_tables = getattr(page, "find_tables", None)
            if callable(find_tables):
                try:
                    tables = find_tables()
                    for table in tables.tables:
                        for row in table.extract():
                            clean_row = [(cell or "").strip() for cell in row]
                            if any(clean_row):
                                page_rows.append(clean_row)
                except Exception:
                    page_rows = []

            if not page_rows:
                for line in page.get_text("text").splitlines():
                    row = _split_pdf_line(line)
                    if row:
                        page_rows.append(row)

            if page_rows and page_index > 1:
                rows.append([])
            rows.extend(page_rows)

    return rows or [["No selectable text found in this PDF. Scanned PDFs need OCR first."]]


def pdf_to_csv(pdf_path: Path, output_path: Path) -> Path:
    rows = extract_rows_from_pdf(pdf_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(rows)
    return output_path


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _xlsx_sheet_xml(rows: list[list[str]]) -> str:
    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            cell_ref = f"{_column_name(column_index)}{row_index}"
            safe_value = escape(str(value))
            cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{safe_value}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>'
        f'{"".join(sheet_rows)}'
        '</sheetData>'
        '</worksheet>'
    )


def write_rows_to_xlsx(rows: list[list[str]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>",
        )
        workbook.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        workbook.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="PDF Export" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>",
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        )
        workbook.writestr(
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            "</styleSheet>",
        )
        workbook.writestr("xl/worksheets/sheet1.xml", _xlsx_sheet_xml(rows))
    return output_path


def pdf_to_excel(pdf_path: Path, output_path: Path) -> Path:
    return write_rows_to_xlsx(extract_rows_from_pdf(pdf_path), output_path)


def extract_text_from_pdf(pdf_path: Path) -> str:
    pages = []
    with fitz.open(pdf_path) as pdf:
        for index, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            pages.append(text or f"[Page {index}: no selectable text found]")
    return "\n\n".join(pages)


def text_to_pdf(title: str, text: str, output_path: Path) -> Path:
    pdf = fitz.open()
    margin = 54
    page_width = 595
    page_height = 842
    line_height = 15
    font_size = 11
    max_width = page_width - (margin * 2)

    page = pdf.new_page(width=page_width, height=page_height)
    y = margin
    page.insert_text((margin, y), title, fontsize=15, fontname="helv", color=(0.05, 0.09, 0.16))
    y += 28

    for paragraph in text.splitlines() or [""]:
        words = paragraph.split(" ")
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if fitz.get_text_length(candidate, fontname="helv", fontsize=font_size) <= max_width:
                line = candidate
                continue
            if y > page_height - margin:
                page = pdf.new_page(width=page_width, height=page_height)
                y = margin
            page.insert_text((margin, y), line, fontsize=font_size, fontname="helv", color=(0, 0, 0))
            y += line_height
            line = word
        if line:
            if y > page_height - margin:
                page = pdf.new_page(width=page_width, height=page_height)
                y = margin
            page.insert_text((margin, y), line, fontsize=font_size, fontname="helv", color=(0, 0, 0))
            y += line_height
        y += 6

    pdf.save(output_path, garbage=4, deflate=True)
    pdf.close()
    return output_path


def replace_text_pairs_in_pdf_with_count(pdf_path: Path, output_path: Path, replacements: list[tuple[str, str]]) -> tuple[Path, int]:
    clean_replacements = [(old_text, new_text) for old_text, new_text in replacements if old_text]
    if not clean_replacements:
        raise ValueError("At least one text replacement is required for PDF editing")

    replacement_count = 0
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            for old_text, new_text in clean_replacements:
                rects = page.search_for(old_text)
                if not rects:
                    continue

                styled_rects = [(rect, find_text_style(page, rect)) for rect in rects]
                for rect in rects:
                    page.add_redact_annot(rect, fill=None, cross_out=False)
                page.apply_redactions(
                    images=fitz.PDF_REDACT_IMAGE_NONE,
                    graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                    text=fitz.PDF_REDACT_TEXT_REMOVE,
                )

                for rect, style in styled_rects:
                    if new_text:
                        font_size = fit_font_size(new_text, rect.width, style["font_size"])
                        y_offset = style["font_size"] - font_size
                        page.insert_text(
                            fitz.Point(rect.x0, style["origin"].y - y_offset),
                            new_text,
                            fontsize=font_size,
                            fontname=style["font_name"],
                            color=style["color"],
                            overlay=True,
                        )
                    replacement_count += 1

        if replacement_count == 0:
            raise ValueError("Edited text was not found in this PDF. Scanned PDFs need OCR first.")
        pdf.save(output_path, garbage=4, deflate=True)

    return output_path, replacement_count


def replace_text_in_pdf_with_count(pdf_path: Path, output_path: Path, old_text: str | None, new_text: str | None) -> tuple[Path, int]:
    if not old_text or new_text is None:
        raise ValueError("old_text and new_text are required for PDF text replacement")
    try:
        return replace_text_pairs_in_pdf_with_count(pdf_path, output_path, [(old_text, new_text)])
    except ValueError as exc:
        if "Edited text was not found" in str(exc):
            raise ValueError(f"'{old_text}' was not found in this PDF. Scanned PDFs need OCR first.") from exc
        raise


def replace_text_in_pdf(pdf_path: Path, output_path: Path, old_text: str | None, new_text: str | None) -> Path:
    output, _ = replace_text_in_pdf_with_count(pdf_path, output_path, old_text, new_text)
    return output


def placeholder_pdf_tool(output_path: Path, tool_name: str) -> Path:
    output_path.write_text(f"{tool_name} is queued as a placeholder MVP operation.", encoding="utf-8")
    return output_path


def pdf_to_zip(pdf_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf_path) as pdf:
        if pdf.page_count == 0:
            raise ValueError("No pages were found in the PDF.")
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for page_index, page in enumerate(pdf, start=1):
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                archive.writestr(f"page_{page_index}.png", pixmap.tobytes("png"))

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError("PDF to ZIP output is blank.")
    return output_path
