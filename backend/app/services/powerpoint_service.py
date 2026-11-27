from pathlib import Path
from io import BytesIO
import shutil
import subprocess
from tempfile import TemporaryDirectory

import fitz


def _ensure_non_empty(output_path: Path, message: str) -> Path:
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError(message)
    return output_path


def pdf_to_powerpoint(pdf_path: Path, output_path: Path) -> Path:
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.util import Pt
    except ImportError as exc:
        raise ValueError("Install python-pptx for PDF to PowerPoint.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    presentation = Presentation()

    with fitz.open(pdf_path) as pdf:
        if pdf.page_count == 0:
            raise ValueError("No pages were found in the PDF.")

        first_rect = pdf[0].rect
        presentation.slide_width = int(first_rect.width * 12700)
        presentation.slide_height = int(first_rect.height * 12700)

        blank_layout = presentation.slide_layouts[6]
        for page in pdf:
            slide = presentation.slides.add_slide(blank_layout)
            spans = [span for block in page.get_text("dict").get("blocks", []) for line in block.get("lines", []) for span in line.get("spans", []) if span.get("text", "").strip()]
            background = fitz.open()
            background.insert_pdf(pdf, from_page=page.number, to_page=page.number)
            background_page = background[0]
            for span in spans:
                background_page.add_redact_annot(fitz.Rect(span["bbox"]), fill=False, cross_out=False)
            if spans:
                background_page.apply_redactions(images=0, graphics=0)
            pixmap = background_page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            slide.shapes.add_picture(
                BytesIO(pixmap.tobytes("png")),
                0,
                0,
                width=presentation.slide_width,
                height=presentation.slide_height,
            )
            background.close()
            scale_x = presentation.slide_width / page.rect.width
            scale_y = presentation.slide_height / page.rect.height
            for span in spans:
                rect = fitz.Rect(span["bbox"])
                box = slide.shapes.add_textbox(int(rect.x0 * scale_x), int(rect.y0 * scale_y), max(1, int((rect.width + 4) * scale_x)), max(1, int((rect.height + 4) * scale_y)))
                frame = box.text_frame
                frame.word_wrap = False
                frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
                run = frame.paragraphs[0].add_run()
                run.text = span["text"]
                run.font.size = Pt(span.get("size", 11) * scale_y / 12700)
                run.font.name = span.get("font", "Arial").split("+")[-1]
                flags = span.get("flags", 0)
                run.font.bold = bool(flags & 16)
                run.font.italic = bool(flags & 2)
                color = span.get("color", 0) & 0xFFFFFF
                run.font.color.rgb = RGBColor((color >> 16) & 255, (color >> 8) & 255, color & 255)

    presentation.save(output_path)
    return _ensure_non_empty(output_path, "PowerPoint output is blank. Please check the PDF again.")


def powerpoint_to_pdf(powerpoint_path: Path, output_path: Path) -> Path:
    converter = _find_office_converter()
    if not converter:
        raise ValueError("Install and configure LibreOffice for PowerPoint to PDF.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as profile_dir:
        try:
            subprocess.run(
                [
                    converter,
                    "--headless",
                    "--nologo",
                    "--nofirststartwizard",
                    f"-env:UserInstallation=file:///{Path(profile_dir).as_posix()}",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(output_path.parent),
                    str(powerpoint_path),
                ],
                check=True,
                capture_output=True,
                timeout=90,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError("PowerPoint to PDF conversion failed. Please check the PPT/PPTX file.") from exc

    generated_path = output_path.parent / f"{powerpoint_path.stem}.pdf"
    if generated_path.exists() and generated_path != output_path:
        generated_path.replace(output_path)

    return _ensure_non_empty(output_path, "PowerPoint to PDF output is blank. Please check the PPT/PPTX file.")


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
