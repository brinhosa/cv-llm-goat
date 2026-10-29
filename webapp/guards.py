"""NeMo Guardrails input rails in front of the grader (BSides Lisbon research).

  nemo      NeMo self-check input rail (LLM judge, DeepSeek)
  nemo_jev  NeMo rail: TypeSafe Jev first; confident -> decide, uncertain -> LLM self-check
"""
from __future__ import annotations

import os
import pathlib
import time

import jev_client

RAILS_DIR = pathlib.Path(__file__).resolve().parent / "rails"
CONFIGS = {"nemo": "selfcheck", "nemo_jev": "cascade"}
_rails: dict = {}


def _get(mode):
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("Tabs C/D need DEEPSEEK_API_KEY (NeMo self-check LLM). See .env.example.")
    if mode == "nemo_jev" and not jev_client._key():
        raise RuntimeError("Tab D needs TYPESAFE_API_KEY (Jev). See .env.example.")
    os.environ.setdefault("OPENAI_API_KEY", os.environ["DEEPSEEK_API_KEY"])
    if mode not in _rails:
        from nemoguardrails import LLMRails, RailsConfig
        _rails[mode] = LLMRails(RailsConfig.from_path(str(RAILS_DIR / CONFIGS[mode])))
    return _rails[mode]


async def check(text: str, mode: str) -> dict:
    rails = _get(mode)
    n0 = len(jev_client.CALLS)
    t0 = time.perf_counter()
    res = await rails.generate_async(messages=[{"role": "user", "content": text}],
                                     options={"rails": ["input"], "log": {"activated_rails": True}})
    ms = (time.perf_counter() - t0) * 1000
    acts = res.log.activated_rails or []
    decisions = [d for a in acts for d in a.decisions]
    jev = jev_client.CALLS[n0:]
    del jev_client.CALLS[:]
    return {
        "blocked": any(a.stop for a in acts),
        "ms": round(ms, 1),
        "llm_judge_used": any(d in decisions for d in ("execute self_check_input", "execute llm_self_check_blocked")),
        "jev": jev[-1] if jev else None,
        "rail": CONFIGS[mode],
    }
