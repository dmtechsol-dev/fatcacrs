from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import (
    FRONTEND_ASSETS_DIR,
    FRONTEND_DIST_DIR,
    FRONTEND_INDEX,
    GENERATED_DIR,
    REQUIRE_FRONTEND,
    ROOT_SCHEMA,
)
from backend.excel_parser import parse_excel_bytes
from backend.models import (
    DownloadArtifact,
    GenerateRequest,
    GenerationResponse,
    UploadResponse,
    ValidateRequest,
    ValidationResponse,
)
from backend.validators import build_summary, validate_records
from backend.xml_builder import build_xml
from backend.xsd_validator import schema_readiness, validate_xml

logger = logging.getLogger("uvicorn.error")


def frontend_available() -> bool:
    return FRONTEND_INDEX.is_file() and FRONTEND_ASSETS_DIR.is_dir()


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        if REQUIRE_FRONTEND and not frontend_available():
            raise RuntimeError(
                "Frontend build is required but "
                f"{FRONTEND_INDEX} or {FRONTEND_ASSETS_DIR} is missing."
            )
        schema = schema_readiness(ROOT_SCHEMA)
        logger.info(
            "FATCA/CRS service started: routes=%d frontend=%s "
            "frontend_dir=%s schema=%s",
            len(application.routes),
            "available" if frontend_available() else "not-built",
            FRONTEND_DIST_DIR,
            schema.status,
        )
        yield
    except Exception:
        logger.exception("FATCA/CRS service stopped after an application error.")
        raise


app = FastAPI(
    title="Local FATCA/CRS FC XML Generator",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict[str, dict] = {}


def health_payload():
    return {
        "status": "ok",
        "service": "fatca-crs-xml-generator",
        "frontend": frontend_available(),
        "schema": schema_readiness(ROOT_SCHEMA).model_dump(by_alias=True),
    }


@app.get("/", include_in_schema=False)
def root():
    if frontend_available():
        return FileResponse(
            FRONTEND_INDEX,
            media_type="text/html",
            headers={"Cache-Control": "no-cache"},
        )
    return {
        "status": "ok",
        "service": "fatca-crs-xml-generator",
        "message": "API service is running; the frontend build is unavailable.",
        "health": "/health",
        "docs": "/docs",
        "apiPrefix": "/api",
    }


@app.get("/health", include_in_schema=False)
def deployment_health():
    return health_payload()


@app.get("/api/health")
def health():
    return health_payload()


@app.post("/api/upload-excel", response_model=UploadResponse)
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Upload an .xlsx workbook.")
    content = await file.read()
    try:
        parsed = parse_excel_bytes(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    validated = validate_records(parsed)
    session_id = uuid4().hex
    SESSIONS[session_id] = {
        "file_name": file.filename,
        "records": [record.model_dump() for record in validated],
    }
    return UploadResponse(
        session_id=session_id,
        file_name=file.filename,
        records=validated,
        summary=build_summary(validated),
        schema_status=schema_readiness(ROOT_SCHEMA),
    )


@app.post("/api/validate", response_model=ValidationResponse)
def validate(request: ValidateRequest):
    records = validate_records(request.records, request.settings)
    if request.session_id and request.session_id in SESSIONS:
        SESSIONS[request.session_id]["records"] = [
            record.model_dump() for record in records
        ]
    return ValidationResponse(
        records=records,
        summary=build_summary(records),
        can_generate=not any(record.errors for record in records),
    )


def write_artifact(suffix: str, content: bytes | str) -> str:
    file_id = f"{uuid4().hex}{suffix}"
    path = GENERATED_DIR / file_id
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return file_id


def text_report(payload: dict) -> str:
    schema = payload["schemaValidation"]
    summary = payload["summary"]
    lines = [
        "FATCA/CRS FC XML Validation Report",
        "=" * 38,
        f"MessageRefId: {payload['messageRefId']}",
        f"Draft export: {'Yes' if payload['draft'] else 'No'}",
        f"Schema status: {schema['status']}",
        f"Schema message: {schema['message']}",
        f"Total records: {summary['totalRecords']}",
        f"Valid records: {summary['validRecords']}",
        f"Error records: {summary['errorRecords']}",
        f"Warning records: {summary['warningRecords']}",
    ]
    if schema["missingImports"]:
        lines.append("Missing imports: " + ", ".join(schema["missingImports"]))
    if schema["errors"]:
        lines.append("Schema errors:")
        lines.extend(f"- {error}" for error in schema["errors"])
    return "\n".join(lines) + "\n"


@app.post("/api/generate-xml", response_model=GenerationResponse)
def generate_xml(request: GenerateRequest):
    records = validate_records(request.records, request.settings)
    data_errors = [
        {
            "rowNumber": record.row_number,
            "accountNumber": record.account_number,
            "errors": record.errors,
        }
        for record in records
        if record.errors
    ]
    if data_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Correct blocking record errors before generation.",
                "records": data_errors,
            },
        )

    xml_content, message_ref_id = build_xml(records, request.settings)
    schema_validation = validate_xml(xml_content, ROOT_SCHEMA)
    if not schema_validation.valid and not request.allow_draft:
        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    "Full XSD validation did not pass. Enable draft export "
                    "only if you intentionally need an unvalidated file."
                ),
                "schemaValidation": schema_validation.model_dump(by_alias=True),
            },
        )

    draft = not schema_validation.valid
    summary = build_summary(records)
    report = {
        "messageRefId": message_ref_id,
        "draft": draft,
        "summary": summary.model_dump(by_alias=True),
        "schemaValidation": schema_validation.model_dump(by_alias=True),
        "records": [
            {
                "rowNumber": record.row_number,
                "accountNumber": record.account_number,
                "errors": record.errors,
                "warnings": record.warnings,
            }
            for record in records
        ],
    }
    xml_id = write_artifact(".xml", xml_content)
    json_id = write_artifact(
        ".json", json.dumps(report, indent=2, ensure_ascii=True)
    )
    text_id = write_artifact(".txt", text_report(report))
    year = request.settings.reporting_period[:4]
    prefix = "DRAFT_" if draft else ""
    return GenerationResponse(
        message_ref_id=message_ref_id,
        xml_preview=xml_content.decode("utf-8"),
        xml=DownloadArtifact(
            file_id=xml_id,
            file_name=f"{prefix}FC_CRS_{year}_{message_ref_id}.xml",
        ),
        validation_json=DownloadArtifact(
            file_id=json_id,
            file_name=f"validation_{message_ref_id}.json",
        ),
        validation_text=DownloadArtifact(
            file_id=text_id,
            file_name=f"validation_{message_ref_id}.txt",
        ),
        schema_validation=schema_validation,
        draft=draft,
    )


@app.get("/api/download/{file_id}")
def download(file_id: str):
    if Path(file_id).name != file_id:
        raise HTTPException(status_code=400, detail="Invalid file identifier.")
    path = GENERATED_DIR / file_id
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Generated file not found.")
    return FileResponse(path, filename=file_id)


if FRONTEND_ASSETS_DIR.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_ASSETS_DIR),
        name="frontend-assets",
    )


@app.get("/{frontend_path:path}", include_in_schema=False)
def frontend_route(frontend_path: str):
    if frontend_path == "api" or frontend_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    if frontend_available():
        return FileResponse(
            FRONTEND_INDEX,
            media_type="text/html",
            headers={"Cache-Control": "no-cache"},
        )
    raise HTTPException(
        status_code=503,
        detail="Frontend build is unavailable.",
    )
