from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import ALLOWED_ORIGINS, API_PREFIX, CORS_ALLOW_ORIGIN_REGEX, OUTPUT_DIR
from app.database.db import init_db
from app.routes import admin_routes, auth_routes, convert_routes, document_routes, editor_routes, history_routes, ocr_routes, upload_routes


app = FastAPI(title="OmniDocs API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"message": "OmniDocs API is running"}


app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(upload_routes.router, prefix=API_PREFIX)
app.include_router(document_routes.router, prefix=API_PREFIX)
app.include_router(editor_routes.router, prefix=API_PREFIX)
app.include_router(convert_routes.router, prefix=API_PREFIX)
app.include_router(ocr_routes.router, prefix=API_PREFIX)
app.include_router(history_routes.router, prefix=API_PREFIX)
app.include_router(admin_routes.router, prefix=API_PREFIX)
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
