"""Read the system clipboard without a subprocess.

Tkinter is part of the standard library and talks to the display server
directly, so the application keeps its promise of no subprocesses (SPEC IN1).
Without a display, without Tkinter or with an empty clipboard the function
returns None and the UI tells the user what to do instead.
"""

from __future__ import annotations

from contextlib import suppress


def read_clipboard() -> str | None:
    """Return the clipboard text, or None when it cannot be read."""
    try:
        import tkinter
    except ImportError:
        return None

    root = None
    try:
        root = tkinter.Tk()
        root.withdraw()
        text = root.clipboard_get()
    except Exception:  # noqa: BLE001 - any Tk failure means "no clipboard here"
        return None
    finally:
        if root is not None:
            with suppress(Exception):
                root.destroy()
    return text or None
