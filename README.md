# pdfsec

A terminal application that puts a password on PDF files and removes it again.
Two fields and one button instead of a command line, so the password never
lands in your shell history.

Built with [pikepdf](https://pikepdf.readthedocs.io/) (qpdf) and
[Textual](https://textual.textualize.io/). Linux and macOS.

## What it does

| Mode | Input | Output |
|---|---|---|
| Encrypt | a PDF without password protection | `<stem>_sec.pdf`, same directory as the input |
| Decrypt | a password-protected PDF | `<stem>_open.pdf`, same directory as the input |

* AES-256, security handler revision 6, metadata encrypted.
* Several files per run: one path per line, one password for the whole run.
  A failing file becomes an error row and the remaining files still run.
* The output is written to a temporary file, then checked (opens with the
  password, does not open without it), then hard-linked to its final name.
  An existing target is never replaced, and the input is only ever opened
  read-only.

## Sample screen

Paths shortened for readability; the real layout was captured at 80×24 in
`evidence/tui-run-batch.txt`.

```text
PDFSec — PDF verschlüsseln und entschlüsseln
 Modus
 ▊ ▐●▌ Verschlüsseln
 ▊ ▐●▌ Entschlüsseln
 PDF-Dateien (eine pro Zeile)
 ╭──────────────────────────────────────────────────────────────────────╮
 │ ~/dokumente/vertrag.pdf                                              │
 │ ~/dokumente/anlage.pdf                                               │
 ╰──────────────────────────────────────────────────────────────────────╯
 Passwort
 ▊  ••••••••••••••••••  ▎  Passwort anzeigen  ▎  Start  ▎
 ╭──────────────────────────────────────────────────────────────────────╮
 │ Datei          Ergebnis   Ziel / Meldung                             │
 │ ~/dokumente…   Fertig     vertrag_sec.pdf — ~/dokumente (5 Seiten)   │
 │ ~/dokumente…   Fertig     anlage_sec.pdf  — ~/dokumente (1 Seite)    │
 ╰──────────────────────────────────────────────────────────────────────╯
 2 von 2 fertig, 0 Fehler
  ^q Beenden
```

The interface is German, including the key hints.

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.12 | `pyproject.toml` pins it; `uv` installs it if needed |
| [uv](https://docs.astral.sh/uv/) | `uv sync` resolves and installs everything |
| A terminal of at least 80×24 | Layout is checked against that size |
| A display server for `Ctrl+V` | Clipboard is read through `tkinter` (X11/XWayland); without it use `Ctrl+Shift+V` |

## Install and run

```bash
git clone git@github.com:FBR65/pdfsec.git
cd pdfsec
uv sync
uv run pdfsec
```

## Keys

| Key | Action |
|---|---|
| `Tab` / `Shift+Tab` | Move focus |
| `Up` / `Down` then `Space` | Choose mode in the mode switch |
| `Ctrl+V` | Paste the clipboard into the focused field |
| `Ctrl+Shift+V` | Terminal paste (works even when the clipboard cannot be read) |
| `Enter` on **Start** | Run |
| `q` / `Ctrl+Q` | Quit; a running batch ends with the app |

Password field: masked by default. The button **Passwort anzeigen** shows the
typed value, so a typo is visible before the run; the field is cleared and
masked again when a run starts. The value never appears in an error message, in
the result table or in a log file.

## Safety design

| Property | How |
|---|---|
| No data loss on failure | Output goes to a `.pdfsec-*` file in the target directory first; on any error it is deleted |
| No overwrite | The finished file is attached with `os.link`, which fails with `FileExistsError` if the name exists — no window between check and write |
| Verified output | After writing, the tool opens the file with the password and checks that it does *not* open without it (decrypt mode: the reverse) |
| Input untouched | The input is opened read-only; a test compares its hash before and after every run, including failures |
| No subprocess, no network | Everything is in-process; the clipboard is read through `tkinter` |

Failure modes that are named and accepted: a hard kill or power loss can leave
a `.pdfsec-*.pdf` behind (the tool never deletes files it did not create), and
the decrypt mode writes an unprotected file by design.

## Limits

PDF password protection is weaker than it looks. These limits come from the PDF
format, not from this tool (background:
[pikepdf — PDF security](https://pikepdf.readthedocs.io/en/latest/topics/security.html)):

| Limit | Consequence |
|---|---|
| Unlimited offline guessing | An attacker holding the file can try passwords without rate limit or lockout. A short password stays a weak password. |
| No integrity protection | AES-CBC in PDF is malleable; encryption proves neither authorship nor that the file was unchanged. |
| Either password decrypts everything | The user password and the owner password both open the full document. |
| Permission bits are advisory | Viewers may ignore "no printing" or "no copying". This tool does not set them. |
| No recovery | A forgotten password cannot be restored. There is no back door. |

## Development

```bash
uv run pytest                                    # 50 tests: core + headless TUI
uv run ruff check .                              # lint
uv run mypy                                      # types (strict)
uv run --with coverage coverage run -m pytest    # coverage
uv run python scripts/mutate.py                  # manual mutation run
PDFSEC_PASSWORD=… uv run python scripts/verify_real.py <dir>   # check real outputs
```

Last verified state: 50 tests green, `ruff` and `mypy --strict` clean, 99 %
line coverage, 6/6 hand-written mutants killed. The numbers and the raw logs
are in `evidence/EVIDENCE.md`.

## Repository layout

| Path | Content |
|---|---|
| `src/pdfsec/core.py` | Encrypt/decrypt one file: exceptions, verification, atomic publish. No UI. |
| `src/pdfsec/tui.py` | The Textual app: mode switch, path list, password field, result table |
| `src/pdfsec/clipboard.py` | Clipboard read through `tkinter`, returns `None` on any failure |
| `tests/` | Unit tests for core, clipboard and messages; headless TUI tests |
| `scripts/` | Mutation run, real-output verification, timing measurement |
| `spikes/` | Throwaway probes for `mkstemp` + `save`, `os.link`, timing |
| `evidence/` | Test/lint/coverage/mutation logs and screen captures of real runs |
| `SPEC.md` | Behaviour contract (German), approved before the code was written |

## License

MIT — see [LICENSE](LICENSE).
