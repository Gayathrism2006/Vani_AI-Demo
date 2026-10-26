import os
import sys
import shutil
import asyncio
import hashlib
import logging
import threading
from pathlib import Path
import torch
import soundfile as sf
import edge_tts

from app.config import (
    REFERENCE_VOICE_WAV,
    REFERENCE_VOICE_OGG,
    REFERENCE_SE_PATH,
    CONVERTER_CONFIG,
    CONVERTER_CKPT,
    AUDIO_CACHE_DIR,
    EDGE_TTS_VOICES
)

logger = logging.getLogger("voice_service")
logger.setLevel(logging.INFO)

class VoiceCloningService:
    def __init__(self):
        self.converter = None
        self.reference_se = None
        self.is_ready = False
        self._conversion_lock = threading.Lock()
        self._active_tasks = {}
        self._init_models()

    def _init_models(self):
        try:
            # Ensure ffmpeg in PATH for pydub/openvoice
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
            ffmpeg_dir = os.path.dirname(ffmpeg_bin)
            if ffmpeg_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

            # Check if converter checkpoints exist
            if not CONVERTER_CONFIG.exists() or not CONVERTER_CKPT.exists():
                logger.warning("Converter checkpoints not found. Voice cloning might require downloading.")
                return

            from openvoice_cli.api import ToneColorConverter
            device = "cpu"
            self.converter = ToneColorConverter(str(CONVERTER_CONFIG), device=device)
            self.converter.load_ckpt(str(CONVERTER_CKPT))
            logger.info("ToneColorConverter successfully initialized on CPU.")

            # Load or extract reference speaker embedding
            if REFERENCE_SE_PATH.exists():
                self.reference_se = torch.load(str(REFERENCE_SE_PATH), map_location=device)
                logger.info("Loaded cached reference speaker embedding.")
            elif REFERENCE_VOICE_WAV.exists():
                logger.info("Extracting reference speaker embedding from reference_voice.wav...")
                self.reference_se = self.converter.extract_se([str(REFERENCE_VOICE_WAV)], se_save_path=str(REFERENCE_SE_PATH))
                logger.info("Saved extracted reference speaker embedding.")
            
            if self.reference_se is not None:
                self.is_ready = True
                logger.info("VoiceCloningService is READY with user reference voice!")
        except Exception as e:
            logger.error(f"Error initializing VoiceCloningService: {e}")
            self.is_ready = False

    def _convert_tone_sync(self, temp_base_path: str, output_path: str) -> bool:
        """
        Runs ToneColorConverter synchronously with a thread lock to prevent
        CPU thrashing and file access race conditions on Windows.
        """
        with self._conversion_lock:
            try:
                # Extract source speaker embedding from the generated base audio
                source_se = self.converter.extract_se([temp_base_path])
                # Convert tone color to user reference voice
                self.converter.convert(
                    audio_src_path=temp_base_path,
                    src_se=source_se,
                    tgt_se=self.reference_se,
                    output_path=output_path
                )
                return True
            except Exception as e:
                logger.warning(f"ToneColorConverter error: {e}")
                return False

    async def generate_speech(self, text: str, language: str, assessment_id: str = "gen", question_index: int = 1) -> dict:
        """
        Generates speech with Gnani voice-cloned TTS, with Edge-TTS and OpenVoice fallback.
        Deduplicates in-flight tasks and checks global cache.
        """
        reference_voice_path = (
            REFERENCE_VOICE_WAV if REFERENCE_VOICE_WAV.exists() else REFERENCE_VOICE_OGG
        )
        if reference_voice_path.exists():
            reference_stat = reference_voice_path.stat()
            reference_signature = f"{reference_stat.st_size}_{reference_stat.st_mtime_ns}"
        else:
            reference_signature = "no-reference"
        text_hash = hashlib.md5(
            f"gnani_vachana_vc_v1_{reference_signature}_{text.strip()}_{language}".encode("utf-8")
        ).hexdigest()[:10]
        final_filename = f"gnani_{language.lower()}_{text_hash}.wav"
        final_path = AUDIO_CACHE_DIR / final_filename

        # Fast path 1: Check canonical cached cloned file
        if final_path.exists() and final_path.stat().st_size > 1000:
            return {
                "filename": final_filename,
                "path": str(final_path),
                "is_cloned": True,
                "cached": True,
                "tts_provider": "Gnani AI Vachana VC",
            }

        # Fast path 2: Check any existing cached file with the same text hash from previous runs
        matching = list(AUDIO_CACHE_DIR.glob(f"*_{text_hash}.wav"))
        for candidate in matching:
            if candidate.exists() and candidate.stat().st_size > 1000:
                provider = (
                    "Gnani AI Vachana VC"
                    if candidate.name.startswith("gnani_")
                    else "Edge-TTS with OpenVoice"
                )
                logger.info("Re-used cached voice audio for hash %s from %s", text_hash, candidate.name)
                return {
                    "filename": candidate.name,
                    "path": str(candidate),
                    "is_cloned": True,
                    "cached": True,
                    "tts_provider": provider,
                }

        # Deduplication: If a generation task is already in-flight for this text, wait for it
        task_key = f"{language.lower()}_{text_hash}"
        if task_key in self._active_tasks:
            logger.info(f"Awaiting in-flight audio generation for {task_key}...")
            return await self._active_tasks[task_key]

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._active_tasks[task_key] = future

        try:
            result = await self._do_generate_speech(text, language, assessment_id, question_index, text_hash, final_path, final_filename)
            future.set_result(result)
            return result
        except Exception as ex:
            future.set_exception(ex)
            raise
        finally:
            self._active_tasks.pop(task_key, None)

    async def _do_generate_speech(
        self,
        text: str,
        language: str,
        assessment_id: str,
        question_index: int,
        text_hash: str,
        final_path: Path,
        final_filename: str
    ) -> dict:
        # Try Gnani AI's voice-cloned TTS first.
        try:
            from app.services.gnani_tts_service import gnani_tts_service
            gnani_audio = await gnani_tts_service.text_to_speech(text)
            if gnani_audio and len(gnani_audio) > 1000:
                final_path.parent.mkdir(parents=True, exist_ok=True)
                final_path.write_bytes(gnani_audio)
                logger.info("Gnani AI voice-cloned TTS succeeded: %s", final_filename)
                return {
                    "filename": final_filename,
                    "path": str(final_path),
                    "is_cloned": True,
                    "cached": False,
                    "tts_provider": "Gnani AI Vachana VC",
                }
        except Exception as e:
            logger.warning("Gnani TTS attempt failed; using Edge-TTS fallback: %s", e)

        # Select base voice
        voice = EDGE_TTS_VOICES.get(language, "en-IN-NeerjaNeural")

        temp_base_filename = f"temp_base_{text_hash}.mp3"
        temp_base_path = AUDIO_CACHE_DIR / temp_base_filename

        # Step 1: Generate base neural TTS audio
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(temp_base_path))
        except Exception as e:
            logger.error(f"Edge-TTS generation failed: {e}")
            raise RuntimeError(f"Base TTS failed: {str(e)}")

        # Step 2: Clone voice using OpenVoice ToneColorConverter
        is_cloned = False
        openvoice_filename = f"openvoice_{language.lower()}_{text_hash}.wav"
        openvoice_path = AUDIO_CACHE_DIR / openvoice_filename
        if self.is_ready and self.converter and self.reference_se is not None:
            # Run in worker thread to prevent event loop blocking
            success = await asyncio.to_thread(self._convert_tone_sync, str(temp_base_path), str(openvoice_path))
            if success and openvoice_path.exists() and openvoice_path.stat().st_size > 1000:
                is_cloned = True
                final_filename = openvoice_filename
                final_path = openvoice_path
                logger.info(f"OpenVoice successfully cloned question audio: {final_filename}")

        # If voice cloning failed or wasn't ready, use base audio as final
        if not is_cloned:
            fallback_filename = f"base_{language.lower()}_{text_hash}.mp3"
            fallback_path = AUDIO_CACHE_DIR / fallback_filename
            if temp_base_path.exists():
                shutil.copyfile(temp_base_path, fallback_path)
            final_filename = fallback_filename
            final_path = fallback_path

        # Cleanup temporary base file
        if is_cloned and temp_base_path.exists():
            try:
                temp_base_path.unlink()
            except Exception:
                pass

        return {
            "filename": final_filename,
            "path": str(final_path),
            "is_cloned": is_cloned,
            "cached": False,
            "tts_provider": "Edge-TTS with OpenVoice" if is_cloned else "Edge-TTS",
        }

# Global singleton
voice_service = VoiceCloningService()
