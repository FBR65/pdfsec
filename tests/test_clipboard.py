"""Clipboard reader without a display server (SPEC F29, IN1)."""

from __future__ import annotations

import sys

import pytest

from pdfsec.clipboard import read_clipboard


def test_missing_tkinter_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """A Python without Tkinter must not crash the app."""
    monkeypatch.setitem(sys.modules, "tkinter", None)

    assert read_clipboard() is None


def test_tk_failure_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """A Tk that cannot open the display is treated as 'no clipboard'."""

    class BrokenTk:
        def __init__(self) -> None:
            raise RuntimeError("kein Display")

    class FakeTkinter:
        Tk = BrokenTk

    monkeypatch.setitem(sys.modules, "tkinter", FakeTkinter)

    assert read_clipboard() is None


class FakeRoot:
    """Minimal stand-in for a Tk root window."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.withdrawn = False
        self.destroyed = False

    def withdraw(self) -> None:
        self.withdrawn = True

    def clipboard_get(self) -> str:
        return self.text

    def destroy(self) -> None:
        self.destroyed = True


def test_returns_clipboard_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """A working Tk delivers the text and the window is closed again."""
    root = FakeRoot("/tmp/datei.pdf")

    class FakeTkinter:
        @staticmethod
        def Tk() -> FakeRoot:
            return root

    monkeypatch.setitem(sys.modules, "tkinter", FakeTkinter)

    assert read_clipboard() == "/tmp/datei.pdf"
    assert root.withdrawn is True
    assert root.destroyed is True


def test_empty_clipboard_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty clipboard is reported as 'nothing to paste'."""
    root = FakeRoot("")

    class FakeTkinter:
        @staticmethod
        def Tk() -> FakeRoot:
            return root

    monkeypatch.setitem(sys.modules, "tkinter", FakeTkinter)

    assert read_clipboard() is None
    assert root.destroyed is True
