"""Ingestion endpoint."""

import os
import shutil
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from src.api.dependencies import TaskStoreDep
from src.core.settings import settings
from src.schemas.ingestion import IngestResponse, TaskRecord
from src.services.ingestion import run_ingestion_logic

router = APIRouter()


@router.post("/ingest", status_code=202, response_model=IngestResponse)
async def ingest_endpoint(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(...)],
    task_store: TaskStoreDep,
) -> dict[str, str]:
    """Endpoint to upload and process a PDF file."""
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    task_id = str(uuid.uuid4())
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)

    file_path = upload_dir / f"{task_id}_{file.filename}"

    def _write_file() -> None:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    try:
        await run_in_threadpool(_write_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {e}") from e

    task_store.create(task_id)
    background_tasks.add_task(run_ingestion_logic, str(file_path), task_id)

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
