import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import (
    AUDIO_CACHE_DIR,
    RECORDINGS_DIR,
    REFERENCE_VOICE_WAV,
    REFERENCE_VOICE_OGG,
    PROJECT_DIR
)
from app.routers import auth, assessment, system
from app.database import init_db

# Initialize database
init_db()

app = FastAPI(
    title="Vani AI — AI-Powered Voice Assessment Platform",
    description="Backend API for AI-powered scenario question generation, OpenVoice voice cloning, and ElevenLabs speech assessment.",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router)
app.include_router(assessment.router)
app.include_router(system.router)

# Audio endpoints
@app.get("/api/audio/cached/{filename}")
async def get_cached_audio(filename: str):
    file_path = AUDIO_CACHE_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    media_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
    return FileResponse(path=str(file_path), media_type=media_type)

@app.get("/api/audio/recording/{filename}")
async def get_candidate_recording(filename: str):
    file_path = RECORDINGS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Recording not found.")
    if filename.endswith(".webm"):
        media_type = "audio/webm"
    elif filename.endswith(".wav"):
        media_type = "audio/wav"
    elif filename.endswith(".mp3"):
        media_type = "audio/mpeg"
    elif filename.endswith(".ogg"):
        media_type = "audio/ogg"
    else:
        media_type = "audio/mpeg"
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

@app.get("/api/audio/reference")
async def get_reference_voice():
    """Serves the user's uploaded reference voice recording."""
    if REFERENCE_VOICE_WAV.exists():
        return FileResponse(path=str(REFERENCE_VOICE_WAV), media_type="audio/wav")
    elif REFERENCE_VOICE_OGG.exists():
        return FileResponse(path=str(REFERENCE_VOICE_OGG), media_type="audio/ogg")
    else:
        raise HTTPException(status_code=404, detail="Reference voice file not found.")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Vani AI Assessment Engine",
        "openvoice_reference_voice": REFERENCE_VOICE_WAV.exists()
    }

# Serve frontend build static files if present
FRONTEND_DIST = PROJECT_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found.")
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
