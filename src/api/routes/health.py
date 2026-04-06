"""Health check route."""

import torch
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    gpu_status = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    return {"status": "ok", "device": gpu_status}
