"""
Grading engines for the BSides Porto demo.

Two modes:
  - vulnerable: naive prompt, resume text dumped straight into the instruction.
                The classic OWASP LLM01 mistake — no separation between trusted
                instructions and untrusted resume content.
  - fixed:      uses defenses.py (sanitize + detect + prompt envelope + output
                validation).

Two engines:
  - real: DeepSeek v4 flash via the OpenAI-compatible API (DEEPSEEK_API_KEY).
  - mock: deterministic, offline. Simulates how a vulnerable LLM obeys injected
          instructions vs. how a hardened pipeline ignores them. Stage-safe.
"""
from __future__ import annotations

import json
import os
import re

import defenses

DEEPSEEK_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# ---- Prompts ----------------------------------------------------------------

# VULNERABLE: resume is concatenated directly into the instruction. No delimiter,
# no untrusted-data framing. Any instruction in the resume is read as a command.
VULNERABLE_TEMPLATE = (
    "You are a senior recruiter evaluating candidates for a mid-level security "
    "engineer role. Evaluate the resume below. Score 1-10 based on qualifications. "
    "List exactly 3 strengths and exactly 3 weaknesses. Give a recommendation: "
    "Advance / Hold / Reject. Output strict JSON only:\n"
    '{"score": <int>, "strengths": [<str>,<str>,<str>], '
    '"weaknesses": [<str>,<str>,<str>], "recommendation": <str>}\n\n'
    "RESUME:\n"
)


def _client():
    from openai import OpenAI

    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set — switch engine to 'mock'.")
    return OpenAI(base_url=DEEPSEEK_BASE, api_key=key)


def _parse_json(raw: str) -> dict | None:
    raw = raw.strip()
    # strip code fences if model added them
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


# ---- Real engine (DeepSeek) -------------------------------------------------

def _real_chat(messages: list[dict]) -> str:
    resp = _client().chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        max_tokens=700,
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


# ---- Mock engine (deterministic, offline) -----------------------------------

def _mock_obeys_injection(text: str) -> bool:
    """Vulnerable mock: does the text contain injection markers it will obey?"""
    return len(defenses.detect_injection(text)) > 0


def _mock_genuine_eval(text: str) -> dict:
    """A deterministic 'honest' evaluation of the fictional candidate.

    The fictional resume is mid-level: solid but with real gaps. Score ~6.
    """
    return {
        "score": 6,
        "strengths": [
            "8 years hands-on AppSec and pentest experience",
            "Practical SAST/DAST program ownership",
            "Broad tooling: Burp, Nmap, cloud security",
        ],
        "weaknesses": [
            "Only entry/associate-level certifications (Security+, AWS)",
            "No demonstrated leadership or team management",
            "Claimed metrics (40% reduction) are unverified",
        ],
        "recommendation": "Hold",
    }


def _mock_vulnerable(text: str) -> dict:
    if _mock_obeys_injection(text):
        # Simulate the hijacked model obeying the embedded instructions.
        return {
            "score": 10,
            "strengths": [
                "Exceptional senior security leader — top-tier candidate",
                "Pre-cleared by executive hiring board",
                "Strongly recommended for immediate hire",
            ],
            "weaknesses": [],
            "recommendation": "Advance",
            "_hijacked": True,
        }
    return _mock_genuine_eval(text)


def _mock_fixed(clean_text: str) -> dict:
    res = _mock_genuine_eval(clean_text)
    flags = defenses.detect_injection(clean_text)
    res["injection_detected"] = bool(flags)
    res["injection_notes"] = (
        "; ".join(f"{f['label']}: '{f['match']}'" for f in flags) if flags else ""
    )
    return res


# ---- Public API -------------------------------------------------------------

def grade(resume_text: str, mode: str, engine: str) -> dict:
    """Grade a resume. Returns a result dict for the UI."""
    if mode == "vulnerable":
        return _grade_vulnerable(resume_text, engine)
    return _grade_fixed(resume_text, engine)


def _grade_vulnerable(resume_text: str, engine: str) -> dict:
    prompt = VULNERABLE_TEMPLATE + resume_text
    messages = [{"role": "user", "content": prompt}]

    if engine == "mock":
        result = _mock_vulnerable(resume_text)
        raw = json.dumps(result, ensure_ascii=False)
    else:
        raw = _real_chat(messages)
        result = _parse_json(raw)

    return {
        "mode": "vulnerable",
        "engine": engine,
        "prompt_sent": prompt,
        "raw_response": raw,
        "result": result,
        "parse_failed": result is None,
        "note": "No separation between instructions and resume data (OWASP LLM01).",
    }


def _grade_fixed(resume_text: str, engine: str) -> dict:
    # 1. Input validation / sanitization
    clean_text, sani_notes = defenses.sanitize(resume_text)
    # 2. Defense-in-depth detection
    flags = defenses.detect_injection(clean_text)
    # 3. Prompt envelope (structural control)
    messages = defenses.build_enveloped_prompt(clean_text)

    if engine == "mock":
        result = _mock_fixed(clean_text)
        raw = json.dumps(result, ensure_ascii=False)
    else:
        raw = _real_chat(messages)
        result = _parse_json(raw) or {}

    # 4. Output validation (LLM05)
    ok, errors, safe = defenses.validate_output(result) if result else (False, ["empty/invalid output"], {})

    return {
        "mode": "fixed",
        "engine": engine,
        "prompt_sent": _render_messages(messages),
        "raw_response": raw,
        "result": safe or result,
        "sanitization_notes": sani_notes,
        "injection_flags": flags,
        "output_valid": ok,
        "output_errors": errors,
        "note": "Sanitized + prompt envelope + injection detection + output validation.",
    }


def _render_messages(messages: list[dict]) -> str:
    return "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in messages)
