from pathlib import Path


def extract_powerpoint_blocks(pptx_path: Path) -> tuple[str, list[dict]]:
    try:
        from pptx import Presentation
    except ImportError as exc:
        raise ValueError("Install python-pptx for the PowerPoint editor.") from exc

    presentation = Presentation(pptx_path)
    blocks = []
    text_lines = []
    for slide_index, slide in enumerate(presentation.slides):
        shapes = []
        for shape_index, shape in enumerate(slide.shapes):
            if not getattr(shape, "has_text_frame", False):
                continue
            text = shape.text.strip()
            if not text:
                continue
            shapes.append({"id": shape_index, "text": text})
            text_lines.append(f"Slide {slide_index + 1}: {text}")
        blocks.append({"type": "slide", "id": slide_index, "title": f"Slide {slide_index + 1}", "shapes": shapes})
    return "\n".join(text_lines), blocks


def save_powerpoint_blocks(template_path: Path, output_path: Path, blocks: list[dict]) -> Path:
    try:
        from pptx import Presentation
    except ImportError as exc:
        raise ValueError("Install python-pptx for the PowerPoint editor.") from exc

    presentation = Presentation(template_path)
    block_map = {block.get("id"): block for block in blocks}
    for slide_index, slide in enumerate(presentation.slides):
        block = block_map.get(slide_index, {})
        shape_map = {shape.get("id"): shape.get("text", "") for shape in block.get("shapes", [])}
        for shape_index, shape in enumerate(slide.shapes):
            if getattr(shape, "has_text_frame", False) and shape_index in shape_map:
                set_shape_text_preserving_first_run(shape, shape_map[shape_index])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(output_path)
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ValueError("Edited PowerPoint output is blank.")
    return output_path


def set_shape_text_preserving_first_run(shape, text: str) -> None:
    text_frame = shape.text_frame
    paragraphs = list(text_frame.paragraphs)
    if not paragraphs:
        text_frame.text = text
        return

    first_paragraph = paragraphs[0]
    if first_paragraph.runs:
        first_paragraph.runs[0].text = text
        for run in first_paragraph.runs[1:]:
            run.text = ""
    else:
        first_paragraph.text = text

    for paragraph in paragraphs[1:]:
        for run in paragraph.runs:
            run.text = ""
