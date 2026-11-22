"""TUI for pdfsec: encrypt or decrypt PDF files, one path per line.

The layout must fit a 80x24 terminal (SPEC A2); every visible string is German.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Static,
    TextArea,
)

from pdfsec.clipboard import read_clipboard
from pdfsec.core import (
    InvalidPdf,
    PdfSecError,
    Result,
    TargetNotSupported,
    decrypt_pdf,
    encrypt_pdf,
)


class Mode(Enum):
    """What the run does with each file."""

    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"


_FIXED_MESSAGES = {
    "EmptyPassword": "Bitte ein Passwort eingeben.",
    "OutputExists": "Zieldatei existiert bereits.",
    "AlreadyEncrypted": "Die Datei ist bereits verschlüsselt.",
    "NotEncrypted": "Die Datei ist nicht verschlüsselt.",
    "WrongPassword": "Passwort falsch.",
    "VerificationFailed": (
        "Die Prüfung der Ausgabe ist fehlgeschlagen. Es wurde nichts gespeichert."
    ),
}


def message_for(error: PdfSecError | OSError) -> str:
    """German message for one expected failure (SPEC section 9)."""
    if isinstance(error, InvalidPdf):
        if error.reason == "not_found":
            return "Die Datei wurde nicht gefunden."
        if error.reason == "not_a_file":
            return "Der Pfad ist keine Datei."
        return "Die Datei ist keine lesbare PDF-Datei."
    if isinstance(error, TargetNotSupported):
        return f"Der Zielordner unterstützt kein atomares Anlegen: {error}"
    if isinstance(error, OSError):
        return f"Die Zieldatei konnte nicht geschrieben werden: {error.strerror or error}"
    return _FIXED_MESSAGES.get(type(error).__name__, str(error))


MASKED_LABEL = "Passwort anzeigen"
VISIBLE_LABEL = "Passwort verbergen"


class PdfSecApp(App[None]):
    """The application: mode, path list, one password, one result table."""

    TITLE = "PDFSec"
    SUB_TITLE = "PDF verschlüsseln und entschlüsseln"
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        layout: vertical;
        padding: 0 1;
    }
    #title {
        height: 1;
        text-style: bold;
    }
    Label {
        height: 1;
    }
    #mode {
        height: auto;
    }
    #paths {
        height: 5;
        border: round $accent;
    }
    #password-row {
        height: 3;
    }
    #password {
        width: 1fr;
    }
    #toggle-password {
        width: 20;
        margin-left: 1;
    }
    #start {
        width: auto;
        margin-left: 1;
    }
    #results {
        height: 1fr;
        border: round $accent;
    }
    #status {
        height: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Beenden"),
        Binding("ctrl+q", "quit", "Beenden"),
        Binding("ctrl+v", "paste_clipboard", "Einfügen", priority=True, show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Static("PDFSec — PDF verschlüsseln und entschlüsseln", id="title")
        yield Label("Modus")
        yield RadioSet(
            RadioButton("Verschlüsseln", value=True, id="mode-encrypt"),
            RadioButton("Entschlüsseln", id="mode-decrypt"),
            id="mode",
        )
        yield Label("PDF-Dateien (eine pro Zeile)")
        yield TextArea(id="paths", placeholder="/pfad/zur/datei.pdf")
        yield Label("Passwort")
        with Horizontal(id="password-row"):
            yield Input(password=True, id="password", placeholder="Passwort")
            yield Button(MASKED_LABEL, id="toggle-password")
            yield Button("Start", id="start", variant="primary")
        yield DataTable(id="results")
        yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Datei", width=24)
        table.add_column("Ergebnis", width=9)
        table.add_column("Ziel / Meldung")
        table.cursor_type = "row"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "toggle-password":
            self._toggle_password()
        elif event.button.id == "start":
            self._start()

    def _toggle_password(self) -> None:
        field = self.query_one("#password", Input)
        button = self.query_one("#toggle-password", Button)
        field.password = not field.password
        button.label = MASKED_LABEL if field.password else VISIBLE_LABEL

    def action_paste_clipboard(self) -> None:
        """Insert the system clipboard into the focused field (Ctrl+V)."""
        text = read_clipboard()
        if not text:
            self._set_status(
                "Zwischenablage ist leer oder nicht lesbar. Im Terminal hilft Strg+Umschalt+V."
            )
            return
        target = self.focused
        if isinstance(target, Input):
            target.insert_text_at_cursor(" ".join(text.splitlines()))
        elif isinstance(target, TextArea):
            target.insert(text)
        else:
            self.query_one("#paths", TextArea).insert(text)

    def _start(self) -> None:
        field = self.query_one("#password", Input)
        password = field.value
        lines = [
            line.strip()
            for line in self.query_one("#paths", TextArea).text.splitlines()
            if line.strip()
        ]
        if not password:
            self._set_status("Bitte ein Passwort eingeben.")
            return
        if not lines:
            self._set_status("Bitte mindestens eine Datei angeben.")
            return

        self.query_one(DataTable).clear()
        self.query_one("#toggle-password", Button).label = MASKED_LABEL
        field.password = True
        field.value = ""
        self._set_status("Läuft …")
        self.run_batch(self._selected_mode(), lines, password)

    def _selected_mode(self) -> Mode:
        index = self.query_one("#mode", RadioSet).pressed_index
        return Mode.DECRYPT if index == 1 else Mode.ENCRYPT

    @work(thread=True, exclusive=True)
    def run_batch(self, mode: Mode, lines: list[str], password: str) -> None:
        """Work through every path. One failure must not stop the rest."""
        done = 0
        failed = 0
        seen: set[str] = set()
        for raw in lines:
            path = Path(raw).expanduser()
            key = str(path.resolve()) if path.exists() else str(path)
            if key in seen:
                failed += 1
                self._row_from_thread(path, "Fehler", "Datei ist mehrfach in der Liste.")
                continue
            seen.add(key)
            try:
                result = self._process(mode, path, password)
            except (PdfSecError, OSError) as error:
                failed += 1
                self._row_from_thread(path, "Fehler", message_for(error))
            else:
                done += 1
                self._row_from_thread(path, "Fertig", self._detail(result))
        self.call_from_thread(
            self._set_status,
            f"{done} von {len(lines)} fertig, {failed} Fehler",
        )

    @staticmethod
    def _process(mode: Mode, path: Path, password: str) -> Result:
        if mode is Mode.DECRYPT:
            return decrypt_pdf(path, password)
        return encrypt_pdf(path, password)

    @staticmethod
    def _detail(result: Result) -> str:
        detail = f"{result.target.name} — {result.target.parent} ({result.pages} Seiten)"
        if result.warning:
            detail = f"{detail} — {result.warning}"
        return detail

    def _row_from_thread(self, path: Path, state: str, detail: str) -> None:
        self.call_from_thread(self._add_row, path, state, detail)

    def _add_row(self, path: Path, state: str, detail: str) -> None:
        self.query_one(DataTable).add_row(str(path), state, detail)

    def _set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(text)
