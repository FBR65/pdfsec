"""pdfsec: PDF files with a password, driven by a TUI."""

from __future__ import annotations


def main() -> None:
    """Start the TUI."""
    from pdfsec.tui import PdfSecApp

    PdfSecApp().run()
