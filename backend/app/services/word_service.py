from pathlib import Path
import shutil
import subprocess

import fitz
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


SERVICE_DIR = Path(__file__).resolve().parent


def text_to_word(title: str, text: str, output_path: Path) -> Path:
    document = Document()
    document.add_heading(title, level=1)
    for paragraph in text.splitlines() or [""]:
        document.add_paragraph(paragraph)
    document.save(output_path)
    return output_path


def extract_text_from_word(docx_path: Path) -> str:
    document = Document(docx_path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _run_to_dict(run) -> dict:
    color = run.font.color.rgb if run.font.color and run.font.color.rgb else None
    size = run.font.size.pt if run.font.size else None
    return {
        "text": run.text,
        "color": f"#{color}" if color else None,
        "bold": bool(run.bold),
        "italic": bool(run.italic),
        "underline": bool(run.underline),
        "size": size,
    }


def _paragraph_to_dict(paragraph: Paragraph, block_id: int) -> dict:
    runs = [_run_to_dict(run) for run in paragraph.runs if run.text]
    return {
        "type": "paragraph",
        "id": block_id,
        "text": paragraph.text,
        "style": paragraph.style.name if paragraph.style else "Normal",
        "runs": runs,
    }


def _cell_to_dict(cell) -> dict:
    paragraphs = [_paragraph_to_dict(paragraph, index) for index, paragraph in enumerate(cell.paragraphs)]
    return {
        "text": "\n".join(paragraph.text for paragraph in cell.paragraphs),
        "paragraphs": paragraphs,
        "runs": paragraphs[0]["runs"] if paragraphs else [],
    }


def extract_word_blocks(docx_path: Path) -> list[dict]:
    document = Document(docx_path)
    blocks = []
    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            blocks.append(_paragraph_to_dict(Paragraph(child, document), len(blocks)))
        elif tag == "tbl":
            table = Table(child, document)
            blocks.append(
                {
                    "type": "table",
                    "id": len(blocks),
                    "rows": [[_cell_to_dict(cell) for cell in row.cells] for row in table.rows],
                }
            )
    return blocks


def extract_word_paragraphs(docx_path: Path) -> list[dict]:
    document = Document(docx_path)
    paragraphs = []
    for index, paragraph in enumerate(document.paragraphs):
        paragraphs.append(
            {
                "id": index,
                "text": paragraph.text,
                "style": paragraph.style.name if paragraph.style else "Normal",
            }
        )
    return paragraphs


def _set_paragraph_text(paragraph: Paragraph, new_text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(new_text)


def _update_cell_text(cell, new_text: str) -> None:
    lines = new_text.splitlines() or [""]
    while len(cell.paragraphs) < len(lines):
        cell.add_paragraph()
    for index, line in enumerate(lines):
        _set_paragraph_text(cell.paragraphs[index], line)
    for paragraph in cell.paragraphs[len(lines):]:
        _set_paragraph_text(paragraph, "")


def save_word_blocks_preserving_format(template_path: Path, output_path: Path, blocks: list[dict]) -> Path:
    document = Document(template_path)
    block_index = 0
    for child in document.element.body.iterchildren():
        if block_index >= len(blocks):
            break

        tag = child.tag.rsplit("}", 1)[-1]
        block = blocks[block_index]
        if tag == "p" and block.get("type") == "paragraph":
            _set_paragraph_text(Paragraph(child, document), block.get("text", ""))
            block_index += 1
        elif tag == "tbl" and block.get("type") == "table":
            table = Table(child, document)
            rows = block.get("rows", [])
            for row_index, row in enumerate(table.rows):
                if row_index >= len(rows):
                    continue
                for cell_index, cell in enumerate(row.cells):
                    if cell_index >= len(rows[row_index]):
                        continue
                    _update_cell_text(cell, rows[row_index][cell_index].get("text", ""))
            block_index += 1

    document.save(output_path)
    return output_path


def save_word_paragraphs_preserving_format(template_path: Path, output_path: Path, paragraphs: list[dict]) -> Path:
    document = Document(template_path)
    for index, paragraph_data in enumerate(paragraphs):
        if index >= len(document.paragraphs):
            document.add_paragraph(paragraph_data.get("text", ""))
            continue

        paragraph = document.paragraphs[index]
        new_text = paragraph_data.get("text", "")
        _set_paragraph_text(paragraph, new_text)

    document.save(output_path)
    return output_path


def replace_text_in_word(docx_path: Path, output_path: Path, old_text: str | None, new_text: str | None) -> Path:
    document = Document(docx_path)
    if old_text and new_text:
        for paragraph in document.paragraphs:
            if old_text in paragraph.text:
                for run in paragraph.runs:
                    run.text = run.text.replace(old_text, new_text)
    else:
        document.add_paragraph("Text replacement skipped because old_text or new_text was not provided.")
    document.save(output_path)
    return output_path


def _find_office_converter() -> str | None:
    for command in ("soffice", "libreoffice"):
        found = shutil.which(command)
        if found:
            return found

    for candidate in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ):
        if Path(candidate).exists():
            return candidate
    return None


def _convert_word_to_pdf_with_office(docx_path: Path, output_path: Path) -> Path | None:
    converter = _find_office_converter()
    if not converter:
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                converter,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_path.parent),
                str(docx_path),
            ],
            check=True,
            capture_output=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    generated_path = output_path.parent / f"{docx_path.stem}.pdf"
    if generated_path.exists() and generated_path != output_path:
        generated_path.replace(output_path)
    return output_path if output_path.exists() else None


