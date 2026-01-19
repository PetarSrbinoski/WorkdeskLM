from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, Tuple

import fitz

SUPPORTED_EXTS = {".pdf", ".txt", ".md"}

@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    text: str

def sha256_bytes(data:bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def parse_pdf_bytes(data: bytes) -> list[ParsedPage]:
    doc = fitz.open(stream = data, filetype = "pdf")
    pages: List[ParsedPage] = []

    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text") or ""
        pages.append(ParsedPage(page_number=i + 1, text = text.strip()))
    doc.close()
    return pages

def parse_text_bytes(data: bytes) -> List[ParsedPage]:
    text = data.decode("utf-8", errors="replace")
    return [ParsedPage(page_number=1, text=text.strip())]


def parse_file(filename: str, data: bytes) -> Tuple[str, List[ParsedPage]]:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf", parse_pdf_bytes(data)
    if lower.endswith(".txt"):
        return "text/plain", parse_text_bytes(data)
    if lower.endswith(".md"):
        return "text/markdown", parse_text_bytes(data)
    raise ValueError("Unsupported file type. Allowed: PDF, TXT, MD")