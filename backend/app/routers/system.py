from fastapi import APIRouter
from app.config import (
    OPENAI_API_KEY,
    ELEVENLABS_API_KEY,
    REFERENCE_VOICE_WAV,
    REFERENCE_SE_PATH,
    CONVERTER_CKPT
)
from app.services.voice_service import voice_service
from app.services.question_service import question_service
from app.services.elevenlabs_service import elevenlabs_service
from app.services.gnani_tts_service import gnani_tts_service

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/status")
def get_system_status():
    """
    Returns full readiness status of all external services and local models:
    - OpenAI GPT-3.5 Turbo availability
    - ElevenLabs Audio Isolation & STT status
    - OpenVoice cloning engine status with user reference voice
    - Reference voice audio file status
    """
    # 1. Check OpenAI
    openai_status = question_service.check_gpt_availability()
    
    # 2. Check ElevenLabs
    elevenlabs_status = elevenlabs_service.check_key_status()
    
    # 3. Check OpenVoice
    ref_voice_exists = REFERENCE_VOICE_WAV.exists()
    voice_cloning_ready = voice_service.is_ready
    openvoice_status = {
        "engine_ready": voice_cloning_ready,
        "reference_voice_present": ref_voice_exists,
        "reference_se_cached": REFERENCE_SE_PATH.exists(),
        "model_checkpoint_present": CONVERTER_CKPT.exists(),
        "message": "OpenVoice voice cloning active using your supplied reference voice!" if voice_cloning_ready else "OpenVoice initializing..."
    }

    return {
        "overall_status": "ready" if (voice_cloning_ready and ref_voice_exists) else "degraded",
        "openai": openai_status,
        "elevenlabs": elevenlabs_status,
        "gnani_tts": {
            "configured": bool(gnani_tts_service.api_key_id),
            "provider": "Gnani AI Vachana VC",
        },
        "openvoice": openvoice_status
    }
