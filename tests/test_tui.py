"""TUI tests: headless App.run_test (SPEC T15 to T22, T24)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pikepdf
import pytest
from textual.binding import Binding
from textual.widgets import Button, DataTable, Footer, Input, RadioButton, RadioSet, TextArea

from pdfsec import core, tui
from pdfsec.core import Result
from pdfsec.tui import PdfSecApp

from .conftest import file_hash

PW = "geheim-2026"
SETTLE = 0.2


async def click(pilot: Any, selector: str) -> None:
    """Click a widget and let the button animation settle.

    Without the settle time a second click on the same button is swallowed by
    the press animation, which makes tests look like application bugs.
    """
    await pilot.click(selector)
    await pilot.pause(SETTLE)


async def wait(app: PdfSecApp, pilot: Any) -> None:
    """Let the worker thread finish and the screen settle."""
    await app.workers.wait_for_complete()
    await pilot.pause(SETTLE)


def status_text(app: PdfSecApp) -> str:
    return str(app.query_one("#status").render())


def rows(app: PdfSecApp) -> list[tuple[str, ...]]:
    table = app.query_one(DataTable)
    return [
        tuple(str(cell) for cell in table.get_row_at(index)) for index in range(table.row_count)
    ]


def label_of(app: PdfSecApp, selector: str) -> str:
    return str(app.query_one(selector, Button).label)


def select_decrypt(app: PdfSecApp) -> None:
    app.query_one("#mode-decrypt", RadioButton).value = True


async def test_widgets_present_and_password_masked() -> None:
    """T15: every widget from F2 exists and the password field is masked."""
    app = PdfSecApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#mode", RadioSet).pressed_index == 0
        assert app.query_one("#paths", TextArea) is not None
        password = app.query_one("#password", Input)
        assert password.password is True
        assert label_of(app, "#toggle-password") == "Passwort anzeigen"
        assert app.query_one("#start", Button) is not None
        assert len(app.query_one(DataTable).columns) == 3
        assert app.query_one(Footer) is not None
        assert status_text(app) == ""


async def test_toggle_shows_password_and_resets_on_start(plain_pdf: Path) -> None:
    """T16: the toggle reveals the value; starting resets mask and clears the field."""
    app = PdfSecApp()
    async with app.run_test() as pilot:
        await click(pilot, "#toggle-password")
        password = app.query_one("#password", Input)
        assert password.password is False
        assert label_of(app, "#toggle-password") == "Passwort verbergen"

        password.value = PW
        app.query_one("#paths", TextArea).text = str(plain_pdf)
        await click(pilot, "#start")
        await wait(app, pilot)

        assert password.password is True
        assert password.value == ""
        assert label_of(app, "#toggle-password") == "Passwort anzeigen"


async def test_empty_password_and_empty_list() -> None:
    """T17: both empty inputs give their message and create nothing."""
    app = PdfSecApp()
    async with app.run_test() as pilot:
        await click(pilot, "#start")
        assert status_text(app) == "Bitte ein Passwort eingeben."

        app.query_one("#password", Input).value = PW
        await click(pilot, "#start")
        assert status_text(app) == "Bitte mindestens eine Datei angeben."
        assert len(rows(app)) == 0


async def test_batch_continues_after_error(plain_pdf: Path, tmp_path: Path) -> None:
    """T18: 3 lines, one broken: two done, one error, totals in the status line."""
    second = tmp_path / "anlage.pdf"
    second.write_bytes(plain_pdf.read_bytes())
    broken = tmp_path / "kaputt.pdf"
    broken.write_text("kein PDF", encoding="utf-8")

    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#paths", TextArea).text = "\n".join(
            [str(plain_pdf), str(broken), str(second)]
        )
        password = app.query_one("#password", Input)
        password.value = PW
        await click(pilot, "#start")
        await wait(app, pilot)

        assert status_text(app) == "2 von 3 fertig, 1 Fehler"
        assert password.value == ""
        table_rows = rows(app)
        assert len(table_rows) == 3
        done = [row for row in table_rows if row[1] == "Fertig"]
        failed = [row for row in table_rows if row[1] == "Fehler"]
        assert len(done) == 2
        assert len(failed) == 1
        assert failed[0][2] == "Die Datei ist keine lesbare PDF-Datei."
        assert "Seiten" in done[0][2]
        assert (tmp_path / "vertrag_sec.pdf").exists()
        assert (tmp_path / "anlage_sec.pdf").exists()


async def test_ui_recovers_after_error(plain_pdf: Path) -> None:
    """T19: after a failed run the app still works."""
    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#password", Input).value = ""
        await click(pilot, "#start")
        assert status_text(app) == "Bitte ein Passwort eingeben."

        app.query_one("#password", Input).value = PW
        app.query_one("#paths", TextArea).text = str(plain_pdf)
        await click(pilot, "#start")
        await wait(app, pilot)

        assert status_text(app) == "1 von 1 fertig, 0 Fehler"
        assert plain_pdf.with_name("vertrag_sec.pdf").exists()


async def test_quit_binding_and_german_footer() -> None:
    """T20: q quits, the footer text is German."""
    descriptions = {
        binding.key: binding.description
        for binding in PdfSecApp.BINDINGS
        if isinstance(binding, Binding)
    }
    assert descriptions["q"] == "Beenden"
    assert descriptions["ctrl+q"] == "Beenden"
    assert PdfSecApp.ENABLE_COMMAND_PALETTE is False

    app = PdfSecApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause(SETTLE)
        assert app.is_running is False


async def test_existing_target_reported_in_batch(plain_pdf: Path, tmp_path: Path) -> None:
    """T21: an existing target is an error row, the other file still finishes."""
    other = tmp_path / "anlage.pdf"
    other.write_bytes(plain_pdf.read_bytes())
    blocked = plain_pdf.with_name("vertrag_sec.pdf")
    blocked.write_bytes(b"alte Datei")
    before = file_hash(blocked)

    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#paths", TextArea).text = f"{plain_pdf}\n{other}"
        app.query_one("#password", Input).value = PW
        await click(pilot, "#start")
        await wait(app, pilot)

        assert status_text(app) == "1 von 2 fertig, 1 Fehler"
        table_rows = rows(app)
        assert table_rows[0][1] == "Fehler"
        assert table_rows[0][2] == "Zieldatei existiert bereits."
        assert table_rows[1][1] == "Fertig"
        assert file_hash(blocked) == before
        assert other.with_name("anlage_sec.pdf").exists()


async def test_work_runs_off_the_ui_thread(
    plain_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T22: the core call runs off the UI thread, the status line is set."""
    seen: dict[str, int] = {}

    def fake(path: Path | str, password: str) -> Result:
        seen["thread"] = threading.get_ident()
        target = Path(path).with_name("fake_sec.pdf")
        return Result(source=Path(path), target=target, pages=7)

    monkeypatch.setattr(tui, "encrypt_pdf", fake)

    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#paths", TextArea).text = str(plain_pdf)
        app.query_one("#password", Input).value = PW
        await click(pilot, "#start")
        await wait(app, pilot)

        assert seen["thread"] != threading.main_thread().ident
        assert status_text(app) == "1 von 1 fertig, 0 Fehler"
        assert rows(app)[0][1] == "Fertig"


