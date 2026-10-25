# Argon4 Hackathon

Gemini 4 Argon SF Hackathon (Cerebral Valley x Google DeepMind), 25 Oct 2026.
Submissions due 26 Oct 2026 (UTC). Prizes include "Best use of Managed Agents".

## Stack
- Python 3.12 managed by `uv` (`uv run <script>`, `uv add <pkg>`).
- SDK: `google-genai` >= 2.30 using the **Interactions API** (`client.interactions.create`),
  not the legacy `generate_content`. Legacy `google-generativeai` is banned.
- Primary model: `gemini-4-argon` (1M context, thinking low/medium/high, tools,
  code execution, function calling, structured output). Not on the Free tier.
- Cheap/fast model for iteration: `gemini-3.8-flash`.
- Managed agents: `antigravity-preview-09-2026` via `client.agents`.

## Skills
Gemini skills live in `.agents/skills/` (symlinked to `.claude/skills/`).
Always consult `gemini-api-dev` before writing Gemini API code and fetch the
hosted doc page it points at for the feature in question.

## Secrets
`GEMINI_API_KEY` lives in `.env` (gitignored). Never commit it.
Check access with `uv run smoke_test.py`.
