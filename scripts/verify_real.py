"""Check what a real run produced, without using pdfsec code.

Usage:
    PDFSEC_PASSWORD=... uv run python scripts/verify_real.py <directory> [...]

For every PDF in the given directories:
  * `<stem>_sec.pdf` must open only with the password and report `is_encrypted`,
  * `<stem>_open.pdf` must open without a password and must not be encrypted,
  * file mode and page count are printed next to the input file's page count,
  * a `.pdfsec-*` leftover in the directory is a failure.

Run it twice (before and after a run) when you also want to see that the inputs
were not modified; the suite checks that with hashes in T23.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pikepdf

PASSWORD_ENV = "PDFSEC_PASSWORD"


def pages(path: Path, password: str) -> int:
    try:
        pdf = pikepdf.open(path)
    except pikepdf.PasswordError:
        pdf = pikepdf.open(path, password=password)
    with pdf:
        return len(pdf.pages)


def check(path: Path, password: str, *, expect_encrypted: bool) -> bool:
    mode = stat.S_IMODE(path.stat().st_mode)
    try:
        with pikepdf.open(path) as pdf:
            opens_without = True
            encrypted_flag = pdf.is_encrypted
            count = len(pdf.pages)
    except pikepdf.PasswordError:
        opens_without = False
        with pikepdf.open(path, password=password) as pdf:
            encrypted_flag = pdf.is_encrypted
            count = len(pdf.pages)

    suffix = "_sec.pdf" if expect_encrypted else "_open.pdf"
    source = path.with_name(path.name[: -len(suffix)] + ".pdf")

    print(f"{path.name}:")
    print(f"  Rechte            {oct(mode)}")
    print(f"  Seiten            {count}")
    if source.exists():
        print(f"  Quelle Seiten     {pages(source, password)}")
    print(f"  oeffnet ohne PW   {'ja' if opens_without else 'nein'}")
    print(f"  is_encrypted      {encrypted_flag}")
    print(f"  erwartet          {'verschluesselt' if expect_encrypted else 'offen'}")
    ok = (
        not opens_without and bool(encrypted_flag)
        if expect_encrypted
        else opens_without and not encrypted_flag
    )
    print(f"  Ergebnis          {'OK' if ok else 'FEHLER'}")
    return ok


def main(argv: list[str]) -> int:
    password = os.environ.get(PASSWORD_ENV)
    if not password:
        print(f"Bitte {PASSWORD_ENV} setzen.")
        return 2

    directories = [Path(argument) for argument in argv] or [Path.cwd()]
    results: list[bool] = []
    for directory in directories:
        print(f"Verzeichnis {directory}")
        for path in sorted(directory.glob("*.pdf")):
            if path.name.endswith("_sec.pdf"):
                results.append(check(path, password, expect_encrypted=True))
            elif path.name.endswith("_open.pdf"):
                results.append(check(path, password, expect_encrypted=False))
        leftovers = sorted(p.name for p in directory.iterdir() if p.name.startswith(".pdfsec-"))
        print(f"Temp-Dateien      {leftovers or 'keine'}")
        results.append(not leftovers)
        print()

    print(f"{sum(results)} von {len(results)} Pruefungen OK")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
