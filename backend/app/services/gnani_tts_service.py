import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

from app.config import (
    AUDIO_CACHE_DIR,
    BACKEND_DIR,
    GNANI_API_KEY_ID,
    REFERENCE_VOICE_OGG,
    REFERENCE_VOICE_WAV,
)

logger = logging.getLogger("gnani_tts_service")
logger.setLevel(logging.INFO)

GNANI_EMBEDDINGS_URL = "https://api.vachana.ai/api/v1/tts/voice-clone/embeddings"
GNANI_TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"
EMBEDDING_CACHE_PATH = AUDIO_CACHE_DIR / "gnani_speaker_embedding.json"
MAX_REFERENCE_DURATION_SECONDS = 30


class GnaniTTSService:
    def __init__(self) -> None:
        self._embedding: Optional[Dict[str, Any]] = None
        self._cached_embedding_signature: Optional[str] = None
        self._embedding_lock = asyncio.Lock()

    @property
    def api_key_id(self) -> str:
        load_dotenv(dotenv_path=BACKEND_DIR / ".env", override=True)
        return os.getenv("GNANI_API_KEY_ID", GNANI_API_KEY_ID).strip()

    def _reference_audio_path(self) -> Path:
        if REFERENCE_VOICE_WAV.exists():
            return REFERENCE_VOICE_WAV
        if REFERENCE_VOICE_OGG.exists():
            return REFERENCE_VOICE_OGG
        raise FileNotFoundError("Gnani TTS requires a reference voice audio file.")

    @staticmethod
    def _get_reference_signature(path: Path) -> str:
        stat = path.stat()
        return f"{stat.st_size}:{stat.st_mtime_ns}"

    def _read_cached_embedding(self, signature: str) -> Optional[Dict[str, Any]]:
        try:
            cache = json.loads(EMBEDDING_CACHE_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read Gnani speaker-embedding cache: %s", exc)
            return None

        if not isinstance(cache, dict):
            logger.warning("Gnani speaker-embedding cache has an invalid format.")
            return None

        embedding = cache.get("voice_clone_embedding")
        if cache.get("reference_signature") == signature and self._valid_embedding(embedding):
            return embedding
        return None

    @staticmethod
    def _valid_embedding(embedding: Any) -> bool:
        return (
            isinstance(embedding, dict)
            and isinstance(embedding.get("embedding"), str)
            and bool(embedding["embedding"])
            and isinstance(embedding.get("shape"), list)
            and isinstance(embedding.get("dtype"), str)
        )

    async def _generate_embedding(self, api_key_id: str, reference_path: Path) -> Dict[str, Any]:
        import imageio_ffmpeg

        signature = self._get_reference_signature(reference_path)
        cached_embedding = self._read_cached_embedding(signature)
        if cached_embedding:
            return cached_embedding

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        with tempfile.TemporaryDirectory(prefix="gnani-reference-") as temp_dir:
            prepared_path = Path(temp_dir) / "reference.wav"
            command = [
                ffmpeg_path,
                "-y",
                "-i",
                str(reference_path),
                "-t",
                str(MAX_REFERENCE_DURATION_SECONDS),
                "-ar",
                "44100",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(prepared_path),
            ]
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0 or not prepared_path.is_file():
                raise RuntimeError(f"Could not prepare reference audio for Gnani TTS: {result.stderr[-500:]}")

            headers = {"X-API-Key-ID": api_key_id}
            async with httpx.AsyncClient(timeout=90.0) as client:
                with prepared_path.open("rb") as audio_file:
                    response = await client.post(
                        GNANI_EMBEDDINGS_URL,
                        headers=headers,
                        files={"audio_file": ("reference.wav", audio_file, "audio/wav")},
                    )

        if response.status_code != 200:
            raise RuntimeError(
                f"Gnani voice embedding request failed ({response.status_code}): {response.text[:500]}"
            )

        response_data = response.json()
        embedding = response_data.get("data", {}).get("voice_clone_embedding")
        if not self._valid_embedding(embedding):
            raise RuntimeError("Gnani returned an invalid voice-clone embedding.")

        EMBEDDING_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cache_payload = {
            "reference_signature": signature,
            "voice_clone_embedding": embedding,
        }
        EMBEDDING_CACHE_PATH.write_text(
            json.dumps(cache_payload),
            encoding="utf-8",
        )
        logger.info("Cached Gnani voice embedding for the reference recording.")
        return embedding

    async def _get_embedding(self, api_key_id: str, reference_path: Path) -> Dict[str, Any]:
        signature = self._get_reference_signature(reference_path)
        if self._embedding and self._cached_embedding_signature == signature:
            return self._embedding

        async with self._embedding_lock:
            if self._embedding and self._cached_embedding_signature == signature:
                return self._embedding

            embedding = self._read_cached_embedding(signature)
            if embedding is None:
                embedding = await self._generate_embedding(api_key_id, reference_path)

            self._embedding = embedding
            self._cached_embedding_signature = signature
            return embedding

    async def text_to_speech(self, text: str) -> Optional[bytes]:
        api_key_id = self.api_key_id
        if not api_key_id:
            logger.warning("GNANI_API_KEY_ID is not configured; using the configured TTS fallback.")
            return None

        try:
            reference_path = self._reference_audio_path()
            embedding = await self._get_embedding(api_key_id, reference_path)
            payload = {
                "text": text,
                "model": "vachana-vc-v1",
                "audio_config": {
                    "sample_rate": 44100,
                    "num_channels": 1,
                    "sample_width": 2,
                    "encoding": "linear_pcm",
                    "container": "wav",
                },
                "speaker_embedding": embedding,
            }

            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    GNANI_TTS_URL,
                    headers={
                        "X-API-Key-ID": api_key_id,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

            if response.status_code != 200:
                logger.warning(
                    "Gnani TTS request failed (%s): %s",
                    response.status_code,
                    response.text[:500],
                )
                return None
            if len(response.content) <= 1000:
                logger.warning("Gnani TTS returned an empty or incomplete audio response.")
                return None

            logger.info("Gnani voice-cloned TTS synthesized audio successfully.")
            return response.content
        except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
            logger.error("Gnani TTS request failed: %s", exc)
            return None


gnani_tts_service = GnaniTTSService()
