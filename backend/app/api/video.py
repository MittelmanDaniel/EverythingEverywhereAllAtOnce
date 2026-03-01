import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx

from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["video"])


class VideoGenerateRequest(BaseModel):
    """Request to generate a Seedance 1.5 video showing the life that was missed."""

    prompt: str  # e.g. "A person finally stepping on stage at a ballet recital..."
    image_url: str = ""  # optional reference image for image-to-video
    duration: str = "5"  # seconds: "5" or "10"
    aspect_ratio: str = "16:9"  # "16:9", "9:16", "1:1"
    seed: int | None = None


class VideoGenerateResponse(BaseModel):
    request_id: str
    status: str  # "IN_QUEUE" | "IN_PROGRESS" | "COMPLETED"
    video_url: str = ""


class VideoStatusResponse(BaseModel):
    request_id: str
    status: str
    video_url: str = ""


FAL_BASE = "https://queue.fal.run"
SEEDANCE_TEXT_TO_VIDEO = "fal-ai/seedance-1-5/text-to-video"
SEEDANCE_IMAGE_TO_VIDEO = "fal-ai/seedance-1-5/image-to-video"


def _build_prompt(user_prompt: str) -> str:
    """Wrap the user's verse description in cinematic framing for the missed life."""
    return (
        f"Cinematic, dreamlike footage of an alternate life: {user_prompt} "
        "Warm golden-hour light, shallow depth of field, gentle camera movement. "
        "Emotionally resonant, bittersweet, like a memory that never happened."
    )


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    req: VideoGenerateRequest,
    user: User = Depends(get_current_user),
):
    """Submit a Seedance 1.5 video generation job for a verse's missed life."""
    if not settings.fal_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video generation not configured",
        )

    endpoint = SEEDANCE_IMAGE_TO_VIDEO if req.image_url else SEEDANCE_TEXT_TO_VIDEO

    payload = {
        "prompt": _build_prompt(req.prompt),
        "duration": req.duration,
        "aspect_ratio": req.aspect_ratio,
    }
    if req.seed is not None:
        payload["seed"] = req.seed
    if req.image_url:
        payload["image_url"] = req.image_url

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{FAL_BASE}/{endpoint}",
            headers={
                "Authorization": f"Key {settings.fal_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30.0,
        )

    if resp.status_code != 200:
        logger.error(f"Seedance submit failed: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Video generation request failed",
        )

    data = resp.json()
    return VideoGenerateResponse(
        request_id=data.get("request_id", ""),
        status=data.get("status", "IN_QUEUE"),
        video_url=data.get("video", {}).get("url", ""),
    )


@router.get("/status/{request_id}", response_model=VideoStatusResponse)
async def get_video_status(
    request_id: str,
    user: User = Depends(get_current_user),
):
    """Poll the status of a Seedance 1.5 video generation job."""
    if not settings.fal_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video generation not configured",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{FAL_BASE}/{SEEDANCE_TEXT_TO_VIDEO}/requests/{request_id}/status",
            headers={"Authorization": f"Key {settings.fal_api_key}"},
            timeout=15.0,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Status check failed")

    data = resp.json()
    video_url = ""
    if data.get("status") == "COMPLETED":
        # Fetch the result to get the video URL
        async with httpx.AsyncClient() as client:
            result_resp = await client.get(
                f"{FAL_BASE}/{SEEDANCE_TEXT_TO_VIDEO}/requests/{request_id}",
                headers={"Authorization": f"Key {settings.fal_api_key}"},
                timeout=15.0,
            )
        if result_resp.status_code == 200:
            result_data = result_resp.json()
            video_url = result_data.get("video", {}).get("url", "")

    return VideoStatusResponse(
        request_id=request_id,
        status=data.get("status", "UNKNOWN"),
        video_url=video_url,
    )
