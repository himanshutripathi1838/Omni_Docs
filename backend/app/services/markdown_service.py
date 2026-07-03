from pathlib import Path
import html
import re


def read_markdown(markdown_path: Path) -> str:
    text = markdown_path.read_text(encoding="utf-8-sig")
    return text if text.strip() else "# Empty Markdown\n\nNo content found in this Markdown file."


def markdown_to_blocks(markdown_text: str) -> list[dict]:
    blocks = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            blocks.append({"type": "blank", "text": ""})
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        bullet = re.match(r"^\s*[-*+]\s+(.+)$", line)
        numbered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if heading:
            blocks.append({"type": "heading", "level": len(heading.group(1)), "text": heading.group(2).strip()})
        elif bullet:
            blocks.append({"type": "bullet", "text": bullet.group(1).strip()})
        elif numbered:
            blocks.append({"type": "numbered", "text": numbered.group(1).strip()})
        else:
            blocks.append({"type": "paragraph", "text": line.strip()})
    return blocks


def markdown_to_text(markdown_path: Path, output_path: Path) -> Path:
    text = read_markdown(markdown_path)
    clean = re.sub(r"`([^`]+)`", r"\1", text)
    clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean)
    clean = re.sub(r"\*([^*]+)\*", r"\1", clean)
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
    return _write_non_empty(output_path, clean)


def markdown_to_html(markdown_path: Path, output_path: Path) -> Path:
    blocks = markdown_to_blocks(read_markdown(markdown_path))
    body = []
    in_list = False
    for block in blocks:
        if block["type"] != "bullet" and in_list:
            body.append("</ul>")
            in_list = False
        if block["type"] == "heading":
            level = min(block["level"], 6)
            body.append(f"<h{level}>{html.escape(block['text'])}</h{level}>")
        elif block["type"] == "bullet":
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{html.escape(block['text'])}</li>")
        elif block["type"] == "numbered":
            body.append(f"<p>{html.escape(block['text'])}</p>")
        elif block["type"] == "paragraph":
            body.append(f"<p>{html.escape(block['text'])}</p>")
        elif block["type"] == "blank":
            body.append("")
    if in_list:
        body.append("</ul>")

    document = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\" />\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        f"<title>{html.escape(markdown_path.stem)}</title>\n"
        "<style>body{font-family:Arial,sans-serif;line-height:1.55;max-width:900px;margin:40px auto;padding:0 24px;color:#0f172a}"
        "h1,h2,h3{color:#0f172a}code{background:#f1f5f9;padding:2px 4px;border-radius:4px}</style>\n"
        "</head>\n<body>\n"
        + "\n".join(body)
        + "\n</body>\n</html>\n"
    )
    return _write_non_empty(output_path, document)


def markdown_to_word(markdown_path: Path, output_path: Path) -> Path:
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError("Install python-docx for Markdown to Word.") from exc

    document = Document()
    for block in markdown_to_blocks(read_markdown(markdown_path)):
        if block["type"] == "heading":
            document.add_heading(block["text"], level=min(block["level"], 4))
        elif block["type"] == "bullet":
            document.add_paragraph(block["text"], style="List Bullet")
        elif block["type"] == "numbered":
            document.add_paragraph(block["text"], style="List Number")
        elif block["type"] == "paragraph":
            document.add_paragraph(block["text"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    return _ensure_non_empty(output_path, "Markdown to Word output is blank.")


def markdown_to_pdf(markdown_path: Path, output_path: Path) -> Path:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise ValueError("Install reportlab for Markdown to PDF.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    story = []
    bullet_items = []

    def flush_bullets():
        nonlocal bullet_items
        if bullet_items:
            story.append(ListFlowable(bullet_items, bulletType="bullet"))
            story.append(Spacer(1, 8))
            bullet_items = []

    for block in markdown_to_blocks(read_markdown(markdown_path)):
        if block["type"] != "bullet":
            flush_bullets()
        if block["type"] == "heading":
            style = styles["Title"] if block["level"] == 1 else styles["Heading2"]
            story.append(Paragraph(html.escape(block["text"]), style))
            story.append(Spacer(1, 8))
        elif block["type"] == "bullet":
            bullet_items.append(ListItem(Paragraph(html.escape(block["text"]), styles["BodyText"])))
        elif block["type"] in {"paragraph", "numbered"}:
            story.append(Paragraph(html.escape(block["text"]), styles["BodyText"]))
            story.append(Spacer(1, 6))
    flush_bullets()
    if not story:
        story.append(Paragraph("No Markdown content found.", styles["BodyText"]))
    SimpleDocTemplate(str(output_path), pagesize=A4, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54).build(story)
    return _ensure_non_empty(output_path, "Markdown to PDF output is blank.")


def markdown_to_powerpoint(markdown_path: Path, output_path: Path) -> Path:
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except ImportError as exc:
        raise ValueError("Install python-pptx for Markdown to PowerPoint.") from exc

    blocks = markdown_to_blocks(read_markdown(markdown_path))
    presentation = Presentation()
    current_slide = None
    body_shape = None

    def add_slide(title: str):
        slide = presentation.slides.add_slide(presentation.slide_layouts[1])
        slide.shapes.title.text = title
        body = slide.placeholders[1]
        body.text = ""
        return slide, body

    for block in blocks:
        if block["type"] == "heading" and block["level"] <= 2:
            current_slide, body_shape = add_slide(block["text"])
            continue
        if current_slide is None:
            current_slide, body_shape = add_slide(markdown_path.stem)
        if block["type"] in {"paragraph", "bullet", "numbered"}:
            frame = body_shape.text_frame
            paragraph = frame.paragraphs[0] if not frame.paragraphs[0].text else frame.add_paragraph()
            paragraph.text = block["text"]
            paragraph.font.size = Pt(20 if block["type"] == "paragraph" else 18)
            paragraph.level = 1 if block["type"] == "bullet" else 0

    if len(presentation.slides) == 0:
        presentation.slides.add_slide(presentation.slide_layouts[0]).shapes.title.text = markdown_path.stem
    for slide in presentation.slides:
        if slide.shapes.title:
            slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(34)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(output_path)
    return _ensure_non_empty(output_path, "Markdown to PowerPoint output is blank.")


def _write_non_empty(output_path: Path, text: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text if text.strip() else "No content found.", encoding="utf-8")
    return _ensure_non_empty(output_path, "Markdown output is blank.")


def _ensure_non_empty(output_path: Path, message: str) -> Path:
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError(message)
    return output_path
