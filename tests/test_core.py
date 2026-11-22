"""Core tests: encrypt and decrypt one PDF (SPEC T1 to T14, T23)."""

from __future__ import annotations

import errno
import os
from pathlib import Path

import pikepdf
import pytest

from pdfsec import core
from pdfsec.core import (
    AlreadyEncrypted,
    EmptyPassword,
    InvalidPdf,
    NotEncrypted,
    OutputExists,
    TargetNotSupported,
    VerificationFailed,
    WrongPassword,
    decrypt_pdf,
    encrypt_pdf,
    target_for,
)

from .conftest import file_hash

PW = "geheim-2026"


def leftovers(directory: Path) -> list[Path]:
    """Temporary files the core must never leave behind."""
    return [p for p in directory.iterdir() if p.name.startswith(".pdfsec-")]


def test_encrypt_creates_protected_file(plain_pdf: Path) -> None:
    """T1: output exists, is encrypted, opens with the password, keeps page count."""
    result = encrypt_pdf(plain_pdf, PW)

    assert result.target == plain_pdf.with_name("vertrag_sec.pdf")
    assert result.pages == 2
    assert result.source == plain_pdf
    assert result.target.stat().st_mode & 0o777 == 0o600
    with pikepdf.open(result.target, password=PW) as out:
        assert out.is_encrypted
        assert len(out.pages) == 2
    assert leftovers(plain_pdf.parent) == []


def test_output_rejects_empty_password(plain_pdf: Path) -> None:
    """T2: the saved file does not open without the password."""
    target = encrypt_pdf(plain_pdf, PW).target

    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(target)


def test_empty_password_is_refused(plain_pdf: Path) -> None:
    """T3: empty password fails and writes nothing."""
    with pytest.raises(EmptyPassword):
        encrypt_pdf(plain_pdf, "")

    assert not plain_pdf.with_name("vertrag_sec.pdf").exists()
    assert leftovers(plain_pdf.parent) == []


def test_existing_target_is_not_touched(plain_pdf: Path) -> None:
    """T4: an existing target raises and keeps its content."""
    target = plain_pdf.with_name("vertrag_sec.pdf")
    target.write_bytes(b"alte Datei")
    before = file_hash(target)

    with pytest.raises(OutputExists):
        encrypt_pdf(plain_pdf, PW)

    assert file_hash(target) == before


def test_encrypted_input_is_refused(plain_pdf: Path) -> None:
    """T5: encrypting an already encrypted file fails and writes nothing."""
    protected = encrypt_pdf(plain_pdf, PW).target
    before = file_hash(protected)

    with pytest.raises(AlreadyEncrypted):
        encrypt_pdf(protected, PW)

    assert file_hash(protected) == before
    assert not protected.with_name("vertrag_sec_sec.pdf").exists()


def test_umlaut_password_roundtrip(plain_pdf: Path) -> None:
    """T6: a password with umlauts works in both directions."""
    password = "Grüße-2026-äöüß"
    protected = encrypt_pdf(plain_pdf, password).target
    with pikepdf.open(protected, password=password) as pdf:
        assert pdf.is_encrypted

    result = decrypt_pdf(protected, password)

    with pikepdf.open(result.target) as pdf:
        assert not pdf.is_encrypted


def test_non_pdf_is_invalid(text_file: Path) -> None:
    """T7: a text file is reported as not a PDF, no temporary file stays."""
    with pytest.raises(InvalidPdf) as info:
        encrypt_pdf(text_file, PW)

    assert info.value.reason == "not_a_pdf"
    assert leftovers(text_file.parent) == []
    assert not text_file.with_name("notiz_sec.pdf").exists()


def test_missing_file_is_invalid(tmp_path: Path) -> None:
    """T7: a missing path is reported with its own reason."""
    with pytest.raises(InvalidPdf) as info:
        encrypt_pdf(tmp_path / "weg.pdf", PW)

    assert info.value.reason == "not_found"


def test_directory_is_not_a_file(tmp_path: Path) -> None:
    """T7: a directory is reported with its own reason."""
    with pytest.raises(InvalidPdf) as info:
        encrypt_pdf(tmp_path, PW)

    assert info.value.reason == "not_a_file"


