"""
BSides Porto 2026 — Vulnerable AI Resume Grader (educational demo).

Run:
  pip install -r requirements.txt
  export DEEPSEEK_API_KEY=...        # optional; omit and use engine=mock
  uvicorn app:app --reload --port 8090

Open http://localhost:8090
"""
from __future__ import annotations

import os
import sys
import pathlib

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import grader
import extract
import guards

# Reuse the payload library + fictional candidate from the parent lab.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
try:
    from payloads import PAYLOADS, FICTIONAL_CANDIDATE  # type: ignore
except Exception:  # pragma: no cover
    PAYLOADS, FICTIONAL_CANDIDATE = {}, {}

HERE = pathlib.Path(__file__).resolve().parent
# Served at root locally (http://localhost:8090). Set BASE_PATH to mount under a
# path prefix (e.g. "/ipit") if you reverse-proxy it without stripping.
BASE = os.environ.get("BASE_PATH", "").rstrip("/")
MAX_UPLOAD = 1_000_000   # 1 MB cap on uploaded files
MAX_CHARS = 20_000       # cap text sent to the LLM (token/cost bound)
app = FastAPI(title="Vulnerable AI Resume Grader — BSides Porto Demo")


def _clean_cv_text() -> str:
    c = FICTIONAL_CANDIDATE
    if not c:
        return "Alex Morgan — Senior Security Engineer\n(sample resume)"
    lines = [c["name"], c["title"], "", c["summary"], "", "EXPERIENCE"]
    for org, role, dates, desc in c["experience"]:
        lines.append(f"- {role}, {org} ({dates}): {desc}")
    lines += ["", "CERTIFICATIONS"] + [f"- {x}" for x in c["certs"]]
    lines += ["", "EDUCATION"] + [f"- {d}, {s} ({y})" for d, s, y in c["education"]]
    lines += ["", "SKILLS"] + [f"- {x}" for x in c["skills"]]
    return "\n".join(lines)


@app.get(BASE or "/", response_class=HTMLResponse)
@app.get(BASE + "/", response_class=HTMLResponse)
def index():
    html = (HERE / "static" / "index.html").read_text(encoding="utf-8")
    return html.replace("__BASE__", BASE)


@app.get(BASE + "/api/seed")
def seed():
    """Provide the default clean CV + payload library to the frontend."""
    return {
        "clean_cv": _clean_cv_text(),
        "payloads": PAYLOADS,
        "has_api_key": bool(os.environ.get("DEEPSEEK_API_KEY")),
    }


@app.post(BASE + "/api/grade")
async def grade(
    mode: str = Form("vulnerable"),
    engine: str = Form("mock"),
    resume_text: str = Form(""),
    file: UploadFile | None = File(None),
):
    text = resume_text or ""
    extracted_from = None
    if file is not None and file.filename:
        data = await file.read()
        if len(data) > MAX_UPLOAD:
            return JSONResponse(
                {"error": f"File too large (>{MAX_UPLOAD // 1000} KB)."}, status_code=413
            )
        text = extract.extract_text(file.filename, data)
        extracted_from = file.filename

    if not text.strip():
        return JSONResponse({"error": "No resume text or file provided."}, status_code=400)

    # Cap text so a huge paste can't blow up token spend / parsing.
    truncated = len(text) > MAX_CHARS
    text = text[:MAX_CHARS]

    if mode not in ("vulnerable", "fixed", "nemo", "nemo_jev"):
        mode = "vulnerable"
    if engine not in ("real", "mock"):
        engine = "mock"

    try:
        guard = None
        if mode in guards.CONFIGS:
            guard = await guards.check(text, mode)
            if guard["blocked"]:
                result = {"mode": mode, "engine": engine, "prompt_sent": "(not sent: blocked by input rail)",
                          "raw_response": "", "result": None,
                          "note": "Blocked by NeMo Guardrails input rail before reaching the grader."}
            else:
                result = grader.grade(text, "vulnerable", engine)
                result["mode"] = mode
                result["note"] = "Input rail allowed it, so it went to the naive grader. The rail is the only defense here."
            result["guard"] = guard
        else:
            result = grader.grade(text, mode, engine)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

    result["extracted_from"] = extracted_from
    result["char_count"] = len(text)
    result["truncated"] = truncated
    return result


app.mount(BASE + "/static", StaticFiles(directory=str(HERE / "static")), name="static")
