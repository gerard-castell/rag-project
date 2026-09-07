"""Health check routes."""

import torch
from fastapi import APIRouter

from src.api.dependencies import LlamaCppClientDep, VRAMSchedulerDep

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Return a basic liveness check."""
    gpu_status = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    return {"status": "ok", "device": gpu_status}


@router.get("/health/gpu")
async def health_gpu(
    vram_scheduler: VRAMSchedulerDep, llama_client: LlamaCppClientDep
) -> dict[str, object]:
    """Report llama.cpp reachability, container state, and GPU lock status."""
    status = await vram_scheduler.get_status()
    reachable = await llama_client.health()
    return {"llama_cpp_reachable": reachable, **status}
