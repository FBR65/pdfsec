"""Manual mutation run for the pdfsec gauntlet.

Applies one mutant at a time, runs the suite, restores the file from a snapshot
and reports whether the suite killed it. An anchor that is not found is an
error, never a pass.

Usage: uv run python scripts/mutate.py
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MUTANTS = [
    (
        "leeres Passwort wird durchgelassen",
        "src/pdfsec/core.py",
        "if not password:\n        raise EmptyPassword",
        "if password is None:\n        raise EmptyPassword",
    ),
    (
        "Zielnamen vertauscht",
        "src/pdfsec/core.py",
        'suffix = "_sec" if encrypt else "_open"',
        'suffix = "_open" if encrypt else "_sec"',
    ),
    (
        "os.replace statt os.link (ueberschreibt still)",
        "src/pdfsec/core.py",
        "os.link(temporary, target)",
        "os.replace(temporary, target)",
    ),
    (
        "Pruefung: Datei ohne Passwort oeffnet, wird nicht gemeldet",
        "src/pdfsec/core.py",
        "    else:\n        raise VerificationFailed(path.name)\n"
        "    with pikepdf.open(path, password=password)",
        "    else:\n        pass\n    with pikepdf.open(path, password=password)",
    ),
    (
        "Pruefung: verschluesselte Ausgabe gilt als entschluesselt",
        "src/pdfsec/core.py",
        "    except pikepdf.PasswordError as exc:\n"
        "        raise VerificationFailed(path.name) from exc",
        "    except pikepdf.PasswordError:\n        pass",
    ),
    (
        "Statuszeile zaehlt einen Fehler zu viel",
        "src/pdfsec/tui.py",
        'f"{done} von {len(lines)} fertig, {failed} Fehler"',
        'f"{done} von {len(lines)} fertig, {failed + 1} Fehler"',
    ),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    survivors = 0
    for name, relative, old, new in MUTANTS:
        path = ROOT / relative
        backup = path.with_suffix(path.suffix + ".orig")
        shutil.copy2(path, backup)
        before = digest(path)
        source = path.read_text(encoding="utf-8")
        if source.count(old) != 1:
            print(f"ERROR anchor not found exactly once: {name}")
            shutil.move(backup, path)
            return 2
        path.write_text(source.replace(old, new), encoding="utf-8")
        try:
            run = subprocess.run(
                ["uv", "run", "pytest", "-q", "--no-header", "-rN"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=600,
            )
            killed = run.returncode != 0
            last = (run.stdout.strip().splitlines() or ["<no output>"])[-1]
        finally:
            shutil.move(backup, path)
        if digest(path) != before:
            print(f"ERROR restore failed for {relative}")
            return 3
        print(f"{'KILLED  ' if killed else 'SURVIVED'} {name}  [{last}]")
        if not killed:
            survivors += 1
    print(f"\n{len(MUTANTS) - survivors}/{len(MUTANTS)} Mutanten getoetet")
    return 0 if survivors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
