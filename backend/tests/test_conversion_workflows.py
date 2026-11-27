import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

import fitz
from docx import Document
from openpyxl import Workbook, load_workbook
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation

from app.services.convert_service import process_document, process_multiple_images_to_pdf


class ConversionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "temp")
        cls.root = Path(cls.tmp.name)
        cls.out = cls.root / "output"
        cls.out.mkdir()
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "Workflow Test Document", fontsize=18)
        pdf.save(cls.root / "source.pdf")
        pdf.close()
        doc = Document()
        doc.add_paragraph("Workflow Test Document")
        doc.save(cls.root / "source.docx")
        presentation = Presentation()
        presentation.slides.add_slide(presentation.slide_layouts[1]).shapes.title.text = "Workflow Test Document"
        presentation.save(cls.root / "source.pptx")
        workbook = Workbook()
        workbook.active.append(["Name", "Count"])
        workbook.active.append(["Alice", 42])
        workbook.save(cls.root / "source.xlsx")
        with (cls.root / "source.csv").open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerows([["Name", "Count"], ["Alice", 42]])
        (cls.root / "source.md").write_text("# Workflow Test\n\nHello document.\n", encoding="utf-8")
        image = Image.new("RGB", (900, 200), "white")
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except OSError:
            font = ImageFont.load_default()
        ImageDraw.Draw(image).text((25, 50), "Workflow Test 123", fill="black", font=font)
        image.save(cls.root / "source.png")
        image.save(cls.root / "source.jpg")
        scan = fitz.open()
        page = scan.new_page(width=450, height=100)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        page.insert_image(page.rect, stream=buf.getvalue())
        scan.save(cls.root / "scan.pdf")
        scan.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def convert(self, name, file_type, task, **options):
        result = process_document(self.root / name, self.out, file_type, task, options=options)
        path = result["output_path"]
        self.assertTrue(path.is_file() and path.stat().st_size > 0)
        return path

    def test_pdf_workflows(self):
        with self.subTest("word"):
            doc = Document(self.convert("source.pdf", "pdf", "pdf_to_word"))
            self.assertIn("Workflow Test Document", " ".join(doc.element.body.itertext()))
        for task in ("pdf_to_csv", "pdf_to_excel", "pdf_to_powerpoint", "pdf_to_zip", "pdf_compress"):
            with self.subTest(task):
                path = self.convert("source.pdf", "pdf", task)
                if task == "pdf_to_excel":
                    load_workbook(path)
                elif task == "pdf_to_powerpoint":
                    self.assertEqual(len(Presentation(path).slides), 1)
                elif task == "pdf_to_zip":
                    self.assertIsNone(zipfile.ZipFile(path).testzip())
                elif task == "pdf_compress":
                    self.assertEqual(len(fitz.open(path)), 1)

    def test_office_and_table_workflows(self):
        for name, kind, task in (("source.docx", "word", "word_to_pdf"), ("source.pptx", "powerpoint", "powerpoint_to_pdf"), ("source.xlsx", "excel", "excel_to_pdf"), ("source.csv", "csv", "csv_to_pdf")):
            with self.subTest(task):
                with fitz.open(self.convert(name, kind, task)) as pdf:
                    self.assertGreater(len(pdf), 0)
                    self.assertIn("Workflow" if kind in ("word", "powerpoint") else "Alice", " ".join(p.get_text() for p in pdf))
        with self.subTest("excel_to_csv"):
            self.assertIn("Alice", self.convert("source.xlsx", "excel", "excel_to_csv").read_text(encoding="utf-8-sig"))
        with self.subTest("csv_to_excel"):
            self.assertEqual(load_workbook(self.convert("source.csv", "csv", "csv_to_excel")).active["A2"].value, "Alice")

    def test_excel_preview_values(self):
        from app.routes.document_routes import read_table_rows

        self.assertEqual(read_table_rows(self.root / "source.xlsx")[:2], [["Name", "Count"], ["Alice", "42"]])

    def test_legacy_excel(self):
        try:
            import xlwt
        except ImportError:
            self.skipTest("Install xlwt to generate a legacy Excel fixture")
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("Sheet1")
        sheet.write(0, 0, "Name")
        sheet.write(1, 0, "Alice")
        workbook.save(str(self.root / "legacy.xls"))
        self.assertIn("Alice", self.convert("legacy.xls", "excel", "excel_to_csv").read_text(encoding="utf-8-sig"))
        with fitz.open(self.convert("legacy.xls", "excel", "excel_to_pdf")) as pdf:
            self.assertIn("Alice", pdf[0].get_text())

    def test_markdown_workflows(self):
        for task in ("markdown_to_pdf", "markdown_to_word", "markdown_to_html", "markdown_to_text", "markdown_to_powerpoint"):
            with self.subTest(task):
                path = self.convert("source.md", "markdown", task)
                if task == "markdown_to_pdf":
                    with fitz.open(path) as pdf:
                        self.assertIn("Workflow", pdf[0].get_text())
                elif task == "markdown_to_word":
                    self.assertIn("Workflow", " ".join(p.text for p in Document(path).paragraphs))
                elif task == "markdown_to_powerpoint":
                    self.assertGreater(len(Presentation(path).slides), 0)
                else:
                    self.assertIn("Workflow", path.read_text(encoding="utf-8"))

    def test_image_workflows(self):
        for name, task in (("source.jpg", "jpg_to_png"), ("source.png", "png_to_jpg"), ("source.png", "image_compress"), ("source.png", "image_crop"), ("source.jpg", "jpg_to_heic"), ("source.png", "png_to_heic")):
            with self.subTest(task):
                path = self.convert(name, "image", task, crop_width=100, crop_height=80)
                self.assertTrue(path.exists())
                if task == "image_crop":
                    with Image.open(path) as image:
                        self.assertEqual(image.size, (100, 80))
        heic = self.out / "source.heic"
        for task in ("heic_to_jpg", "heic_to_png"):
            with self.subTest(task):
                result = process_document(heic, self.out, "heic", task)
                with Image.open(result["output_path"]) as image:
                    self.assertEqual(image.size, (900, 200))
        with self.subTest("images_to_pdf"):
            result = process_multiple_images_to_pdf([self.root / "source.png", self.root / "source.jpg"], self.out)
            with fitz.open(result["output_path"]) as pdf:
                self.assertEqual(len(pdf), 2)

    def test_ocr_workflows(self):
        for name, kind, task in (("source.png", "image", "ocr_extract"), ("scan.pdf", "pdf", "scanned_pdf_to_editable_text")):
            with self.subTest(task):
                self.assertIn("Workflow", self.convert(name, kind, task).read_text(encoding="utf-8"))
        heic = self.convert("source.png", "image", "png_to_heic")
        result = process_document(heic, self.out, "heic", "ocr_extract")
        self.assertIn("Workflow", result["output_path"].read_text(encoding="utf-8"))

    def test_mixed_pdf_ocr(self):
        pdf = fitz.open(self.root / "source.pdf")
        scanned = fitz.open(self.root / "scan.pdf")
        pdf.insert_pdf(scanned)
        pdf.save(self.root / "mixed.pdf")
        pdf.close()
        scanned.close()
        text = self.convert("mixed.pdf", "pdf", "scanned_pdf_to_editable_text").read_text(encoding="utf-8")
        self.assertIn("Workflow Test Document", text)
        self.assertIn("Workflow Test 123", text)

    def test_upload_download_api(self):
        try:
            from fastapi.testclient import TestClient
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy.pool import StaticPool
            from unittest.mock import patch
            from app.database.db import Base, get_db
            from app.models import subscription_model  # Register relationships before creating the test database.
            from app.main import app
            from app.routes import document_routes, upload_routes
        except ImportError:
            self.skipTest("Install httpx for API tests")
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)

        def override_db():
            session = session_factory()
            try:
                yield session
            finally:
                session.close()

        uploads = self.root / "api-uploads"
        uploads.mkdir(exist_ok=True)
        app.dependency_overrides[get_db] = override_db
        try:
            with patch.object(upload_routes, "UPLOAD_DIR", uploads), patch.object(upload_routes, "OUTPUT_DIR", self.out), patch.object(document_routes, "OUTPUT_DIR", self.out), patch("app.main.init_db"), TestClient(app) as client:
                for index, (filename, task, content_type) in enumerate((("source.pdf", "pdf_to_word", "application/pdf"), ("source.png", "png_to_jpg", "image/png"), ("source.xlsx", "excel_to_csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), ("source.pptx", "powerpoint_to_pdf", "application/vnd.openxmlformats-officedocument.presentationml.presentation"))):
                    with self.subTest(task):
                        with (self.root / filename).open("rb") as file:
                            response = client.post("/api/upload", data={"task": task, "guest_id": f"workflow-test-{index}"}, files={"file": (filename, file, content_type)})
                        self.assertEqual(response.status_code, 200, response.text)
                        result = response.json()
                        self.assertEqual(result["detected_task"], task)
                        downloaded = client.get(result["output_file_url"])
                        self.assertEqual(downloaded.status_code, 200)
                        self.assertGreater(len(downloaded.content), 0)
        finally:
            app.dependency_overrides.pop(get_db, None)
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
