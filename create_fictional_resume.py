"""
BSides Porto 2026 — CV Prompt Injection Demo
Step 1: Generate a clean fictional resume PDF (no injection).
"""
import fitz
from pathlib import Path
from payloads import FICTIONAL_CANDIDATE as C

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "resume_CLEAN_control.pdf"

# ── colours & sizes ──────────────────────────────────────────────────────────
DARK   = (0.11, 0.11, 0.18)   # near-black for headings
GOLD   = (0.75, 0.60, 0.20)   # accent
BODY   = (0.20, 0.20, 0.25)   # body text
LINE   = (0.85, 0.85, 0.88)   # divider

W, H   = 595, 842             # A4 points

def rule(page, y, color=LINE, x0=50, x1=545):
    page.draw_line(fitz.Point(x0, y), fitz.Point(x1, y), color=color, width=0.5)

def text(page, x, y, content, size=10, color=BODY, bold=False):
    page.insert_text(fitz.Point(x, y), content, fontsize=size, color=color)

def build_clean_resume():
    doc  = fitz.open()
    page = doc.new_page(width=W, height=H)

    # ── header bar ───────────────────────────────────────────────────────────
    page.draw_rect(fitz.Rect(0, 0, W, 110), color=DARK, fill=DARK)
    text(page, 50,  42, C["name"],  size=26, color=(1,1,1), bold=True)
    text(page, 50,  65, C["title"], size=13, color=(0.85,0.75,0.40))
    text(page, 50,  85, "alex.morgan@example.com  ·  linkedin.com/in/alexmorgan-fictional",
         size=9, color=(0.75,0.75,0.80))

    y = 130

    # ── summary ──────────────────────────────────────────────────────────────
    text(page, 50, y, "SUMMARY", size=9, color=GOLD, bold=True); y += 4
    rule(page, y); y += 14
    # wrap manually
    words = C["summary"].split()
    line_buf, lines = [], []
    for w in words:
        line_buf.append(w)
        if len(" ".join(line_buf)) > 88:
            lines.append(" ".join(line_buf[:-1]))
            line_buf = [w]
    lines.append(" ".join(line_buf))
    for ln in lines:
        text(page, 50, y, ln, size=10); y += 14
    y += 10

    # ── experience ───────────────────────────────────────────────────────────
    text(page, 50, y, "EXPERIENCE", size=9, color=GOLD, bold=True); y += 4
    rule(page, y); y += 14
    for company, role, period, desc in C["experience"]:
        text(page, 50,  y, role,    size=11, color=DARK, bold=True)
        text(page, 350, y, period,  size=9,  color=BODY)
        y += 14
        text(page, 50,  y, company, size=10, color=BODY, bold=True)
        y += 13
        # wrap description
        words = desc.split()
        line_buf, lines = [], []
        for w in words:
            line_buf.append(w)
            if len(" ".join(line_buf)) > 88:
                lines.append(" ".join(line_buf[:-1]))
                line_buf = [w]
        lines.append(" ".join(line_buf))
        for ln in lines:
            text(page, 60, y, "• " + ln, size=10); y += 13
        y += 8

    # ── certifications ───────────────────────────────────────────────────────
    text(page, 50, y, "CERTIFICATIONS", size=9, color=GOLD, bold=True); y += 4
    rule(page, y); y += 14
    for cert in C["certs"]:
        text(page, 60, y, "• " + cert, size=10); y += 13
    y += 8

    # ── education ────────────────────────────────────────────────────────────
    text(page, 50, y, "EDUCATION", size=9, color=GOLD, bold=True); y += 4
    rule(page, y); y += 14
    for degree, school, year in C["education"]:
        text(page, 50,  y, degree, size=11, color=DARK, bold=True)
        text(page, 380, y, year,   size=9,  color=BODY)
        y += 13
        text(page, 50,  y, school, size=10, color=BODY); y += 18

    # ── skills ───────────────────────────────────────────────────────────────
    text(page, 50, y, "SKILLS", size=9, color=GOLD, bold=True); y += 4
    rule(page, y); y += 14
    for skill in C["skills"]:
        text(page, 60, y, "• " + skill, size=10); y += 13

    # ── footer ───────────────────────────────────────────────────────────────
    page.draw_rect(fitz.Rect(0, H-30, W, H), color=DARK, fill=DARK)
    text(page, 50, H-12,
         "---",
         size=7, color=(0.55,0.55,0.65))

    doc.save(str(OUTPUT_PATH), garbage=4, deflate=True)
    doc.close()
    print(f"[+] Clean control resume saved → {OUTPUT_PATH}")

if __name__ == "__main__":
    build_clean_resume()
