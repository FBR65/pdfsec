"""Entry point test (SPEC F1, IN3)."""

from __future__ import annotations

import pytest

import pdfsec
from pdfsec.tui import PdfSecApp


def test_main_runs_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    """`pdfsec.main()` starts the TUI and returns when it ends."""
    started: list[bool] = []

    def fake_run(self: PdfSecApp) -> None:
        started.append(True)

    monkeypatch.setattr(PdfSecApp, "run", fake_run)

    pdfsec.main()

    assert started == [True]
