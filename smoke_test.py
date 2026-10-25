"""Verify the Gemini API key works and that it has access to Gemini 4 Argon.

Run:  uv run smoke_test.py
"""
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    sys.exit("GEMINI_API_KEY is not set. Copy .env.example to .env and paste your key.")

client = genai.Client()

print("1) Key is valid, listing models that mention 'argon'...")
try:
    names = [m.name for m in client.models.list()]
except errors.APIError as e:
    sys.exit(f"   Key rejected: {e.code} {e.message}")
argon = [n for n in names if "argon" in n]
print("   ", argon or "(no argon model listed, but the call may still work)")

print("2) Calling gemini-4-argon...")
try:
    interaction = client.interactions.create(
        model="gemini-4-argon",
        input="Reply with exactly: ARGON OK",
    )
    print("   ", interaction.output_text.strip())
    print("\nAll good. You are on the Paid tier with Argon access.")
except errors.APIError as e:
    print(f"   FAILED: HTTP {e.code}: {e.message}")
    if e.code in (403, 429):
        print(
            "\n   This usually means the key's project is on the Free tier,\n"
            "   has no prepaid balance, or billing identity verification is pending.\n"
            "   Fix at https://aistudio.google.com/billing and\n"
            "   https://aistudio.google.com/projects (Set up billing)."
        )
    print("\n3) Fallback: trying gemini-3.8-flash (works on Free tier)...")
    fb = client.interactions.create(model="gemini-3.8-flash", input="Reply with exactly: FLASH OK")
    print("   ", fb.output_text.strip())
