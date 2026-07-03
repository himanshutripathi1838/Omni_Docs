# OmniDocs

OmniDocs is an AI-powered document workspace MVP. Users upload PDF, Word, image, spreadsheet, presentation, or scanned documents and type natural commands such as `Is photo ko Word me convert kar do`. The backend detects the file type, parses the command with rule-based logic, routes the job to a processing service, stores output locally, and saves history in SQLite.

## Stack

- Frontend: React, Vite, JavaScript, Tailwind CSS, Axios, React Router, Lucide icons
- Backend: FastAPI, Uvicorn, SQLAlchemy, SQLite, PyMuPDF, python-docx, Pillow
- Storage: local `backend/uploads` and `backend/outputs`
- OCR: placeholder service ready for PaddleOCR or Tesseract integration

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Backend Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`.

## Core APIs

- `POST /api/upload` - accepts `file` and `command`
- `GET /api/documents/download/{filename}` - downloads processed output
- `GET /api/history` - lists previous jobs
- `POST /api/history` - creates a history entry
- `GET /api/admin/stats` - returns usage summary
- `POST /api/auth/register` - creates a local user
- `POST /api/auth/login` - logs in a local user

## MVP Notes

- SQLite is used for MVP speed and portability.
- Firebase can be added later for Auth, Firestore metadata, and Storage.
- Word to PDF, PDF merge, PDF split, compression, and advanced PDF text replacement are placeholders.
- OCR currently returns placeholder text. Add PaddleOCR or Tesseract inside `backend/app/services/ocr_service.py`.
