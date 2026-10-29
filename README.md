# CV LLM GOAT — Vulnerable AI Resume Grader

> ⚠️ **Intentionally vulnerable, by design.** This is a teaching target (a "GOAT",
> like OWASP WebGoat) for **LLM prompt injection**. Run it **locally only**. Do not
> deploy it on a public or untrusted network. Educational / authorized use only.

A live, audience-facing demo of **indirect prompt injection** — OWASP **LLM01** — in
an AI résumé grader, plus the **hardened** version that defeats it.

## Talk

**Reading Between the Lines: Exploiting Indirect Injection in AI Systems**
Michael Reimsbach & Rafael B. Brinhosa — BSides Porto • 15:30 – 16:20, follow-up at BSides Lisbon

We've moved past the era of users manually bypassing chatbot filters with *"Ignore
previous instructions."* and entered a more dangerous era: **indirect injection**.

The 2025 **EchoLeak** exploit first proved that a single unread email could trigger
Microsoft Copilot to silently exfiltrate private data without a single user click.
This was followed by the 2026 **Claude Code hijacks**, which demonstrated that a
poisoned `.CLAUDE.md` file in a repository could allow an attacker to execute
arbitrary shell commands and harvest sensitive environment variables.

The fundamental lack of a security boundary between *data* and *instructions* causes
LLMs to treat every input as a potential command — transforming seemingly benign
files such as a CV or a RAG chunk into an injection vector that can force the model to
ignore its safety boundaries.

This session deconstructs real-world injection attacks and the obfuscation techniques
that make them effective: hidden metadata, Unicode steganography, and homoglyph
substitution tunnelling malicious instructions through "invisible" channels. We
conclude with a hardened design pattern for resilient LLMs — so your agents can
process untrusted data without compromising their internal logic.

This repo is the live demo for that talk.

A candidate uploads a résumé. An LLM scores it 1–10 and recommends Advance / Hold /
Reject. The résumé hides instructions a human reviewer never sees — but the model does.

- **Page A — Vulnerable:** résumé text is dumped straight into the LLM prompt. A CV
  with a hidden payload hijacks the grader → a mediocre CV gets `10/10` / "Advance".
- **Page B — Hardened:** sanitization + injection detection + prompt envelope
  (untrusted-data delimiters) + strict output validation → the same CV gets its real
  grade and the injection is flagged.

## What it teaches

| Control (`webapp/defenses.py`) | Mitigates |
|---|---|
| `sanitize()` (strips zero-width / invisible chars) | hidden-text smuggling / input validation |
| `detect_injection()` | LLM01 — defense-in-depth detection |
| `build_enveloped_prompt()` | LLM01 — structural: untrusted-data framing |
| `validate_output()` | LLM05 — Improper Output Handling (schema/range) |

Heuristic detection alone is not enough — the **prompt envelope + output validation**
are the structural controls; the detector just makes the attack visible on stage.

## Run it

### Option A — Python

```bash
cd webapp
pip install -r requirements.txt
uvicorn app:app --reload --port 8090
```

Open <http://localhost:8090>.

### Option B — Docker

```bash
docker compose up --build      # -> http://localhost:8090
```

No API key needed: the default **mock** engine is offline, deterministic and
stage-safe (it reproduces the same hijack/defense behavior without any network call).

### Optional: real LLM

To grade with a real model (DeepSeek, OpenAI-compatible), bring **your own** key:

```bash
cp .env.example .env
# edit .env and set DEEPSEEK_API_KEY=sk-...
```

No key is shipped with this repo. Without `.env`, everything runs on the mock engine.

## Live demo script

1. **Page A**, engine `mock` → default clean CV → *Grade* → ~6/10 "Hold".
2. Pick a payload (e.g. `direct_override`) → **💉 Inject (hidden)** (wraps it in
   zero-width chars, like a real attacker) → *Grade* → **10/10, hijack banner**.
3. Show the **"Exact prompt sent"** panel: résumé content lands where instructions go.
4. Switch to **Page B** → *Grade* the same text → injection flagged, score restored,
   output validated. Show the prompt envelope (`<resume_data>…</resume_data>`).
5. Optional: upload a weaponized PDF from `output/` (white text, metadata, micro-font,
   hidden annotation, zero-width chars, combined).

## Tests

Offline smoke tests (mock engine — no network, no API key) cover the core
claims: the vulnerable grader is hijacked, the hardened grader resists, the
defenses primitives behave, and the API + PDF extraction work end to end.

```bash
pip install pytest httpx
pytest -q
```

## Weaponized sample PDFs

`output/` ships a clean control résumé plus six injection variants. Regenerate them:

```bash
pip install pymupdf
python create_fictional_resume.py     # clean résumé
python weaponize_resume.py            # 6 hidden-injection layers
```

All résumé data is **fictional** ("Alex Morgan") — no real person, no real PII.

## BSides Lisbon follow-up: NeMo Guardrails + Jev

Tabs **C** and **D** put an NVIDIA NeMo Guardrails input rail in front of the naive grader:

* **C · NeMo (LLM):** NeMo's `self check input` rail, DeepSeek as the judge.
* **D · NeMo + Jev → LLM:** a NeMo rail backed by TypeSafe Jev (System One). Jev decides when it is
  confident; unsure cases go to the LLM judge.

Both need keys in `.env` (`DEEPSEEK_API_KEY`, and `TYPESAFE_API_KEY` for D). Without them, the tabs
return a clear error and tabs A/B keep working offline.

The benchmark behind the talk (detection quality, latency, and an adaptive LLM attacker) is in
[`nemo_lab/`](nemo_lab/), with the write-up in [`nemo_lab/REPORT.md`](nemo_lab/REPORT.md). Headline on
our synthetic corpus: Jev inside NeMo matched the LLM judge's detection at about 5x lower median latency,
and the Jev → LLM cascade removed Jev's false positives while sending only 8% of resumes to the LLM.

## Layout

```
webapp/            FastAPI app + single-page UI (tabs A/B/C/D)
  app.py           routes: /, /api/seed, /api/grade
  grader.py        vulnerable vs. fixed flows; real (DeepSeek) + mock engines
  defenses.py      the Page B controls
  extract.py       .txt / .pdf text extraction (incl. hidden layers)
  static/          index.html + app.js
  guards.py        NeMo Guardrails input rails for tabs C/D
  jev_client.py    TypeSafe Jev client
  rails/           NeMo configs (selfcheck, cascade)
nemo_lab/          BSides Lisbon benchmark: NeMo vs NeMo + Jev (REPORT.md)
payloads.py        injection payload library + fictional candidate
create_fictional_resume.py / weaponize_resume.py   PDF tooling
test_with_cli.py / test_with_llm.py                test harnesses
output/            sample clean + weaponized PDFs
```

## License

MIT, with an educational-use notice — see [LICENSE](LICENSE). Intentionally
vulnerable; use responsibly and only against systems you are authorized to test.

## Authors

Michael Reimsbach & Rafael B. Brinhosa — BSides Porto and BSides Lisbon.
