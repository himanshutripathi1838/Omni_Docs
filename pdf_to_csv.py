"""Convert a PDF file to CSV using pdfplumber, with optional OCR fallback.

Example:
    python pdf_to_csv.py input.pdf output.csv

By default this script combines all tables/text from all pages into one CSV.
Use --split-pages if you want one CSV per page instead.

For scanned PDFs, install Tesseract OCR and Poppler on your system, then run:
    python pdf_to_csv.py input.pdf output.csv --ocr
"""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


# Project venv fallback lets `python pdf_to_csv.py ...` work even if global Python
# cannot import the packages but the app's virtual environment can.
PROJECT_VENV_PYTHON = Path(__file__).resolve().parent / "backend" / ".venv" / "Scripts" / "python.exe"


def load_pdfplumber() -> Any:
    """Import pdfplumber only when conversion starts, so --help works before install."""
    try:
        import pdfplumber
    except ImportError as exc:
        if PROJECT_VENV_PYTHON.exists() and Path(sys.executable).resolve() != PROJECT_VENV_PYTHON.resolve():
            print(f"pdfplumber not found in {sys.executable}. Re-running with project venv Python...", flush=True)
            completed = subprocess.run([str(PROJECT_VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]], check=False)
            raise SystemExit(completed.returncode)
        raise SystemExit("pdfplumber is not installed. Run: pip install -r requirements.txt") from exc
    return pdfplumber


# You can set default paths here if you do not want to use command-line args.
DEFAULT_INPUT_PDF = ""
DEFAULT_OUTPUT_CSV = "output.csv"
DEFAULT_POPPLER_BIN = Path(r"D:\Release-26.02.0-0\poppler-26.02.0\Library\bin")
DEFAULT_TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


def clean_cell(value: object) -> str:
    """Convert empty cells to blank strings and trim extra spaces."""
    if value is None:
        return ""
    return str(value).strip()


def clean_row(row: list[object]) -> list[str]:
    """Clean every cell in a table row."""
    return [clean_cell(cell) for cell in row]


def is_empty_row(row: list[str]) -> bool:
    """Check whether a row has no useful text."""
    return not any(cell.strip() for cell in row)


def normalize_header(row: list[str]) -> tuple[str, ...]:
    """Normalize a header row so repeated headers can be detected."""
    return tuple(cell.strip().lower() for cell in row if cell.strip())


def append_table_rows(
    output_rows: list[list[str]],
    table: list[list[object]],
    seen_headers: set[tuple[str, ...]],
) -> None:
    """Add table rows to output and skip duplicate header rows."""
    for row_index, raw_row in enumerate(table):
        row = clean_row(raw_row)
        if is_empty_row(row):
            continue

        # Treat the first row of each extracted table as a possible header.
        header_key = normalize_header(row)
        if row_index == 0 and header_key:
            if header_key in seen_headers:
                continue
            seen_headers.add(header_key)

        output_rows.append(row)


def extract_page_rows(page: Any, page_number: int, seen_headers: set[tuple[str, ...]]) -> list[list[str]]:
    """Extract table rows from one page, or plain text if no table exists."""
    page_rows: list[list[str]] = []

    # First try to extract tables from the page.
    tables = page.extract_tables() or []
    for table in tables:
        append_table_rows(page_rows, table, seen_headers)

    if page_rows:
        return page_rows

    # If there is no table, keep plain text instead of skipping the page.
    text = (page.extract_text() or "").strip()
    if text:
        return [[f"Page {page_number} text", text]]

    # If there is no table and no text, the page might be scanned/image-based.
    if page.images:
        print(f"Warning: Page {page_number} looks image-based. OCR is needed, for example with pytesseract.")
    else:
        print(f"Warning: Page {page_number} is empty.")

    return [[f"Page {page_number}", "No table or selectable text found"]]


def extract_text_with_ocr(pdf_path: Path) -> list[list[str]]:
    """Run OCR on a scanned/image-based PDF and return text lines as CSV rows."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise SystemExit(
            "OCR libraries are not installed. Run: pip install -r requirements.txt\n"
            "Also install Tesseract OCR and Poppler, then try again."
        ) from exc

    if DEFAULT_TESSERACT_EXE.exists():
        pytesseract.pytesseract.tesseract_cmd = str(DEFAULT_TESSERACT_EXE)
    elif not shutil.which("tesseract"):
        raise SystemExit("Tesseract OCR was not found. Install it or add tesseract.exe to PATH.")

    poppler_path = str(DEFAULT_POPPLER_BIN) if DEFAULT_POPPLER_BIN.exists() else None
    if not poppler_path and not shutil.which("pdftoppm"):
        raise SystemExit("Poppler was not found. Add Poppler's bin folder to PATH or update DEFAULT_POPPLER_BIN.")

    print("No selectable text found. This PDF may be scanned/image-based.")
    print("Running OCR with pytesseract. This can take time for large PDFs...")

    rows: list[list[str]] = []
    images = convert_from_path(str(pdf_path), poppler_path=poppler_path)
    for page_number, page_image in enumerate(images, start=1):
        print(f"OCR processing page {page_number}/{len(images)}...")
        text = pytesseract.image_to_string(page_image, lang="eng+hin")
        for line in text.splitlines():
            clean_line = line.strip()
            if clean_line:
                rows.append([clean_line])

    return rows


def write_csv(rows: list[list[str]], output_path: Path) -> None:
    """Write rows to CSV with UTF-8 BOM so Hindi/regional text opens well in Excel."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(rows)


