"""Ctrl+V pastes the system clipboard into the focused field (SPEC F29)."""

from __future__ import annotations

from typing import Any

import pytest
from textual.widgets import Input, TextArea

from pdfsec import tui
from pdfsec.tui import PdfSecApp


def status_text(app: PdfSecApp) -> str:
    return str(app.query_one("#status").render())


async def press_paste(pilot: Any) -> None:
    await pilot.press("ctrl+v")
    await pilot.pause(0.2)


async def test_paste_into_path_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """F29: the copied path lands in the path list."""
    monkeypatch.setattr(tui, "read_clipboard", lambda: "/tmp/eingefuegt.pdf")
    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#paths", TextArea).focus()
        await pilot.pause(0.1)
        await press_paste(pilot)

        assert app.query_one("#paths", TextArea).text == "/tmp/eingefuegt.pdf"


async def test_paste_into_password_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """F29: a single-line paste also works in the password field."""
    monkeypatch.setattr(tui, "read_clipboard", lambda: "Geheim-2026\n")
    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#password", Input).focus()
        await pilot.pause(0.1)
        await press_paste(pilot)

        assert app.query_one("#password", Input).value == "Geheim-2026"


async def test_paste_without_clipboard_shows_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    """F29: an unreadable clipboard gives a German hint, nothing is inserted."""
    monkeypatch.setattr(tui, "read_clipboard", lambda: None)
    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#paths", TextArea).focus()
        await pilot.pause(0.1)
        await press_paste(pilot)

        assert app.query_one("#paths", TextArea).text == ""
        assert "Zwischenablage" in status_text(app)


async def test_paste_with_button_focused_goes_to_path_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F29: with a button focused the paste still lands in the path list."""
    monkeypatch.setattr(tui, "read_clipboard", lambda: "/tmp/ziel.pdf")
    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#start").focus()
        await pilot.pause(0.1)
        await press_paste(pilot)

        assert app.query_one("#paths", TextArea).text == "/tmp/ziel.pdf"
