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
        Generates speech using base TTS and applies OpenVoice tone color conversion
        to match the user's supplied reference voice.
        Deduplicates in-flight tasks and checks global cache.
        """
        text_hash = hashlib.md5(f"{text.strip()}_{language}".encode('utf-8')).hexdigest()[:10]
        final_filename = f"cloned_{language.lower()}_{text_hash}.wav"
        final_path = AUDIO_CACHE_DIR / final_filename

        # Fast path 1: Check canonical cached cloned file
        if final_path.exists() and final_path.stat().st_size > 1000:
            return {
                "filename": final_filename,
                "path": str(final_path),
                "is_cloned": True,
                "cached": True
            }

        # Fast path 2: Check any existing cached file with the same text hash from previous runs
        matching = list(AUDIO_CACHE_DIR.glob(f"*_{text_hash}.wav"))
        for candidate in matching:
            if candidate.exists() and candidate.stat().st_size > 1000:
                try:
                    shutil.copyfile(candidate, final_path)
                    logger.info(f"Re-used previously cloned voice for hash {text_hash} -> {final_filename}")
                    return {
                        "filename": final_filename,
                        "path": str(final_path),
                        "is_cloned": True,
                        "cached": True
                    }
                except Exception:
                    return {
                        "filename": candidate.name,
                        "path": str(candidate),
                        "is_cloned": True,
                        "cached": True
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
        # Step 0: Try ElevenLabs Multilingual TTS if configured
        try:
            from app.services.elevenlabs_service import elevenlabs_service
            eleven_audio = await elevenlabs_service.text_to_speech(text=text, language=language)
            if eleven_audio and len(eleven_audio) > 1000:
                eleven_base_filename = f"eleven_base_{text_hash}.mp3"
                eleven_base_path = AUDIO_CACHE_DIR / eleven_base_filename
                with open(eleven_base_path, "wb") as f:
                    f.write(eleven_audio)

                is_cloned = False
                if self.is_ready and self.converter and self.reference_se is not None:
                    success = await asyncio.to_thread(self._convert_tone_sync, str(eleven_base_path), str(final_path))
                    if success and final_path.exists() and final_path.stat().st_size > 1000:
                        is_cloned = True
                        logger.info(f"ElevenLabs TTS + OpenVoice Tone Color Converter succeeded: {final_filename}")

                if is_cloned:
                    try: eleven_base_path.unlink()
                    except Exception: pass
                    return {
                        "filename": final_filename,
                        "path": str(final_path),
                        "is_cloned": True,
                        "cached": False
                    }
                else:
                    return {
                        "filename": eleven_base_filename,
                        "path": str(eleven_base_path),
                        "is_cloned": False,
                        "cached": False
                    }
        except Exception as e:
            logger.warning(f"ElevenLabs TTS attempt: {e}. Falling back to Edge-TTS neural engine.")

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
        if self.is_ready and self.converter and self.reference_se is not None:
            # Run in worker thread to prevent event loop blocking
            success = await asyncio.to_thread(self._convert_tone_sync, str(temp_base_path), str(final_path))
            if success and final_path.exists() and final_path.stat().st_size > 1000:
                is_cloned = True
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
            "cached": False
        }

# Global singleton
voice_service = VoiceCloningService()
