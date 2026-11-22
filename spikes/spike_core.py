"""Spikes SP1, SP3 and SP2 from the SPEC. Run: uv run python spikes/spike_core.py"""

from __future__ import annotations

import os
import resource
import tempfile
import time
from pathlib import Path

import pikepdf

PASSWORD = "spike-2026"


def make_pdf(path: Path, pages: int = 1) -> Path:
    pdf = pikepdf.Pdf.new()
    for _ in range(pages):
        pdf.add_blank_page(page_size=(200, 200))
    pdf.save(path)
    pdf.close()
    return path


def sp1_save_over_existing_empty_file(directory: Path) -> None:
    """SP1: does Pdf.save() write into an existing empty file from mkstemp?"""
    source = make_pdf(directory / "sp1.pdf")
    fd, name = tempfile.mkstemp(dir=directory, prefix=".pdfsec-", suffix=".pdf")
    os.close(fd)
    tmp = Path(name)
    try:
        with pikepdf.open(source) as pdf:
            pdf.save(
                tmp,
                encryption=pikepdf.Encryption(owner=PASSWORD, user=PASSWORD, R=6, aes=True),
            )
        with pikepdf.open(tmp, password=PASSWORD) as check:
            print(f"SP1: ok, is_encrypted={check.is_encrypted}, size={tmp.stat().st_size}")
    except Exception as exc:  # noqa: BLE001 - the spike reports whatever happens
        print(f"SP1: FAILED {type(exc).__name__}: {exc}")
    finally:
        tmp.unlink(missing_ok=True)


def sp3_link_and_collision(directory: Path) -> None:
    """SP3: os.link to a new name works and fails when the target exists."""
    tmp = directory / ".pdfsec-link.pdf"
    tmp.write_bytes(b"inhalt")
    target = directory / "ziel.pdf"
    try:
        os.link(tmp, target)
        print(f"SP3: link ok, same inode={tmp.stat().st_ino == target.stat().st_ino}")
        try:
            os.link(tmp, target)
            print("SP3: FAILED - second link did not raise")
        except FileExistsError:
            print("SP3: collision raises FileExistsError as specified")
    finally:
        tmp.unlink(missing_ok=True)
        target.unlink(missing_ok=True)


def sp2_timing_and_memory(directory: Path, pages: int) -> None:
    """SP2: measured time and peak memory for one real-sized file."""
    source = make_pdf(directory / f"sp2-{pages}.pdf", pages=pages)
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    start = time.perf_counter()
    out = directory / f"sp2-{pages}-out.pdf"
    with pikepdf.open(source) as pdf:
        pdf.save(out, encryption=pikepdf.Encryption(owner=PASSWORD, user=PASSWORD, R=6))
    elapsed = time.perf_counter() - start
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    size = source.stat().st_size
    print(
        f"SP2: pages={pages} size={size / 1024:.1f} KiB "
        f"time={elapsed * 1000:.1f} ms peak_rss_delta={(after - before) / 1024:.1f} MiB"
    )


def main() -> None:
    with tempfile.TemporaryDirectory(dir=Path.cwd(), prefix="spike-") as raw:
        directory = Path(raw)
        sp1_save_over_existing_empty_file(directory)
        sp3_link_and_collision(directory)
        for pages in (1, 50, 500):
            sp2_timing_and_memory(directory, pages)


if __name__ == "__main__":
    main()
