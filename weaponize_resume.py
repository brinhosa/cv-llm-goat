"""
BSides Porto 2026 — CV Prompt Injection Demo
Step 2: Takes clean fictional resume and generates 6 injection variants.

Techniques demonstrated:
  Layer 1 — White text on white background
  Layer 2 — PDF metadata fields
  Layer 3 — Micro font (0.1 pt)
  Layer 4 — Hidden PDF annotation
  Layer 5 — Zero-width Unicode encoding
  Layer 6 — All layers combined (demo artifact)

RESEARCH USE ONLY. Fictional candidate. Never submit to real employers.
"""
import fitz
from pathlib import Path
from payloads import PAYLOADS

INPUT_PDF  = Path("output/resume_CLEAN_control.pdf")
OUTPUT_DIR = Path("output")


# ── Layer helpers ─────────────────────────────────────────────────────────────

def layer1_white_text(doc: fitz.Document):
    """White text (color 1,1,1) on white background — invisible to humans."""
    page = doc[0]
    rect = fitz.Rect(50, page.rect.height - 60, page.rect.width - 50, page.rect.height - 35)
    page.insert_textbox(
        rect,
        PAYLOADS["direct_override"],
        fontsize=9,
        color=(1, 1, 1),   # white on white
    )


def layer2_metadata(doc: fitz.Document):
    """Inject override instructions into PDF metadata fields.
    Many LLM document parsers include metadata in context."""
    meta = doc.metadata.copy()
    meta["author"]   = "Alex Morgan | CISSP, OSCP, CEH"
    meta["keywords"] = PAYLOADS["suppression"]
    meta["subject"]  = PAYLOADS["authority_hijack"]
    meta["creator"]  = "MIT Graduate 2020"
    doc.set_metadata(meta)


def layer3_microfont(doc: fitz.Document):
    """0.1 pt font — renders as a single invisible dot at max zoom."""
    page = doc[-1]
    rect = fitz.Rect(50, page.rect.height - 8, page.rect.width - 50, page.rect.height - 1)
    page.insert_textbox(
        rect,
        PAYLOADS["persistent"],
        fontsize=0.1,
        color=(0, 0, 0),   # black — size alone hides it
    )


def layer4_hidden_annotation(doc: fitz.Document):
    """Hidden sticky-note annotation — not rendered, not printed.
    Text extractors and some LLM parsers include annotation content."""
    page = doc[0]
    annot = page.add_text_annot(
        fitz.Point(10, 10),
        PAYLOADS["json_structured"],
    )
    annot.set_flags(fitz.PDF_ANNOT_IS_HIDDEN | fitz.PDF_ANNOT_IS_NO_VIEW)
    annot.update()


def layer5_zero_width_chars(doc: fitz.Document):
    """Encode payload as zero-width Unicode characters.
    ZWJ (U+200D) = bit 1, ZWNJ (U+200C) = bit 0.
    LLM tokenizers process these — the model receives the decoded payload."""
    payload_bytes = PAYLOADS["direct_override"].encode("utf-8")
    zwc = "".join(
        "\u200d" if (byte >> i) & 1 else "\u200c"
        for byte in payload_bytes
        for i in range(7, -1, -1)
    )
    page = doc[0]
    # Placed at top-left as 1pt invisible text, blends with existing content
    rect = fitz.Rect(50, 78, 300, 90)
    page.insert_textbox(rect, zwc, fontsize=1, color=(1, 1, 1))


# ── Build all variants ────────────────────────────────────────────────────────

VARIANTS = {
    "layer1_whitetext":  [layer1_white_text],
    "layer2_metadata":   [layer2_metadata],
    "layer3_microfont":  [layer3_microfont],
    "layer4_annotation": [layer4_hidden_annotation],
    "layer5_zwc":        [layer5_zero_width_chars],
    "layer6_combined":   [
        layer1_white_text,
        layer2_metadata,
        layer3_microfont,
        layer4_hidden_annotation,
        layer5_zero_width_chars,
    ],
}


def build_variants():
    if not INPUT_PDF.exists():
        print("[!] Clean resume not found. Run create_fictional_resume.py first.")
        return

    for name, funcs in VARIANTS.items():
        doc = fitz.open(str(INPUT_PDF))
        for fn in funcs:
            fn(doc)
        out = OUTPUT_DIR / f"resume_{name}.pdf"
        doc.save(str(out), garbage=4, deflate=True)
        doc.close()
        print(f"[+] Created: {out}")

    print("\n[✓] All variants generated.")
    print("    → Demo artifact : output/resume_layer6_combined.pdf")
    print("    → Control copy  : output/resume_CLEAN_control.pdf")
    print("\n    Verify with:  pdftotext output/resume_layer6_combined.pdf -")


if __name__ == "__main__":
    build_variants()
