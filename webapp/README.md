# AI Resume Grader — BSides Porto Demo

Live, audience-facing demo of **indirect prompt injection** (OWASP **LLM01**) in an
AI resume grader, plus the **hardened** version that defeats it.

- **Page A — Vulnerable:** resume text is dumped straight into the LLM prompt. A CV
  with a hidden payload hijacks the grader → bad CV gets `10/10` / "Advance".
- **Page B — Hardened:** sanitization + injection detection + prompt envelope
  (untrusted-data delimiters) + strict output validation → same CV gets its real
  grade and the injection is flagged.

## Run

```bash
cd cv_injection_lab/webapp
pip install -r requirements.txt

# real LLM (DeepSeek v4 flash, OpenAI-compatible) — optional:
export DEEPSEEK_API_KEY=sk-...
# export DEEPSEEK_MODEL=deepseek-chat   # override if needed

uvicorn app:app --reload --port 8090
```

Open <http://localhost:8090>. No key? Use the **mock** engine (offline, deterministic,
stage-safe) — same attack/defense behavior without network.

## Stage script

1. **Page A**, engine `mock` (or `real`), default clean CV → *Grade* → ~6/10 "Hold".
2. Pick a payload (e.g. `direct_override`) → **💉 Inject (hidden)** (wraps it in
   zero-width chars, like a real attacker) → *Grade* → **10/10, hijack banner**.
3. Show the **"Exact prompt sent"** panel: resume content sits where instructions go.
4. Switch to **Page B** → *Grade* same text → injection flagged, score restored,
   output validated. Show the prompt envelope (`<resume_data>…</resume_data>`).
5. Optional: upload a weaponized PDF from `../output/resume_layer*.pdf`.

## Controls → OWASP mapping

| Control (`defenses.py`)      | Mitigates |
|------------------------------|-----------|
| `sanitize()` zero-width strip | hidden-text smuggling / input validation |
| `detect_injection()`          | LLM01 (defense-in-depth detection) |
| `build_enveloped_prompt()`    | LLM01 (structural: untrusted-data framing) |
| `validate_output()`           | LLM05 Improper Output Handling |

Heuristic detection alone is not enough — the **prompt envelope + output validation**
are the structural controls; the detector just makes the attack visible on stage.

## Files

- `app.py` — FastAPI routes (`/`, `/api/seed`, `/api/grade`).
- `grader.py` — vulnerable vs. fixed flows; real (DeepSeek) + mock engines.
- `defenses.py` — the Page B controls.
- `extract.py` — `.txt` / `.pdf` text extraction (incl. hidden layers).
- `static/index.html` — single-page UI (tabs A/B).

Reuses payloads + fictional candidate from `../payloads.py`. Fictional data only — no
real PII. Educational use.

## Built-in guardrails

These bound resource use; they do NOT make the grader safe (the vulnerable page is
injectable on purpose):

| Control | Where | Detail |
|---|---|---|
| Upload cap | `app.py` `MAX_UPLOAD` | 1 MB → 413 |
| Text cap | `app.py` `MAX_CHARS` | 20 000 chars, truncates, `truncated` flag |
| Output XSS | `static/app.js` `esc()` | escapes untrusted LLM `recommendation` |

> ⚠️ **Intentionally vulnerable — do not deploy on a public/untrusted network.**
> Run it locally for learning. See the root `README.md` for the full GOAT writeup.