def test_read_only_directory_fails_cleanly(plain_pdf: Path) -> None:
    """T8: no write permission gives OSError, no temporary file, no output."""
    os.chmod(plain_pdf.parent, 0o500)
    try:
        with pytest.raises(OSError) as info:
            encrypt_pdf(plain_pdf, PW)
        assert info.value.errno == errno.EACCES
        assert not plain_pdf.with_name("vertrag_sec.pdf").exists()
    finally:
        os.chmod(plain_pdf.parent, 0o700)
    assert leftovers(plain_pdf.parent) == []


def test_target_names(tmp_path: Path) -> None:
    """T9: target names follow the SPEC for both modes."""
    assert target_for(tmp_path / "a.pdf", encrypt=True) == tmp_path / "a_sec.pdf"
    assert target_for(tmp_path / "b.PDF", encrypt=True) == tmp_path / "b_sec.pdf"
    assert target_for(tmp_path / "c_sec.pdf", encrypt=False) == tmp_path / "c_sec_open.pdf"


def test_decrypt_removes_protection(plain_pdf: Path) -> None:
    """T10: decrypt writes an unprotected copy with the same page count."""
    protected = encrypt_pdf(plain_pdf, PW).target

    result = decrypt_pdf(protected, PW)

    assert result.target == protected.with_name("vertrag_sec_open.pdf")
    assert result.pages == 2
    with pikepdf.open(result.target) as out:
        assert not out.is_encrypted
        assert len(out.pages) == 2
    assert leftovers(plain_pdf.parent) == []


def test_decrypt_with_wrong_password(plain_pdf: Path) -> None:
    """T11: a wrong password is reported and writes nothing."""
    protected = encrypt_pdf(plain_pdf, PW).target

    with pytest.raises(WrongPassword):
        decrypt_pdf(protected, "falsch")

    assert not protected.with_name("vertrag_sec_open.pdf").exists()
    assert leftovers(plain_pdf.parent) == []


def test_decrypt_unprotected_file(plain_pdf: Path) -> None:
    """T12: decrypting an unprotected file is refused."""
    with pytest.raises(NotEncrypted):
        decrypt_pdf(plain_pdf, PW)

    assert not plain_pdf.with_name("vertrag_open.pdf").exists()