def _convert_word_to_pdf_with_ms_word(docx_path: Path, output_path: Path) -> Path | None:
    script_path = SERVICE_DIR / "word_to_pdf_com.ps1"
    if not script_path.exists():
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                "-InputPath",
                str(docx_path.resolve()),
                "-OutputPath",
                str(output_path.resolve()),
            ],
            check=True,
            capture_output=True,
            timeout=90,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    return output_path if output_path.exists() and output_path.stat().st_size > 0 else None


def _wrap_text_lines(text: str, max_width: float, font_size: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if fitz.get_text_length(candidate, fontname="helv", fontsize=font_size) <= max_width:
            line = candidate
            continue
        if line:
            lines.append(line)
        line = word

    if line:
        lines.append(line)
    return lines or [""]


def _insert_wrapped_text(page: fitz.Page, text: str, x: float, y: float, max_width: float, font_size: float, line_height: float, color=(0, 0, 0)) -> float:
    for line in _wrap_text_lines(text, max_width, font_size):
        page.insert_text((x, y), line, fontsize=font_size, fontname="helv", color=color)
        y += line_height
    return y


def _docx_rgb_to_pdf(color) -> tuple[float, float, float] | None:
    if not color:
        return None
    return color[0] / 255, color[1] / 255, color[2] / 255


def _run_color(run, default_color: tuple[float, float, float]) -> tuple[float, float, float]:
    font_color = run.font.color.rgb if run.font.color and run.font.color.rgb else None
    return _docx_rgb_to_pdf(font_color) or default_color


def _draw_rich_paragraph_runs(
    page: fitz.Page,
    paragraph: Paragraph,
    x: float,
    y: float,
    max_width: float,
    font_size: float,
    line_height: float,
    default_color: tuple[float, float, float],
    bottom_y: float | None = None,
) -> float:
    cursor_x = x
    space_width = fitz.get_text_length(" ", fontname="helv", fontsize=font_size)
    had_text = False

    runs = paragraph.runs or [paragraph.add_run(paragraph.text)]
    for run in runs:
        color = _run_color(run, default_color)
        words = run.text.split()
        for word in words:
            word_width = fitz.get_text_length(word, fontname="helv", fontsize=font_size)
            if cursor_x > x and cursor_x + word_width > x + max_width:
                cursor_x = x
                y += line_height
            if bottom_y is not None and y > bottom_y:
                return y
            page.insert_text((cursor_x, y), word, fontsize=font_size, fontname="helv", color=color)
            cursor_x += word_width + space_width
            had_text = True

    return y + line_height if had_text else y + 8


def _new_pdf_page(pdf: fitz.Document, width: float = 595, height: float = 842) -> fitz.Page:
    return pdf.new_page(width=width, height=height)


def _paragraph_style(paragraph: Paragraph) -> tuple[float, float, tuple[float, float, float], bool]:
    style_name = (paragraph.style.name if paragraph.style else "Normal").lower()
    if style_name.startswith("heading 1"):
        return 17, 22, (0.05, 0.09, 0.16), True
    if style_name.startswith("heading"):
        return 14, 19, (0.05, 0.09, 0.16), True
    return 11, 15, (0, 0, 0), False


def _draw_paragraph(page: fitz.Page, paragraph: Paragraph, x: float, y: float, max_width: float) -> float:
    text = paragraph.text.strip()
    if not text:
        return y + 8

    font_size, line_height, color, is_heading = _paragraph_style(paragraph)
    y = _draw_rich_paragraph_runs(page, paragraph, x, y, max_width, font_size, line_height, color)
    return y + (8 if is_heading else 4)


def _table_row_height(row, col_width: float, font_size: float, line_height: float, padding: float) -> float:
    max_lines = 1
    for cell in row.cells:
        text = cell.text.strip().replace("\n", " ")
        max_lines = max(max_lines, len(_wrap_text_lines(text, col_width - (padding * 2), font_size)))
    return max(26, (max_lines * line_height) + (padding * 2))


def _draw_table(page: fitz.Page, table: Table, x: float, y: float, max_width: float, bottom_y: float, pdf: fitz.Document) -> tuple[fitz.Page, float]:
    rows = list(table.rows)
    if not rows:
        return page, y

    max_cols = max(len(row.cells) for row in rows)
    if max_cols == 0:
        return page, y

    col_width = max_width / max_cols
    padding = 5
    font_size = 9.5
    line_height = 12

    for row_index, row in enumerate(rows):
        row_height = _table_row_height(row, col_width, font_size, line_height, padding)
        if y + row_height > bottom_y:
            page = _new_pdf_page(pdf)
            y = 54

        for col_index, cell in enumerate(row.cells):
            cell_x = x + (col_index * col_width)
            rect = fitz.Rect(cell_x, y, cell_x + col_width, y + row_height)
            fill = (0.94, 0.97, 1) if row_index == 0 else None
            page.draw_rect(rect, color=(0.55, 0.6, 0.68), fill=fill, width=0.7)

            text_y = y + padding + font_size
            for paragraph in cell.paragraphs:
                if text_y >= y + row_height - padding:
                    break
                text_y = _draw_rich_paragraph_runs(
                    page,
                    paragraph,
                    cell_x + padding,
                    text_y,
                    col_width - (padding * 2),
                    font_size,
                    line_height,
                    (0, 0, 0),
                    bottom_y=y + row_height - padding,
                )

        y += row_height

    return page, y + 10


def _word_to_pdf_fallback(docx_path: Path, output_path: Path) -> Path:
    document = Document(docx_path)
    pdf = fitz.open()
    margin = 54
    page_width = 595
    page_height = 842
    max_width = page_width - (margin * 2)
    bottom_y = page_height - margin
    page = _new_pdf_page(pdf, page_width, page_height)
    y = margin

    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            paragraph = Paragraph(child, document)
            font_size, line_height, _, _ = _paragraph_style(paragraph)
            estimated_height = len(_wrap_text_lines(paragraph.text.strip(), max_width, font_size)) * line_height + 10
            if y + estimated_height > bottom_y:
                page = _new_pdf_page(pdf, page_width, page_height)
                y = margin
            y = _draw_paragraph(page, paragraph, margin, y, max_width)
        elif tag == "tbl":
            table = Table(child, document)
            if y + 36 > bottom_y:
                page = _new_pdf_page(pdf, page_width, page_height)
                y = margin
            page, y = _draw_table(page, table, margin, y, max_width, bottom_y, pdf)

        if y > bottom_y:
            page = _new_pdf_page(pdf, page_width, page_height)
            y = margin

    if len(pdf) == 1 and not page.get_text("text").strip():
        page.insert_text((margin, margin), "No readable content found in this Word document.", fontsize=11, fontname="helv")

    pdf.save(output_path, garbage=4, deflate=True)
    pdf.close()
    return output_path


def word_to_pdf(docx_path: Path, output_path: Path) -> Path:
    converted = _convert_word_to_pdf_with_ms_word(docx_path, output_path)
    if converted:
        return converted

    converted = _convert_word_to_pdf_with_office(docx_path, output_path)
    if converted:
        return converted

    return _word_to_pdf_fallback(docx_path, output_path)
