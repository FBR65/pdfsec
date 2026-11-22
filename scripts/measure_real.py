"""SP2: measured time and memory on a real PDF from the user's documents.

Copies the largest PDF found under ~/Dokumente into the scratch directory and
encrypts the copy with the real core function.

Usage: uv run python scripts/measure_real.py
"""

from __future__ import annotations

import resource
import shutil
import time
from pathlib import Path

from pdfsec.core import encrypt_pdf

DOCUMENTS = Path.home() / "Dokumente"
SCRATCH = Path.home() / ".hermes/cache/scratch/pdfsec-real"
PASSWORD = "Geheim-2026-pruefung"


def largest_pdf() -> Path:
    candidates = [p for p in DOCUMENTS.rglob("*.pdf") if p.is_file()]
    return max(candidates, key=lambda p: p.stat().st_size)


def rss_mib() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def main() -> None:
    source = largest_pdf()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    copy = SCRATCH / f"messung_{source.name}"
    shutil.copy2(source, copy)

    before_rss = rss_mib()
    start = time.perf_counter()
    result = encrypt_pdf(copy, PASSWORD)
    elapsed = time.perf_counter() - start
    after_rss = rss_mib()

    print(f"Quelle      (Dokumente) {source.name}")
    print(f"Groesse     {copy.stat().st_size / 1024 / 1024:.2f} MiB")
    print(f"Seiten      {result.pages}")
    print(f"Ziel        {result.target} ({result.target.stat().st_size / 1024 / 1024:.2f} MiB)")
    print(f"Zeit        {elapsed * 1000:.0f} ms")
    print(f"RSS vorher  {before_rss:.1f} MiB")
    print(f"RSS nachher {after_rss:.1f} MiB")
    print(f"Zuwachs     {after_rss - before_rss:.1f} MiB")


if __name__ == "__main__":
    main()
