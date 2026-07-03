from pathlib import Path
import csv
import shutil


def table_blocks_to_text(rows: list[list[str]]) -> str:
    return "\n".join("\t".join(str(cell) for cell in row) for row in rows)


def rows_to_table_block(rows: list[list[str]], styles: list[list[dict]] | None = None) -> list[dict]:
    return [
        {
            "type": "table",
            "id": 0,
            "rows": [
                [
                    {"text": str(cell), "runs": [], "style": (styles or [])[row_index][cell_index] if styles and row_index < len(styles) and cell_index < len(styles[row_index]) else {}}
                    for cell_index, cell in enumerate(row)
                ]
                for row_index, row in enumerate(rows)
            ],
        }
    ]


def extract_csv_blocks(csv_path: Path) -> tuple[str, list[dict]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = [row for row in csv.reader(csv_file)]
    if not rows:
        rows = [[""]]
    return table_blocks_to_text(rows), rows_to_table_block(rows)


def extract_excel_blocks(excel_path: Path) -> tuple[str, list[dict]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError("Install openpyxl for the Excel editor.") from exc

    workbook = load_workbook(excel_path)
    sheet = workbook.active
    rows = []
    styles = []
    for row in sheet.iter_rows():
        rows.append(["" if cell.value is None else str(cell.value) for cell in row])
        styles.append([cell_style(cell) for cell in row])
    if not rows:
        rows = [[""]]
        styles = [[{}]]
    return table_blocks_to_text(rows), rows_to_table_block(rows, styles)


def cell_style(cell) -> dict:
    font_color = color_to_css(cell.font.color)
    fill_color = color_to_css(cell.fill.fgColor)
    return {
        "fontColor": font_color,
        "backgroundColor": fill_color if fill_color and fill_color.upper() not in {"#000000", "#FFFFFF"} else None,
        "bold": bool(cell.font.bold),
        "italic": bool(cell.font.italic),
        "horizontal": cell.alignment.horizontal,
    }


def color_to_css(color) -> str | None:
    if not color:
        return None
    if color.type == "rgb" and color.rgb:
        value = str(color.rgb)
        if len(value) == 8:
            value = value[2:]
        return f"#{value}"
    return None


def table_rows_from_blocks(blocks: list[dict]) -> list[list[str]]:
    for block in blocks:
        if block.get("type") == "table":
            return [[cell.get("text", "") for cell in row] for row in block.get("rows", [])]
    return [[""]]


def save_csv_blocks(output_path: Path, blocks: list[dict]) -> Path:
    rows = table_rows_from_blocks(blocks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        csv.writer(csv_file).writerows(rows)
    return _ensure_non_empty(output_path)


def save_excel_blocks(output_path: Path, blocks: list[dict], template_path: Path | None = None) -> Path:
    try:
        from openpyxl import Workbook, load_workbook
    except ImportError as exc:
        raise ValueError("Install openpyxl for the Excel editor.") from exc

    rows = table_rows_from_blocks(blocks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if template_path and template_path.exists():
        shutil.copyfile(template_path, output_path)
        workbook = load_workbook(output_path)
        sheet = workbook.active
        for row_index, row in enumerate(rows, start=1):
            for column_index, value in enumerate(row, start=1):
                sheet.cell(row=row_index, column=column_index).value = value
    else:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Edited"
        for row in rows:
            sheet.append(row)
    workbook.save(output_path)
    return _ensure_non_empty(output_path)


def _ensure_non_empty(output_path: Path) -> Path:
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError("Edited table output is blank.")
    return output_path
