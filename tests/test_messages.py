"""Message mapping and result formatting (SPEC section 9, F21)."""

from __future__ import annotations

import errno
from pathlib import Path

from pdfsec.core import (
    AlreadyEncrypted,
    EmptyPassword,
    InvalidPdf,
    NotEncrypted,
    OutputExists,
    Result,
    TargetNotSupported,
    VerificationFailed,
    WrongPassword,
)
from pdfsec.tui import PdfSecApp, message_for


def test_message_for_every_error() -> None:
    """Each expected failure has exactly one German message."""
    assert message_for(EmptyPassword()) == "Bitte ein Passwort eingeben."
    assert message_for(OutputExists("/x")) == "Zieldatei existiert bereits."
    assert message_for(AlreadyEncrypted("/x")) == "Die Datei ist bereits verschlüsselt."
    assert message_for(NotEncrypted("/x")) == "Die Datei ist nicht verschlüsselt."
    assert message_for(WrongPassword("/x")) == "Passwort falsch."
    assert message_for(InvalidPdf("not_found")) == "Die Datei wurde nicht gefunden."
    assert message_for(InvalidPdf("not_a_file")) == "Der Pfad ist keine Datei."
    assert message_for(InvalidPdf("not_a_pdf")) == "Die Datei ist keine lesbare PDF-Datei."
    assert message_for(VerificationFailed("x")) == (
        "Die Prüfung der Ausgabe ist fehlgeschlagen. Es wurde nichts gespeichert."
    )
    assert message_for(TargetNotSupported("/ziel")) == (
        "Der Zielordner unterstützt kein atomares Anlegen: /ziel"
    )
    assert message_for(OSError(errno.EACCES, "Permission denied")) == (
        "Die Zieldatei konnte nicht geschrieben werden: Permission denied"
    )


def test_detail_names_target_pages_and_warning() -> None:
    """F21/F26: the result cell shows target, page count and the warning."""
    plain = Result(source=Path("a.pdf"), target=Path("a_sec.pdf"), pages=3)
    assert PdfSecApp._detail(plain) == "a_sec.pdf — . (3 Seiten)"

    warned = Result(
        source=Path("a.pdf"),
        target=Path("a_sec.pdf"),
        pages=3,
        warning="Temporäre Datei konnte nicht entfernt werden: .pdfsec-abc.pdf",
    )
    assert PdfSecApp._detail(warned).endswith(
        "— Temporäre Datei konnte nicht entfernt werden: .pdfsec-abc.pdf"
    )
