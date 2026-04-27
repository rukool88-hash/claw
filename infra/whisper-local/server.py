"""
Local faster-whisper FastAPI service.

Endpoints:
- POST /transcribe   { "path": "/vault/inbox/audio/xxx.m4a", "language": "zh" } -> JSON
- POST /transcribe-upload (multipart audio file)            -> JSON
- GET  /health

Run:
    uvicorn server:app --host 0.0.0.0 --port 9000
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from faster_whisper import WhisperModel

MODEL_NAME = os.getenv("WHISPER_MODEL", "large-v3")
DEVICE = os.getenv("WHISPER_DEVICE", "auto")  # "cuda" | "cpu" | "auto"
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8_float16")
# 当 n8n 容器传入容器内路径 /vault/... 时，宿主机映射到这里
VAULT_HOST_ROOT = Path(os.getenv("VAULT_HOST_ROOT", r"D:\VScode\机器人"))


def _resolve_device() -> str:
    if DEVICE != "auto":
        return DEVICE
    try:
        import torch  # noqa: F401

        return "cuda" if __import__("torch").cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


_device = _resolve_device()
_compute = COMPUTE_TYPE if _device == "cuda" else "int8"
print(f"[whisper] loading {MODEL_NAME} on {_device} ({_compute})")
model = WhisperModel(MODEL_NAME, device=_device, compute_type=_compute)
print("[whisper] ready")

app = FastAPI(title="brain-vault whisper", version="1.0")


class TranscribeRequest(BaseModel):
    path: str
    language: Optional[str] = None
    vad_filter: bool = True


def _map_vault_path(p: str) -> Path:
    """Translate n8n container path '/vault/...' -> host path."""
    if p.startswith("/vault/"):
        return VAULT_HOST_ROOT / p[len("/vault/") :]
    return Path(p)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "model": MODEL_NAME, "device": _device}


@app.post("/transcribe")
def transcribe(req: TranscribeRequest) -> dict:
    audio = _map_vault_path(req.path)
    if not audio.exists():
        raise HTTPException(404, f"file not found: {audio}")

    segments, info = model.transcribe(
        str(audio),
        language=req.language,
        vad_filter=req.vad_filter,
        beam_size=5,
    )
    seg_list = [
        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for s in segments
    ]
    return {
        "language": info.language,
        "duration": info.duration,
        "text": "\n".join(s["text"] for s in seg_list),
        "segments": seg_list,
    }


@app.post("/transcribe-upload")
async def transcribe_upload(file: UploadFile = File(...), language: Optional[str] = None) -> dict:
    tmp = Path(os.getenv("TEMP", ".")) / f"_wh_{file.filename}"
    tmp.write_bytes(await file.read())
    try:
        return transcribe(TranscribeRequest(path=str(tmp), language=language))
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
