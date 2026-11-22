# EVIDENCE — pdfsec

Datum: 2026-11-22
SPEC: `SPEC.md`, Revision 4 freigegeben durch Frank am 2026-11-22; Revision 5
ergänzt nur die bei der Umsetzung sichtbar gewordenen Punkte
(`TargetNotSupported`, Feld `warning`, lesbare Erfolgszeile); Revision 6 setzt
Franks Meldung um, dass ein Pfad nicht in das Dateifeld eingefügt werden konnte
(neue Anforderung F29).

Quellstand: kein Commit (Repo ohne Historie). Prüfsummen der Quellen:

| Datei | SHA-256 |
|---|---|
| `src/pdfsec/core.py` | `7df9ab5849a09598fbf80d19591bdfc6eb089d72d68d360ffd5a4759f9cce3b1` |
| `src/pdfsec/tui.py` | `a5cff612645c5ceedc81080b0e8685c0ed9d3c1af8a7e204e8e475d4df63a701` |
| `src/pdfsec/clipboard.py` | `dcfa0961310d53dcbece917ac28cb2aaf5ab68fd916b456ae1b2a5736468eaac` |
| `src/pdfsec/__init__.py` | `af9156e2826af51d06217bcd7cbce517eeeb1f5b38676317881bc6043b696b85` |
| `pyproject.toml` | `59c0987c96567587602713de06761f27cd37a3c4eb160e55c7a04a4efafea09c` |

Alle Ergebnisse unten stammen aus Läufen nach der letzten Codeänderung.

## 1. Anforderungen und Nachweise

| Anforderung | Test | Ergebnis |
|---|---|---|
| F1, F23, F24 | T20, `tests/test_entry.py` | grün |
| F2, F3 | T15 | grün |
| F4, F5 | T16, T19 | grün |
| F6 | T16, T17, T24 | grün |
| F7, F15 | T7, T18, `test_decrypt_non_pdf` | grün |
| F8 | T9 | grün |
| F9 | T4, T21, `test_publish_loses_the_race_cleanly`, `test_decrypt_with_existing_target` | grün |
| F10 | T1, T5, `test_encrypt_refuses_pdf_with_blank_user_password` | grün |
| F11, F18 | T10, `test_decrypt_file_with_blank_user_password` | grün |
| F12 | T11 | grün |
| F13 | T12 | grün |
| F14 | T3, T17 | grün |
| F16 | T1, T8, T13, T14, `test_unremovable_temporary_file_is_a_warning` | grün |
| F17 | T2, `test_verify_encrypted_rejects_blank_user_password_file`, `test_verify_encrypted_rejects_plain_file` | grün |
| F19 | T13, T14 | grün |
| F20, F21, F22 | T18, T21, T22, T24 | grün |
| F25 | T17, T19 | grün |
| F26 | T1, T10, `test_detail_names_target_pages_and_warning` | grün |
| F27 | T6 | grün |
| F28 (README) | Datei `README.md`, Abschnitte „Limits“, „Install and run“ | vorhanden |
| F29 (Strg+V) | T25, T26, T27, T28 | grün, zusätzlich echter Lauf (Abschnitt 5) |
| IN1 (kein Netz, kein Unterprozess) | `ruff`/`mypy` sauber; kein Import von `socket`, `subprocess`, `urllib`, `requests` in `src/`; Zwischenablage über `tkinter` | geprüft |
| IN2 (Eingabe unverändert) | T23 | grün |
| IN4 (alles Deutsch) | T15, T20; Footer zeigt nur „Beenden“ (`ENABLE_COMMAND_PALETTE = False`) | grün |

## 2. Gauntlet

| Stufe | Befehl | Ergebnis | Log |
|---|---|---|---|
| Testsuite | `uv run pytest` | 50 passed, 0 failed, 10,9 s | `evidence/pytest.log` |
| Lint | `uv run ruff check .` | All checks passed | `evidence/ruff.log` |
| Format | `uv run ruff format --check .` | 19 files already formatted | `evidence/ruff.log` |
| Typen | `uv run mypy` (strict) | Success: no issues found in 12 source files | `evidence/mypy.log` |
| Coverage | `uv run --with coverage coverage run -m pytest` | 821 Anweisungen, 3 nicht ausgeführt, 99 % gesamt; `tui.py` 100 %, `clipboard.py` 100 %, `core.py` 98 % | `evidence/coverage.log` |
| Mutation (manuell) | `uv run python scripts/mutate.py` | 6 von 6 Mutanten getötet | `evidence/mutation.log` |
| Echter Lauf | tmux, 80×24, `uv run pdfsec` | siehe Abschnitte 4 und 5 | `evidence/tui-*.txt` |
| Unabhängige Prüfung | `PDFSEC_PASSWORD=... uv run python scripts/verify_real.py <dir>` | 4 von 4 Prüfungen OK | `evidence/real-verification.log` |

