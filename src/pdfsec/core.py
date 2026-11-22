"""Core logic: encrypt and decrypt one PDF file. No user interface here.

The write path is: temporary file in the target directory, verification of the
protection state, then a hard link to the final name. A hard link never
replaces an existing file, so a concurrent run or an old output cannot be
overwritten (SPEC F9, F16, E7).
"""

from __future__ import annotations

import errno
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pikepdf


class PdfSecError(Exception):
    """Base class for all expected failures."""


class EmptyPassword(PdfSecError):
    """The password was empty."""


class OutputExists(PdfSecError):
    """The target file already exists."""


class AlreadyEncrypted(PdfSecError):
    """The input is already encrypted and the mode is encrypt."""


class NotEncrypted(PdfSecError):
    """The input is not encrypted and the mode is decrypt."""


class WrongPassword(PdfSecError):
    """The password does not open the input."""


class VerificationFailed(PdfSecError):
    """The written file does not have the requested protection state."""


class TargetNotSupported(PdfSecError):
    """The target directory cannot create a hard link."""


class InvalidPdf(PdfSecError):
    """The input is missing or is not a readable PDF."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Result:
    """What one successful run produced."""

    source: Path
    target: Path
    pages: int
    warning: str | None = None


def target_for(path: Path, *, encrypt: bool) -> Path:
    """Build the target path for one input file."""
    suffix = "_sec" if encrypt else "_open"
    return path.with_name(f"{path.stem}{suffix}.pdf")


def encrypt_pdf(path: Path | str, password: str) -> Result:
    """Encrypt one PDF and write it next to the input as <stem>_sec.pdf."""
    source = Path(path)
    _require_password(password)
    _check_input(source)
    try:
        pdf = pikepdf.open(source)
    except pikepdf.PasswordError as exc:
        raise AlreadyEncrypted(str(source)) from exc
    except pikepdf.PdfError as exc:
        raise InvalidPdf("not_a_pdf") from exc

    with pdf:
        if pdf.is_encrypted:
            raise AlreadyEncrypted(str(source))
        pages = len(pdf.pages)
        target = target_for(source, encrypt=True)
        if target.exists():
            raise OutputExists(str(target))
        temporary = _temporary_path(target)
        try:
            pdf.save(
                temporary,
                encryption=pikepdf.Encryption(
                    owner=password,
                    user=password,
                    R=6,
                    aes=True,
                    metadata=True,
                ),
            )
            _verify_encrypted(temporary, password)
            warning = _publish(temporary, target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    return Result(source=source, target=target, pages=pages, warning=warning)


def decrypt_pdf(path: Path | str, password: str) -> Result:
    """Remove the password from one PDF and write <stem>_open.pdf."""
    source = Path(path)
    _require_password(password)
    _check_input(source)
    pdf = _open_for_decrypt(source, password)

    with pdf:
        pages = len(pdf.pages)
        target = target_for(source, encrypt=False)
        if target.exists():
            raise OutputExists(str(target))
        temporary = _temporary_path(target)
        try:
            pdf.save(temporary)
            _verify_open(temporary)
            warning = _publish(temporary, target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    return Result(source=source, target=target, pages=pages, warning=warning)


def _open_for_decrypt(source: Path, password: str) -> pikepdf.Pdf:
    """Open the input once, without a warning for files that need no password."""
    try:
        pdf = pikepdf.open(source)
    except pikepdf.PasswordError:
        pdf = None
    except pikepdf.PdfError as exc:
        raise InvalidPdf("not_a_pdf") from exc

    if pdf is not None:
        if not pdf.is_encrypted:
            pdf.close()
            raise NotEncrypted(str(source))
        return pdf

    try:
        return pikepdf.open(source, password=password)
    except pikepdf.PasswordError as exc:
        raise WrongPassword(str(source)) from exc
    except pikepdf.PdfError as exc:
        raise InvalidPdf("not_a_pdf") from exc


def _require_password(password: str) -> None:
    if not password:
        raise EmptyPassword("empty password")


def _check_input(path: Path) -> None:
    if not path.exists():
        raise InvalidPdf("not_found")
    if not path.is_file():
        raise InvalidPdf("not_a_file")


def _temporary_path(target: Path) -> Path:
    descriptor, name = tempfile.mkstemp(dir=target.parent, prefix=".pdfsec-", suffix=".pdf")
    os.close(descriptor)
    return Path(name)


def _verify_encrypted(path: Path, password: str) -> None:
    """The file must open with the password and must not open without it."""
    try:
        with pikepdf.open(path):
            pass
    except pikepdf.PasswordError:
        pass
    else:
        raise VerificationFailed(path.name)
    with pikepdf.open(path, password=password) as check:
        if not check.is_encrypted:
            raise VerificationFailed(path.name)


def _verify_open(path: Path) -> None:
    """The file must open without a password and must not be encrypted."""
    try:
        with pikepdf.open(path) as check:
            if check.is_encrypted:
                raise VerificationFailed(path.name)
    except pikepdf.PasswordError as exc:
        raise VerificationFailed(path.name) from exc


def _publish(temporary: Path, target: Path) -> str | None:
    """Link the verified file to its final name; never replace a file."""
    try:
        os.link(temporary, target)
    except FileExistsError as exc:
        raise OutputExists(str(target)) from exc
    except OSError as exc:
        if exc.errno in (errno.EPERM, errno.EXDEV):
            raise TargetNotSupported(str(target)) from exc
        raise

    try:
        temporary.unlink()
    except OSError:
        return f"Temporäre Datei konnte nicht entfernt werden: {temporary.name}"
    return None
