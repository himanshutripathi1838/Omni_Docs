from pathlib import Path
import csv


def _load_pandas():
    try:
        import pandas as pd
    except ImportError as exc:
        raise ValueError("Install pandas and openpyxl for Excel/CSV conversion.") from exc
    return pd


def excel_to_csv(input_path: Path, output_path: Path) -> Path:
    pd = _load_pandas()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # MVP: first sheet only. Future: export all sheets as separate CSV files inside a ZIP.
    dataframe = pd.read_excel(input_path, sheet_name=0, engine="xlrd" if input_path.suffix.lower() == ".xls" else "openpyxl")
    if dataframe.empty:
        dataframe = pd.DataFrame([["No rows found in the first sheet."]])
    dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")
    return _ensure_non_empty(output_path, "Excel to CSV output is blank.")


def excel_to_pdf(input_path: Path, output_path: Path) -> Path:
    pd = _load_pandas()
    dataframe = pd.read_excel(input_path, sheet_name=0, engine="xlrd" if input_path.suffix.lower() == ".xls" else "openpyxl").fillna("")
    rows = [list(map(str, dataframe.columns.tolist()))]
    rows.extend(dataframe.astype(str).values.tolist())
    if len(rows) == 1 and not rows[0]:
        rows = [["No rows found in the first sheet."]]
    return _rows_to_pdf(rows, input_path.name, output_path)


def csv_to_excel(input_path: Path, output_path: Path) -> Path:
    pd = _load_pandas()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = pd.read_csv(input_path, encoding="utf-8-sig")
    if dataframe.empty:
        dataframe = pd.DataFrame([["No rows found in this CSV."]])
    dataframe.to_excel(output_path, index=False, engine="openpyxl")
    return _ensure_non_empty(output_path, "CSV to Excel output is blank.")


def csv_to_pdf(input_path: Path, output_path: Path) -> Path:
    with input_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = [row for row in csv.reader(csv_file)]

    if not rows:
        rows = [["No rows found in this CSV."]]
    return _rows_to_pdf(rows, input_path.name, output_path)


def _rows_to_pdf(rows: list[list[str]], title: str, output_path: Path) -> Path:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise ValueError("Install reportlab for Table to PDF.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=24,
        rightMargin=24,
        topMargin=28,
        bottomMargin=28,
    )
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    max_columns = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (max_columns - len(row)) for row in rows]
    table_data = [
        [Paragraph(str(cell), styles["BodyText"]) for cell in row]
        for row in normalized_rows
    ]
    table = Table(table_data, repeatRows=1 if len(table_data) > 1 else 0)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    document.build(story)
    return _ensure_non_empty(output_path, "CSV to PDF output is blank.")


def _ensure_non_empty(output_path: Path, message: str) -> Path:
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError(message)
    return output_path