Mutation im Einzelnen (alle getötet):

| Mutante | Tötender Test |
|---|---|
| leeres Passwort wird durchgelassen | T3, T17 |
| Zielnamen vertauscht (`_sec`/`_open`) | T1, T9 und weitere (9 Fehlschläge) |
| `os.replace` statt `os.link` | T4, T21 und weitere (4 Fehlschläge) |
| Prüfung meldet „öffnet ohne Passwort“ nicht | `test_verify_encrypted_rejects_blank_user_password_file` |
| Prüfung hält verschlüsselte Ausgabe für entschlüsselt | `test_verify_open_rejects_protected_file` |
| Statuszeile zählt einen Fehler zu viel | T18, T21 und weitere (6 Fehlschläge) |

## 3. Spikes

| Spike | Ergebnis | Log |
|---|---|---|
| SP1 | `Pdf.save()` schreibt in eine vorhandene, leere `mkstemp`-Datei; Ergebnis ist verschlüsselt (is_encrypted=True) | `evidence/spikes.log` |
| SP3 | `os.link` im Zielordner gelingt (gleiche Inode), zweiter Link scheitert mit `FileExistsError` | `evidence/spikes.log` |
| SP2 (synthetisch) | 1 Seite 13,2 ms; 50 Seiten 13,4 ms; 500 Seiten 20,4 ms | `evidence/spikes.log` |
| SP2 (echte Datei) | 13,35 MiB, 9 Seiten: 150 ms, RSS-Zuwachs 5,3 MiB | `evidence/sp2-real.log` |

Die Quelle der echten Messung ist die größte PDF-Datei aus dem Dokumente-Ordner
(Dateiname im Log, Pfad gekürzt). Die Kopie wurde nach der Messung gelöscht.

## 4. Echte Läufe (80×24, tmux)

| Lauf | Eingabe | Ergebnis | Nachweis |
|---|---|---|---|
| Verschlüsseln, Batch | 2 echte PDF-Dateien | „2 von 2 fertig, 0 Fehler“, zwei `_sec.pdf` mit Modus 0600 | `evidence/tui-run-batch.txt` |
| Entschlüsseln | `gasthaus_sec.pdf` | „1 von 1 fertig, 0 Fehler“, `gasthaus_sec_open.pdf` | `evidence/tui-run-decrypt.txt` |
| Startbildschirm | — | Layout passt in 80×24, alle Texte Deutsch | `evidence/tui-start-80x24.txt` |

Unabhängige Prüfung der Ausgabedateien ohne pdfsec-Code (`scripts/verify_real.py`):

| Datei | Rechte | Seiten | öffnet ohne Passwort | is_encrypted | Ergebnis |
|---|---|---|---|---|---|
| `gasthaus_sec.pdf` | 0600 | 2 (Quelle 2) | nein | True | OK |
| `woerterbuch_sec.pdf` | 0600 | 1 (Quelle 1) | nein | True | OK |
| `gasthaus_sec_open.pdf` | 0600 | 2 (Quelle 2) | ja | False | OK |

Die Eingaben wurden nur lesend geöffnet; dass ihr Hash unverändert bleibt, prüft
T23 im Test. Im Zielordner blieb keine `.pdfsec-*`-Datei liegen.

## 5. Zwischenablage (F29, gemeldeter Fehler)

Vorher: `Strg+V` tat nichts. Textual schickt dafür eine OSC-52-Abfrage an das
Terminal; viele Terminals beantworten sie nicht, und der Nutzer sieht keine
Reaktion. Nur das Terminal-Einfügen (`Strg+Umschalt+V`, Mittelklick) kam an.

Jetzt liest `src/pdfsec/clipboard.py` die Zwischenablage über `tkinter` aus dem
Display-Server (kein Unterprozess, IN1 bleibt gültig) und fügt sie in das Feld
mit dem Fokus ein. Ohne lesbare Zwischenablage nennt die Statuszeile den
Ausweg.

