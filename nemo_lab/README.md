# nemo_lab

NeMo Guardrails input rails in front of the BSides Porto resume grader: LLM self-check vs TypeSafe Jev
vs Jev → LLM cascade. Results and method: [REPORT.md](REPORT.md).

* `dataset.py`, `adaptive.py`: build the labeled corpora in `data/`.
* `rails/selfcheck`, `rails/jev`, `rails/cascade`: NeMo configs (Colang 1.0).
* `jev_client.py`: Jev System One client (`POST https://api.typesafe.ai/v1/systemone`).
* `bench.py`: detection, latency and end-to-end attack success. Caches per detector in `results/`.
* `attack.py`, `baseline_noise.py`, `verify_winners.py`: adaptive LLM attacker and its re-grading checks.

Keys: `DEEPSEEK_API_KEY` and `TYPESAFE_API_KEY` in `.env` (gitignored, see `.env.example`), or Jev key as a docker secret at `/run/secrets/TYPESAFE_API_KEY`.
The web app has the same rails as tabs C and D.