def test_failed_encrypt_verification(plain_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T13: a failed check removes the temporary file and writes nothing."""

    def boom(path: Path, password: str) -> None:
        raise VerificationFailed(path.name)

    monkeypatch.setattr(core, "_verify_encrypted", boom)

    with pytest.raises(VerificationFailed):
        encrypt_pdf(plain_pdf, PW)

    assert not plain_pdf.with_name("vertrag_sec.pdf").exists()
    assert leftovers(plain_pdf.parent) == []


def test_failed_decrypt_verification(plain_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T14: the same for the decrypt direction."""
    protected = encrypt_pdf(plain_pdf, PW).target

    def boom(path: Path) -> None:
        raise VerificationFailed(path.name)

    monkeypatch.setattr(core, "_verify_open", boom)

    with pytest.raises(VerificationFailed):
        decrypt_pdf(protected, PW)

    assert not protected.with_name("vertrag_sec_open.pdf").exists()
    assert leftovers(plain_pdf.parent) == []


def test_input_hash_never_changes(plain_pdf: Path) -> None:
    """T23: every input keeps its hash, also on failures (IN2, Z8)."""
    before = file_hash(plain_pdf)
    protected = encrypt_pdf(plain_pdf, PW).target
    assert file_hash(plain_pdf) == before

    protected_hash = file_hash(protected)
    decrypt_pdf(protected, PW)
    assert file_hash(protected) == protected_hash

    with pytest.raises(WrongPassword):
        decrypt_pdf(protected, "falsch")
    assert file_hash(protected) == protected_hash

    with pytest.raises(OutputExists):
        encrypt_pdf(plain_pdf, PW)
    assert file_hash(plain_pdf) == before


def test_verify_encrypted_rejects_plain_file(plain_pdf: Path) -> None:
    """T13: the check rejects a file that opens without any password."""
    with pytest.raises(VerificationFailed):
        core._verify_encrypted(plain_pdf, PW)


def test_verify_open_rejects_protected_file(plain_pdf: Path) -> None:
    """T14: the decrypt check rejects a file that is still encrypted."""
    protected = encrypt_pdf(plain_pdf, PW).target

    with pytest.raises(VerificationFailed):
        core._verify_open(protected)


def test_target_directory_without_hardlinks(
    plain_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RIS12: EPERM from os.link becomes TargetNotSupported, nothing is left."""
    real_link = os.link

    def no_link(src: object, dst: object) -> None:
        raise OSError(errno.EPERM, "Operation not permitted")

    monkeypatch.setattr(os, "link", no_link)
    try:
        with pytest.raises(TargetNotSupported):
            encrypt_pdf(plain_pdf, PW)
    finally:
        monkeypatch.setattr(os, "link", real_link)

    assert not plain_pdf.with_name("vertrag_sec.pdf").exists()
    assert leftovers(plain_pdf.parent) == []


def test_other_link_errors_are_reported_as_oserror(
    plain_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unexpected link error stays an OSError and is not swallowed."""

    def broken_link(src: object, dst: object) -> None:
        raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(os, "link", broken_link)

    with pytest.raises(OSError) as info:
        encrypt_pdf(plain_pdf, PW)

    assert info.value.errno == errno.EIO
    assert leftovers(plain_pdf.parent) == []


def test_unremovable_temporary_file_is_a_warning(
    plain_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F16: after the link the file counts as done; the leftover is a warning."""
    real_unlink = Path.unlink

    def stubborn_unlink(self: Path, missing_ok: bool = False) -> None:
        if self.name.startswith(".pdfsec-"):
            raise OSError(errno.EACCES, "Permission denied")
        real_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", stubborn_unlink)

    result = encrypt_pdf(plain_pdf, PW)

    assert result.target.exists()
    assert result.warning is not None
    assert "Temporäre Datei konnte nicht entfernt werden" in result.warning


def blank_user_pdf(tmp_path: Path) -> Path:
    """A PDF that is encrypted but opens without any password."""
    path = tmp_path / "offen_geschuetzt.pdf"
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(200, 200))
    pdf.save(
        path,
        encryption=pikepdf.Encryption(owner="besitzer-geheim", user="", R=6, aes=True),
    )
    pdf.close()
    return path


def test_encrypt_refuses_pdf_with_blank_user_password(tmp_path: Path) -> None:
    """F10: a PDF that opens freely but is encrypted is still refused."""
    source = blank_user_pdf(tmp_path)

    with pytest.raises(AlreadyEncrypted):
        encrypt_pdf(source, PW)

    assert not source.with_name("offen_geschuetzt_sec.pdf").exists()


def test_decrypt_non_pdf(text_file: Path) -> None:
    """F15: decrypt reports a text file as not a PDF."""
    with pytest.raises(InvalidPdf) as info:
        decrypt_pdf(text_file, PW)

    assert info.value.reason == "not_a_pdf"


def test_decrypt_with_existing_target(plain_pdf: Path) -> None:
    """F9: decrypt never overwrites an existing _open file."""
    protected = encrypt_pdf(plain_pdf, PW).target
    existing = protected.with_name("vertrag_sec_open.pdf")
    existing.write_bytes(b"alte Datei")
    before = file_hash(existing)

    with pytest.raises(OutputExists):
        decrypt_pdf(protected, PW)

    assert file_hash(existing) == before


def test_publish_loses_the_race_cleanly(plain_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """F9: a file created between pre-check and link is not replaced."""
    calls: list[int] = []

    def racing_link(src: object, dst: object) -> None:
        calls.append(1)
        raise FileExistsError(errno.EEXIST, "File exists")

    monkeypatch.setattr(os, "link", racing_link)

    with pytest.raises(OutputExists):
        encrypt_pdf(plain_pdf, PW)

    assert calls == [1]
    assert not plain_pdf.with_name("vertrag_sec.pdf").exists()
    assert leftovers(plain_pdf.parent) == []


def test_verify_encrypted_rejects_blank_user_password_file(tmp_path: Path) -> None:
    """F17: an output that opens without a password fails, even if marked encrypted."""
    source = blank_user_pdf(tmp_path)

    with pytest.raises(VerificationFailed):
        core._verify_encrypted(source, PW)


def test_verify_open_rejects_blank_user_password_file(tmp_path: Path) -> None:
    """F18: a file that still opens without a password fails the check."""
    source = blank_user_pdf(tmp_path)

    with pytest.raises(VerificationFailed):
        core._verify_open(source)


def test_decrypt_file_with_blank_user_password(tmp_path: Path) -> None:
    """F11: a file that opens freely but is encrypted can still be decrypted."""
    source = blank_user_pdf(tmp_path)

    result = decrypt_pdf(source, "beliebig")

    with pikepdf.open(result.target) as pdf:
        assert not pdf.is_encrypted
    assert result.warning is None
