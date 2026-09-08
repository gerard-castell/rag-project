"""Ingestion endpoint."""

import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from src.api.dependencies import TaskStoreDep
from src.core.settings import settings
from src.schemas.ingestion import IngestResponse, TaskRecord
from src.services.ingestion import run_ingestion_logic

router = APIRouter()

_PDF_MAGIC_BYTES = b"%PDF-"
_COPY_CHUNK_SIZE = 1024 * 1024


class _NotAPDFError(Exception):
    """Raised internally when the uploaded content isn't actually a PDF."""


class _UploadTooLargeError(Exception):
    """Raised internally when the upload exceeds the configured size limit."""


@router.post("/ingest", status_code=202, response_model=IngestResponse)
async def ingest_endpoint(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(...)],
    task_store: TaskStoreDep,
) -> dict[str, str]:
    """Endpoint to upload and process a PDF file."""
    safe_filename = Path(file.filename or "").name
    if not safe_filename or not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    task_id = str(uuid.uuid4())
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)

    file_path = upload_dir / f"{task_id}_{safe_filename}"

    def _write_file() -> None:
        header = file.file.read(len(_PDF_MAGIC_BYTES))
        if not header.startswith(_PDF_MAGIC_BYTES):
            raise _NotAPDFError
        file.file.seek(0)

        bytes_written = 0
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(_COPY_CHUNK_SIZE):
                bytes_written += len(chunk)
                if bytes_written > settings.max_upload_size_bytes:
                    raise _UploadTooLargeError
                buffer.write(chunk)

    try:
        await run_in_threadpool(_write_file)
    except _NotAPDFError as e:
        raise HTTPException(
            status_code=400, detail="File content is not a valid PDF."
        ) from e
    except _UploadTooLargeError as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413, detail="File exceeds maximum upload size."
        ) from e
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error writing file: {e}") from e

    task_store.create(task_id)
    background_tasks.add_task(
        run_ingestion_logic, str(file_path), task_id, safe_filename
    )

    return {
        "status": "queued",
        "task_id": task_id,
        "info": "The file is being processed by the GPU.",
    }


@router.get("/ingest/{task_id}", response_model=TaskRecord)
async def ingest_status_endpoint(task_id: str, task_store: TaskStoreDep) -> TaskRecord:
    """Endpoint to check the status of an ingestion task."""
    record = task_store.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown task_id.")
    return record
