import os
import logging
import torch
from pathlib import Path
from typing import Dict, Any, Optional

from app.config import RECORDINGS_DIR
from app.services.voice_service import voice_service
from app.services.elevenlabs_service import standardize_and_pad_audio, isolate_noise_ffmpeg

logger = logging.getLogger("verification_service")
logger.setLevel(logging.INFO)

SIMILARITY_MATCH_THRESHOLD = 0.68  # OpenVoice neural speaker embedding cosine similarity threshold

class VoiceVerificationService:
    def __init__(self):
        pass

    def register_baseline_voice(self, assessment_id: str, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Saves candidate's Terms & Conditions declaration audio and extracts
        their biometric speaker embedding (baseline) for proctoring verification.
        """
        try:
            # Standardize audio to PCM WAV format
            clean_bytes = isolate_noise_ffmpeg(audio_bytes)
            padded_bytes = standardize_and_pad_audio(clean_bytes if len(clean_bytes) > 1000 else audio_bytes, target_duration_sec=4.0)

            baseline_filename = f"baseline_{assessment_id}.wav"
            baseline_path = RECORDINGS_DIR / baseline_filename
            with open(baseline_path, "wb") as f:
                f.write(padded_bytes)

            se_filename = f"baseline_{assessment_id}.pth"
            se_path = RECORDINGS_DIR / se_filename

            # Extract speaker embedding using loaded OpenVoice converter
            if voice_service.is_ready and voice_service.converter:
                embedding = voice_service.converter.extract_se([str(baseline_path)], se_save_path=str(se_path))
                logger.info(f"Successfully registered baseline voice embedding for assessment {assessment_id}")
                return {
                    "success": True,
                    "baseline_audio_filename": baseline_filename,
                    "baseline_audio_url": f"/api/audio/recording/{baseline_filename}",
                    "embedding_saved": se_path.exists(),
                    "message": "Candidate Terms & Conditions baseline voice registered successfully."
                }
            else:
                logger.warning(f"Voice converter not ready, saved baseline audio only for assessment {assessment_id}")
                return {
                    "success": True,
                    "baseline_audio_filename": baseline_filename,
                    "baseline_audio_url": f"/api/audio/recording/{baseline_filename}",
                    "embedding_saved": False,
                    "message": "Candidate baseline audio saved."
                }
        except Exception as e:
            logger.error(f"Error registering baseline voice for {assessment_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "baseline_audio_filename": "",
                "baseline_audio_url": ""
            }

    def verify_speaker(self, assessment_id: str, answer_audio_path: Path, threshold: float = SIMILARITY_MATCH_THRESHOLD) -> Dict[str, Any]:
        """
        Compares the speaker embedding of an assessment answer against the candidate's
        Terms & Conditions baseline voice embedding.
        Returns match boolean, cosine similarity percentage, and human-readable audit text.
        """
        se_path = RECORDINGS_DIR / f"baseline_{assessment_id}.pth"
        baseline_wav = RECORDINGS_DIR / f"baseline_{assessment_id}.wav"

        # If baseline embedding doesn't exist, try extracting from baseline_wav if present
        baseline_se = None
        device = "cpu"
        if se_path.exists():
            try:
                baseline_se = torch.load(str(se_path), map_location=device)
            except Exception as e:
                logger.warning(f"Failed to load cached baseline embedding: {e}")

        if baseline_se is None and baseline_wav.exists() and voice_service.converter:
            try:
                baseline_se = voice_service.converter.extract_se([str(baseline_wav)], se_save_path=str(se_path))
            except Exception as e:
                logger.warning(f"Failed to extract baseline SE on-the-fly: {e}")

        if baseline_se is None:
            logger.warning(f"No baseline voice found for assessment {assessment_id}. Skipping biometric match.")
            return {
                "matched": True,
                "similarity_score": 100.0,
                "status": "unverified",
                "message": "Baseline voice verification bypassed (no baseline sample recorded)"
            }

        if not answer_audio_path.exists() or answer_audio_path.stat().st_size < 1000:
            return {
                "matched": False,
                "similarity_score": 0.0,
                "status": "no_audio",
                "message": "Voice Not Matched: No audible speech detected in answer"
            }

        try:
            # Standardize answer audio (MP3/WebM/WAV) to standard PCM WAV with duration padding
            with open(answer_audio_path, "rb") as f_ans:
                raw_bytes = f_ans.read()
            std_bytes = standardize_and_pad_audio(raw_bytes, target_duration_sec=4.0)

            temp_std_path = RECORDINGS_DIR / f"temp_verify_{assessment_id}.wav"
            with open(temp_std_path, "wb") as f_tmp:
                f_tmp.write(std_bytes if len(std_bytes) > 1000 else raw_bytes)

            try:
                # Extract speaker embedding of the standardized answer audio
                answer_se = voice_service.converter.extract_se([str(temp_std_path)])
            finally:
                if temp_std_path.exists():
                    try:
                        os.remove(temp_std_path)
                    except Exception:
                        pass

            if answer_se is None:
                return {
                    "matched": False,
                    "similarity_score": 0.0,
                    "status": "extraction_failed",
                    "message": "Voice Not Matched: Could not extract voice characteristics"
                }

            # Compute cosine similarity between baseline and answer speaker embeddings
            similarity = torch.nn.functional.cosine_similarity(
                baseline_se.flatten().unsqueeze(0),
                answer_se.flatten().unsqueeze(0)
            ).item()

            score_pct = round(max(0.0, min(1.0, similarity)) * 100.0, 1)
            is_matched = bool(similarity >= threshold)

            logger.info(f"Assessment {assessment_id} speaker verification: score={score_pct}%, matched={is_matched}")

            return {
                "matched": is_matched,
                "similarity_score": score_pct,
                "threshold": round(threshold * 100.0, 1),
                "status": "matched" if is_matched else "not_matched",
                "message": (
                    f"Voice Verified (Identity Match: {score_pct}%)"
                    if is_matched
                    else f"Voice Not Matched: Candidate voice does not match Terms & Conditions voice ({score_pct}% vs {int(threshold * 100)}% required)"
                )
            }
        except Exception as e:
            logger.error(f"Error comparing speaker embeddings for {assessment_id}: {e}")
            return {
                "matched": False,
                "similarity_score": 0.0,
                "status": "error",
                "message": f"Voice verification notice: {str(e)}"
            }

verification_service = VoiceVerificationService()
