from fastapi import APIRouter


router = APIRouter(prefix="/convert", tags=["convert"])


@router.get("/supported")
def supported_conversions():
    return {
        "supported": [
            "image_to_word",
            "image_to_pdf",
            "pdf_to_word",
            "pdf_to_csv",
            "pdf_to_excel",
            "word_to_pdf",
            "ocr_extract",
            "text_replace",
        ]
    }