async def test_duplicate_path_is_one_error_row(plain_pdf: Path) -> None:
    """T24: a path twice in the list is an error row, the file is handled once."""
    app = PdfSecApp()
    async with app.run_test() as pilot:
        app.query_one("#paths", TextArea).text = f"{plain_pdf}\n{plain_pdf}"
        app.query_one("#password", Input).value = PW
        await click(pilot, "#start")
        await wait(app, pilot)

        table_rows = rows(app)
        assert len(table_rows) == 2
        assert table_rows[0][1] == "Fertig"
        assert table_rows[1][1] == "Fehler"
        assert table_rows[1][2] == "Datei ist mehrfach in der Liste."
        assert status_text(app) == "1 von 2 fertig, 1 Fehler"


async def test_decrypt_mode_uses_core_decrypt(plain_pdf: Path) -> None:
    """T10 (UI path): mode Entschlüsseln writes the _open file."""
    protected = core.encrypt_pdf(plain_pdf, PW).target

    app = PdfSecApp()
    async with app.run_test() as pilot:
        select_decrypt(app)
        await pilot.pause()
        assert app.query_one("#mode", RadioSet).pressed_index == 1
        app.query_one("#paths", TextArea).text = str(protected)
        app.query_one("#password", Input).value = PW
        await click(pilot, "#start")
        await wait(app, pilot)

        assert status_text(app) == "1 von 1 fertig, 0 Fehler"
        opened = protected.with_name("vertrag_sec_open.pdf")
        assert opened.exists()
        with pikepdf.open(opened) as pdf:
            assert not pdf.is_encrypted