| Prüfung | Ergebnis | Nachweis |
|---|---|---|
| `Strg+V` in die Dateiliste, echter Terminallauf | Pfad erscheint im Feld | `evidence/tui-paste-ctrl-v.txt` |
| `Strg+V` in das Passwortfeld, echter Terminallauf | Passwort erscheint nach dem Sichtbar-Schalter im Klartext | `evidence/tui-paste-password.txt` |
| Kein Tkinter / kein Display / leer | `read_clipboard()` gibt `None`, Hinweis in der Statuszeile | T27, T28 |
| Fokus auf einem Knopf | Einfügen landet in der Dateiliste | `test_paste_with_button_focused_goes_to_path_list` |

Nebenbei behoben: der Sichtbar-Schalter war bei 80 Spalten auf „Passwort“
abgeschnitten; er hat jetzt eine feste Breite von 20 Zeichen und zeigt
„Passwort anzeigen“ beziehungsweise „Passwort verbergen“ vollständig.

Der rote Lauf vor der Umsetzung liegt in `evidence/red-paste.log` (3
Fehlschläge, `AttributeError: read_clipboard`).

## 6. Nachträglich ergänzte Tests (kein RED beobachtet)

- `tests/test_core.py`: `test_verify_encrypted_rejects_plain_file`,
  `test_verify_open_rejects_protected_file`, `test_target_directory_without_hardlinks`,
  `test_other_link_errors_are_reported_as_oserror`,
  `test_unremovable_temporary_file_is_a_warning`, `blank_user_pdf` und die drei
  Tests darauf, `test_publish_loses_the_race_cleanly`,
  `test_decrypt_file_with_blank_user_password`.
- `tests/test_messages.py` (vollständig), `tests/test_entry.py` (vollständig).
- `tests/test_clipboard.py` (vollständig, mit Ersatz für Tk),
  `tests/test_paste.py::test_paste_with_button_focused_goes_to_path_list`.

Der RED-Lauf der ursprünglichen Kriterien liegt in `evidence/red-core.log`
(17 Fehlschläge, alle `NotImplementedError`), `evidence/red-tui.log`
(10 Fehlschläge, alle `NotImplementedError`) und `evidence/red-paste.log`.

## 7. Nicht gelaufene Stufen und Grenzen

| Punkt | Warum | Folge |
|---|---|---|
| Property-basierte Tests | `hypothesis` ist nicht Abhängigkeit der SPEC und wurde nicht ergänzt. | Keine systematische Eingabefläche; die Randfälle sind als Beispiele getestet. |
| Randomisierte Testreihenfolge | `pytest-randomly` nicht installiert. | Reihenfolgeabhängigkeit nicht ausgeschlossen; die Tests teilen keinen Zustand außer `tmp_path`. |
| CI | Kein Remote, kein Workflow verlangt. | Der Nachweis beruht auf den Logs in `evidence/`. |
| `core.py` Zeilen 159–160 | Zweiter Öffnungsversuch mit `PdfError`: nur erreichbar, wenn dieselbe Datei erst `PasswordError` und dann einen anderen PDF-Fehler liefert. | Defensive Zeile, nicht testbar ohne Fälschung der Bibliothek. |
| `core.py` Zeile 192 | Prüfung „öffnet mit Passwort, meldet aber nicht verschlüsselt“: widersprüchlich, praktisch unerreichbar. | Bleibt als Sicherheitsnetz stehen. |
| Zwischenablage | Braucht einen Display-Server mit X11/XWayland und ein Python mit `tkinter`. Reines Wayland ohne XWayland liefert `None`. | Hinweis in der Statuszeile, Terminal-Einfügen bleibt möglich (RIS13). |
| 80 Spalten | Lange Pfade werden in der Spalte „Datei“ abgeschnitten; die Erfolgszeile beginnt deshalb mit dem Zielnamen. | Bei schmalem Terminal ist der volle Pfad nicht sichtbar; die Datei liegt im Ordner der Eingabe. |
| SIGKILL/Stromausfall | Die temporäre Datei kann liegen bleiben. | In `README.md` und RIS3 benannt; die Anwendung löscht keine fremden Dateien. |
| Laufender Batch | Kein Abbruchknopf; `q` beendet die App und damit den Lauf. | F23 sagt das ausdrücklich. |
