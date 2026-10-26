import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
GNANI_API_KEY_ID = os.getenv("GNANI_API_KEY_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "vani_ai_secret_key_super_secure_2026")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Directory paths
VOICE_REF_DIR = BACKEND_DIR / "voice_reference"
MODELS_DIR = BACKEND_DIR / "models"
AUDIO_CACHE_DIR = BACKEND_DIR / "cache" / "audio"
RECORDINGS_DIR = BACKEND_DIR / "uploads" / "recordings"

VOICE_REF_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

# Reference voice file paths
REFERENCE_VOICE_WAV = VOICE_REF_DIR / "reference_voice.wav"
REFERENCE_VOICE_OGG = VOICE_REF_DIR / "reference_voice.ogg"
REFERENCE_SE_PATH = VOICE_REF_DIR / "reference_speaker_embedding.pth"

# OpenVoice converter paths
CONVERTER_DIR = MODELS_DIR / "checkpoints_v2" / "converter"
CONVERTER_CONFIG = CONVERTER_DIR / "config.json"
CONVERTER_CKPT = CONVERTER_DIR / "checkpoint.pth"

# Supported options
SUPPORTED_PROGRAMMING_LANGUAGES = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C",
    "C++",
    "C#",
    "SQL",
    "Go",
    "Rust"
]

SUPPORTED_ASSESSMENT_LANGUAGES = [
    "English",
    "Tamil"
]

# Base voice mapping for Edge-TTS
EDGE_TTS_VOICES = {
    "English": "en-IN-NeerjaNeural",     # High-quality Indian English neural female voice
    "Tamil": "ta-IN-PallaviNeural"        # High-quality Tamil neural female voice
}
