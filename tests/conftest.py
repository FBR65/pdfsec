"""Shared fixtures: real PDF files made with pikepdf."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pikepdf
import pytest


@pytest.fixture
def plain_pdf(tmp_path: Path) -> Path:
    """A two-page PDF without encryption."""
    path = tmp_path / "vertrag.pdf"
    pdf = pikepdf.Pdf.new()
    for _ in range(2):
        pdf.add_blank_page(page_size=(200, 200))
    pdf.save(path)
    pdf.close()
    return path


@pytest.fixture
def text_file(tmp_path: Path) -> Path:
    """A file that only looks like a document."""
    path = tmp_path / "notiz.pdf"
    path.write_text("kein PDF", encoding="utf-8")
    return path


def file_hash(path: Path) -> str:
    """SHA-256 of a file, for before/after comparisons."""
    return hashlib.sha256(path.read_bytes()).hexdigest()
