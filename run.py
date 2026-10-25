import os
import sys
import subprocess
import uvicorn
from pathlib import Path

# Add backend to sys.path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Ensure imageio_ffmpeg is in PATH
try:
    import imageio_ffmpeg
    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_bin)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 70)
    print("  Vani AI — AI-Powered Voice Assessment Platform")
    print("=" * 70)
    print(f"  Server URL: http://0.0.0.0:{port}")
    print("  Reference voice: Loaded & Cloned with OpenVoice")
    print("  Supported Languages: English & Tamil")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
