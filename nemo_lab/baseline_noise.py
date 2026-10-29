"""How often does the naive grader 'hijack' a clean resume by itself? (decision-boundary noise)"""
import json, sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/lab/webapp")
import grader
from dataset import CANDIDATES, resume

N = 6
seeds = [c for c in CANDIDATES if c[0] not in ("Alex Morgan", "Priya Natarajan")]
def g(c):
    res = grader.grade(resume(c), "vulnerable", "real")["result"] or {}
    return c[0], (res.get("score"), res.get("recommendation"))
with ThreadPoolExecutor(6) as ex:
    out = list(ex.map(g, [c for c in seeds for _ in range(N)]))
by = {}
for n, r in out: by.setdefault(n, []).append(r)
summary = {n: dict(Counter(f"{s} {r}" for s, r in v)) for n, v in by.items()}
json.dump(summary, open("results/attack/baseline_noise.json", "w"), indent=2)
print(json.dumps(summary, indent=2))
