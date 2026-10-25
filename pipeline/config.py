"""Single source of truth for model ids and paths."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILDS = ROOT / "builds"
GAMES = ROOT / "games"
RESSOURCES = ROOT / "ressources"
SCHEMA = ROOT / "schema"
PROMPTS = ROOT / "prompts"

ARGON = "gemini-4-argon"
FLASH = "gemini-3.8-flash"
IMAGE = "gemini-nano-banana-2.1"
TTS = "gemini-3.8-flash-tts"
AGENT = "antigravity-preview-09-2026"
AGENT_CONFIG = {"type": "antigravity", "model": ARGON}

NARRATOR_VOICE = "Charon"
API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def playable_dir(build):
    """Folder to serve for a build: the Vite/webpack output if the game has one, else the game root."""
    from pathlib import Path
    g = Path(build) / "game"
    for d in ("dist", "build", "public"):
        if (g / d / "index.html").exists():
            return g / d
    return g
