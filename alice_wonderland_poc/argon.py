"""Thin wrapper around the Gemini Interactions API for the Argon hackathon.

Usage:
    python argon.py "your prompt"              # quick smoke test (thinking_level=low)
    python argon.py --level high "prompt"      # deeper reasoning
"""
import argparse
import sys
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads GEMINI_API_KEY from .env

ARGON = "gemini-4-argon"
FLASH = "gemini-3.8-flash"
LITE = "gemini-3.5-flash-lite"

# 20-minute timeout: "high" thinking calls can run long
client = genai.Client(http_options={"timeout": 20 * 60 * 1000})


def ask(prompt, model=ARGON, level="medium", max_output_tokens=None, previous=None):
    """One synchronous call. Pass `previous` (an interaction id) to continue a conversation."""
    cfg = {"thinking_level": level}
    if max_output_tokens:
        cfg["max_output_tokens"] = max_output_tokens
    kwargs = {"model": model, "input": prompt, "generation_config": cfg}
    if previous:
        kwargs["previous_interaction_id"] = previous
    return client.interactions.create(**kwargs)


def ask_long(prompt, level="high", max_output_tokens=262144, poll=5):
    """Background call for output beyond 64K tokens, polled until done."""
    it = client.interactions.create(
        model=ARGON,
        input=prompt,
        background=True,
        generation_config={"thinking_level": level, "max_output_tokens": max_output_tokens},
    )
    while it.status in ("in_progress", "queued"):
        time.sleep(poll)
        it = client.interactions.get(id=it.id)
    return it


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("prompt", nargs="?", default="Reply with exactly: Argon is up.")
    p.add_argument("--level", default="low", choices=["low", "medium", "high"])
    p.add_argument("--model", default=ARGON)
    a = p.parse_args()
    t0 = time.time()
    it = ask(a.prompt, model=a.model, level=a.level)
    print(it.output_text)
    print(f"\n[{a.model} · {a.level} · {time.time() - t0:.1f}s · id={it.id}]", file=sys.stderr)
    if getattr(it, "usage", None):
        print(f"[usage: {it.usage}]", file=sys.stderr)
