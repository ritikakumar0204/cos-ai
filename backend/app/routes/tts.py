"""
Text-to-speech routes.

Provides a backend proxy to ElevenLabs so API keys remain server-side.
"""

from __future__ import annotations

import json
from urllib import error, request

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..config import get_settings

router = APIRouter(prefix="/tts", tags=["tts"])
FALLBACK_TTS_TEXT = (
    "Maya Chen (Lead) in Product is referencing an earlier version of this decision. "
    "A targeted update would bring Product into alignment and prevent execution inconsistencies."
)


class ElevenLabsTtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str | None = None
    model_id: str | None = None


def _multipart_form_data(parts: list[tuple[str, str | bytes, str | None]]) -> tuple[bytes, str]:
    boundary = "----cos-elevenlabs-boundary"
    body = bytearray()

    for name, value, filename in parts:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        if filename:
            body.extend(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8")
            )
            body.extend(b"Content-Type: application/octet-stream\r\n\r\n")
            body.extend(value if isinstance(value, bytes) else value.encode("utf-8"))
            body.extend(b"\r\n")
            continue

        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(value if isinstance(value, bytes) else value.encode("utf-8"))
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), boundary


@router.post("/elevenlabs")
def synthesize_with_elevenlabs(payload: ElevenLabsTtsRequest) -> Response:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise HTTPException(status_code=503, detail="ElevenLabs API key is not configured.")

    voice_id = payload.voice_id or settings.elevenlabs_voice_id
    model_id = payload.model_id or settings.elevenlabs_model_id
    tts_text = payload.text.strip() or FALLBACK_TTS_TEXT
    endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    body = json.dumps(
        {
            "text": tts_text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.8,
            },
        }
    ).encode("utf-8")

    outgoing = request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
            "xi-api-key": settings.elevenlabs_api_key,
        },
        method="POST",
    )

    try:
        with request.urlopen(outgoing, timeout=20) as upstream:
            audio_bytes = upstream.read()
            content_type = upstream.headers.get("Content-Type", "audio/mpeg")
    except error.HTTPError as exc:
        upstream_detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(
            status_code=502,
            detail=f"ElevenLabs request failed with status {exc.code}: {upstream_detail}",
        ) from exc
    except error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach ElevenLabs: {exc.reason}") from exc

    return Response(
        content=audio_bytes,
        media_type=content_type,
        headers={"X-TTS-Input-Length": str(len(tts_text))},
    )


@router.post("/elevenlabs/transcribe")
async def transcribe_with_elevenlabs(file: UploadFile = File(...)) -> dict[str, str]:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise HTTPException(status_code=503, detail="ElevenLabs API key is not configured.")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    filename = file.filename or "recording.webm"
    multipart_body, boundary = _multipart_form_data(
        [
            ("model_id", settings.elevenlabs_stt_model_id, None),
            ("file", audio_bytes, filename),
        ]
    )

    outgoing = request.Request(
        "https://api.elevenlabs.io/v1/speech-to-text",
        data=multipart_body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "xi-api-key": settings.elevenlabs_api_key,
        },
        method="POST",
    )

    try:
        with request.urlopen(outgoing, timeout=30) as upstream:
            payload = json.loads(upstream.read().decode("utf-8"))
    except error.HTTPError as exc:
        upstream_detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(
            status_code=502,
            detail=f"ElevenLabs STT request failed with status {exc.code}: {upstream_detail}",
        ) from exc
    except error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach ElevenLabs: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="ElevenLabs STT returned invalid JSON.") from exc

    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=502, detail="ElevenLabs STT did not return transcript text.")
    return {"text": text}
