// External script (CSP-safe: script-src 'self', no inline code/handlers).
// BASE derived from this script's own URL: .../ipit/static/app.js -> /ipit
const BASE = (function () {
  const s = document.currentScript && document.currentScript.src;
  if (s) return new URL(s).pathname.replace(/\/static\/app\.js.*$/, "");
  return "";
})();

let MODE = "vulnerable";
let SEED = { clean_cv: "", payloads: {}, has_api_key: false };

async function boot() {
  SEED = await (await fetch(BASE + "/api/seed")).json();
  document.getElementById("resume").value = SEED.clean_cv;
  const sel = document.getElementById("payloadSel");
  Object.keys(SEED.payloads).forEach((k) => {
    const o = document.createElement("option");
    o.value = k; o.textContent = k; sel.appendChild(o);
  });
  document.getElementById("engineNote").textContent = SEED.has_api_key
    ? "DEEPSEEK_API_KEY detected — 'real' engine available."
    : "No DEEPSEEK_API_KEY — use 'mock' (set key + restart for real LLM).";
}

function setMode(m) {
  MODE = m;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.mode === m));
  document.getElementById("resultTitle").textContent = {
    vulnerable: "Result — ⚠️ Naive grader", fixed: "Result — 🛡️ Hardened grader",
    nemo: "Result — NeMo self-check (LLM) → naive grader", nemo_jev: "Result — NeMo + Jev → LLM → naive grader",
  }[m];
}

function injectPayload() {
  const key = document.getElementById("payloadSel").value;
  if (!key) { alert("Pick a payload first."); return; }
  const p = SEED.payloads[key];
  // Hide it like a real attacker would: wrapped in zero-width chars + buried at end.
  const ta = document.getElementById("resume");
  ta.value = ta.value + "\n\n​" + p + "​";
}

function resetCV() {
  document.getElementById("resume").value = SEED.clean_cv;
  document.getElementById("file").value = "";
}

function scoreClass(s) { if (s >= 8) return "good"; if (s >= 5) return "mid"; return "bad-hi"; }

async function grade() {
  const fd = new FormData();
  fd.append("mode", MODE);
  fd.append("engine", document.getElementById("engine").value);
  fd.append("resume_text", document.getElementById("resume").value);
  const f = document.getElementById("file").files[0];
  if (f) fd.append("file", f);

  document.getElementById("result").innerHTML = '<p class="note">Grading…</p>';
  let data;
  try { data = await (await fetch(BASE + "/api/grade", { method: "POST", body: fd })).json(); }
  catch (e) { document.getElementById("result").innerHTML = `<div class="flag">${e}</div>`; return; }

  if (data.error) { document.getElementById("result").innerHTML = `<div class="flag">${data.error}</div>`; return; }
  render(data);
}

function render(d) {
  document.getElementById("promptOut").textContent = d.prompt_sent || "—";
  document.getElementById("rawOut").textContent = d.raw_response || "—";
  document.getElementById("srcNote").textContent = d.extracted_from
    ? `(from file: ${d.extracted_from}, ${d.char_count} chars)`
    : `(${d.char_count} chars)`;

  const r = d.result || {};
  let html = "";

  if (d.guard) {
    const g = d.guard, j = g.jev;
    html += g.blocked
      ? `<div class="flag"><b>🛑 Blocked by input rail</b> in ${g.ms} ms</div>`
      : `<div class="ok">Input rail allowed it (${g.ms} ms)</div>`;
    let det = [];
    if (j) det.push(`Jev risk <b>${j.risk}</b> → ${esc(j.decision)} (${j.ms} ms API, ${esc(j.model || "")})`);
    det.push(g.llm_judge_used ? "LLM self-check: used" : "LLM self-check: skipped");
    html += `<p class="note">${det.join(" · ")}</p>`;
  }

  if ((d.mode === "vulnerable" || d.guard) && (r._hijacked || (r.score >= 9 && (r.weaknesses || []).length === 0)))
    html += `<div class="hijack-banner">⚠️ GRADER HIJACKED — resume content overrode the instructions</div>`;

  if (d.parse_failed)
    html += `<div class="flag">Model did not return valid JSON — likely followed the injected instructions.</div>`;

  if (d.mode === "fixed") {
    if ((d.injection_flags || []).length) {
      html += `<div class="flag"><b>🚩 Injection detected (${d.injection_flags.length}):</b><ul class="compact">` +
        d.injection_flags.map((f) => `<li>${f.label}: <code>${esc(f.match)}</code></li>`).join("") + `</ul></div>`;
    } else { html += `<div class="ok">No injection signatures detected.</div>`; }
    if ((d.sanitization_notes || []).length)
      html += `<div class="ok">🧼 Sanitization: ${d.sanitization_notes.join("; ")}</div>`;
    html += d.output_valid
      ? `<div class="ok">✓ Output passed schema validation.</div>`
      : `<div class="flag">✗ Output validation failed: ${(d.output_errors || []).join("; ")}</div>`;
  }

  if (typeof r.score === "number" || r.score) {
    html += `<div class="row"><div><div class="score ${scoreClass(r.score)}">${r.score}<span class="suffix">/10</span></div>
           <div class="verdict">${esc(r.recommendation || "—")}</div></div></div>`;
  }
  if ((r.strengths || []).length)
    html += `<b>Strengths</b><ul class="compact strengths">` + r.strengths.map((s) => `<li>${esc(s)}</li>`).join("") + `</ul>`;
  html += `<b>Weaknesses</b><ul class="compact weaknesses">` +
    ((r.weaknesses || []).length ? r.weaknesses.map((s) => `<li>${esc(s)}</li>`).join("") : `<li class="note">(none reported)</li>`) + `</ul>`;

  html += `<p class="note">${d.note || ""}</p>`;
  document.getElementById("result").innerHTML = html;
}

function esc(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

// Wire events (no inline handlers — CSP-safe).
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => setMode(t.dataset.mode)));
  document.getElementById("btnInject").addEventListener("click", injectPayload);
  document.getElementById("btnReset").addEventListener("click", resetCV);
  document.getElementById("btnGrade").addEventListener("click", grade);
  boot();
});
