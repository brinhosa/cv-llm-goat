"""
Text extraction for uploaded resumes (.txt / .pdf).

IMPORTANT for the demo: we extract ALL text the model would see, including
hidden layers (white text, micro-font, annotations, zero-width chars). This is
exactly what makes the resume dangerous — the human reviewer never sees these,
but the LLM does.
"""
from __future__ import annotations

import io


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _extract_pdf(data)
    # default: treat as plain text
    return data.decode("utf-8", errors="replace")


def _extract_pdf(data: bytes) -> str:
    # Prefer PyMuPDF (fitz): pulls visible text + many hidden layers.
    try:
        import fitz  # pymupdf

        parts: list[str] = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            # document + page metadata (covers metadata-injection layer)
            meta = doc.metadata or {}
            meta_blob = " ".join(str(v) for v in meta.values() if v)
            if meta_blob.strip():
                parts.append(meta_blob)
            for page in doc:
                parts.append(page.get_text("text"))
                # annotations (covers annotation-injection layer)
                for annot in page.annots() or []:
                    info = annot.info or {}
                    for key in ("content", "title", "subject"):
                        val = info.get(key)
                        if val:
                            parts.append(val)
        text = "\n".join(p for p in parts if p)
        if text.strip():
            return text
    except Exception:
        pass

    # Fallback: pypdf
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:  # pragma: no cover
        return f"[extraction failed: {exc}]"