def has_useful_rows(rows: list[list[str]]) -> bool:
    """Return True if extraction produced at least one meaningful row."""
    return any(any(cell.strip() for cell in row) for row in rows)


def only_no_text_rows(rows: list[list[str]]) -> bool:
    """Detect placeholder rows created for empty/scanned pages."""
    if not rows:
        return True
    return all("No table or selectable text found" in " ".join(row) or "PDF is empty" in " ".join(row) for row in rows)


def convert_pdf_to_single_csv(pdf_path: Path, output_csv: Path, use_ocr: bool = False) -> None:
    """Combine tables/text from every page into one CSV file."""
    all_rows: list[list[str]] = []
    seen_headers: set[tuple[str, ...]] = set()
    pdfplumber = load_pdfplumber()

    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            all_rows.append(["PDF is empty"])

        for page_number, page in enumerate(pdf.pages, start=1):
            page_rows = extract_page_rows(page, page_number, seen_headers)
            all_rows.extend(page_rows)

    if use_ocr and (not has_useful_rows(all_rows) or only_no_text_rows(all_rows)):
        all_rows = extract_text_with_ocr(pdf_path)

    write_csv(all_rows, output_csv)


def convert_pdf_to_page_csvs(pdf_path: Path, output_csv: Path, use_ocr: bool = False) -> list[Path]:
    """Save each page's extracted rows as a separate CSV file."""
    saved_paths: list[Path] = []
    seen_headers: set[tuple[str, ...]] = set()
    output_dir = output_csv.parent
    output_stem = output_csv.stem
    pdfplumber = load_pdfplumber()

    if use_ocr:
        rows = extract_text_with_ocr(pdf_path)
        ocr_output = output_dir / f"{output_stem}_ocr.csv"
        write_csv(rows, ocr_output)
        return [ocr_output]

    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            empty_path = output_dir / f"{output_stem}_empty.csv"
            write_csv([["PDF is empty"]], empty_path)
            return [empty_path]

        for page_number, page in enumerate(pdf.pages, start=1):
            page_rows = extract_page_rows(page, page_number, seen_headers)
            page_output = output_dir / f"{output_stem}_page_{page_number}.csv"
            write_csv(page_rows, page_output)
            saved_paths.append(page_output)

    return saved_paths


def parse_args() -> argparse.Namespace:
    """Read command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert PDF tables/text to CSV using pdfplumber.")
    parser.add_argument("input_pdf", nargs="?", default=DEFAULT_INPUT_PDF, help="Path to input PDF file")
    parser.add_argument("output_csv", nargs="?", default=DEFAULT_OUTPUT_CSV, help="Path to output CSV file")
    parser.add_argument(
        "--split-pages",
        action="store_true",
        help="Save one CSV per PDF page instead of combining all pages into one CSV",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Use pytesseract OCR if the PDF has no selectable text. Requires Tesseract and Poppler.",
    )
    return parser.parse_args()


def main() -> None:
    """Validate paths, run conversion, and print a success message."""
    args = parse_args()
    pdf_path = Path(args.input_pdf).expanduser()
    output_csv = Path(args.output_csv).expanduser()

    if not args.input_pdf:
        raise SystemExit("Please provide an input PDF path. Example: python pdf_to_csv.py input.pdf output.csv")

    if not pdf_path.exists():
        raise SystemExit(f"Input PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise SystemExit("Input file must be a PDF.")

    if args.split_pages:
        saved_paths = convert_pdf_to_page_csvs(pdf_path, output_csv, use_ocr=args.ocr)
        print("Success! CSV files saved:")
        for saved_path in saved_paths:
            print(saved_path.resolve())
    else:
        convert_pdf_to_single_csv(pdf_path, output_csv, use_ocr=args.ocr)
        print(f"Success! CSV saved at: {output_csv.resolve()}")


if __name__ == "__main__":
    main()
