from pathlib import Path
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
    except ImportError as exc:
        raise ValueError("Install python-pptx for PDF to PowerPoint.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    presentation = Presentation()

    with fitz.open(pdf_path) as pdf, TemporaryDirectory() as temp_dir:
        if pdf.page_count == 0:
            raise ValueError("No pages were found in the PDF.")

        first_rect = pdf[0].rect
        presentation.slide_width = int(first_rect.width * 12700)
        presentation.slide_height = int(first_rect.height * 12700)

        blank_layout = presentation.slide_layouts[6]
        for page_index, page in enumerate(pdf, start=1):
            image_path = Path(temp_dir) / f"page_{page_index}.png"
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pixmap.save(image_path)

            slide = presentation.slides.add_slide(blank_layout)
            slide.shapes.add_picture(
                str(image_path),
                0,
                0,
                width=presentation.slide_width,
                height=presentation.slide_height,
            )

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
