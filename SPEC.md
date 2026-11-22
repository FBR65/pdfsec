# SPEC pdfsec — PDF verschlüsseln und entschlüsseln (TUI)

Status: freigegeben (Revision 4, Frank, 2026-11-22)
Datum: 2026-11-22
Repo: ~/Dokumente/dev/PDFSec (Branch master)
Vorgänger: Revision 1 und 2, Review-Berichte unter `~/.hermes/reviews/PDFSec/`

## 1. Problem

Frank will PDF-Dateien mit einem Passwort schützen und den Schutz wieder
entfernen können. Das Werkzeug soll ohne Kommandozeilen-Passwort arbeiten, weil
das Passwort sonst in der Shell-History landet. Eine TUI zeigt Dateien,
Passwort und Ergebnis. Mehrere Dateien sollen in einem Lauf verarbeitet werden
können.

## 2. Ziele (Z)

| ID | Ziel | Prüfbar durch |
|---|---|---|
| Z1 | Eine PDF-Datei wird mit einem Passwort verschlüsselt und als neue Datei gespeichert. | F9, F10, F26 |
| Z2 | Eine verschlüsselte PDF wird mit ihrem Passwort entschlüsselt und als neue Datei gespeichert. | F11, F18 |
| Z3 | Die Bedienung erfolgt in einer TUI auf Deutsch. | F2, F3, F4, F24 |
| Z4 | Das Passwort kann per Klick sichtbar gemacht werden, damit ein Schreibfehler auffällt. | F4 |
| Z5 | Das Passwort erscheint nicht in Prozessargumenten, in der Shell-History und in keiner Ausgabe. | F5 |
| Z6 | Mehrere Dateien laufen in einem Batch; ein Fehler stoppt die übrigen Dateien nicht. | F6, F20, F21 |
| Z7 | Die Anwendung prüft nach dem Speichern, ob die Ausgabe den gewünschten Schutz-Zustand hat. | F17, F18, F19 |
| Z8 | Ein Fehler zerstört keine Datei: die Eingabe bleibt unverändert, eine halbe Ausgabe bleibt nicht liegen, eine vorhandene Zieldatei wird nicht überschrieben. | F9, F16, T23 |

## 3. Entscheidungen (E)

| ID | Entscheidung | Quelle | Betroffene Abschnitte |
|---|---|---|---|
| E1 | Im Modus Verschlüsseln ist das Ergebnis eine neue Datei im Ordner der Eingabe, benannt `<stamm>_sec.pdf`. Den Namen je Modus legt F8 fest. Es gibt kein Zielfeld. Das Original wird nie geschrieben. | Frank, 2026-11-22 | F8, E8 |
| E2 | Die Anwendung kann auch entschlüsseln: Moduswahl in der TUI. | Frank, 2026-11-22 | F11, F12, F13, F18 |
| E3 | Batch ist möglich: eine Pfadliste, ein Passwort pro Lauf. | Frank, 2026-11-22 | F6, F20, F21 |
| E4 | Ein Schalter „Passwort anzeigen“ ersetzt ein zweites Bestätigungsfeld. | Frank, 2026-11-22 | F4, ALT11 |
| E5 | `owner` und `user` erhalten denselben Wert. Grund: die pikepdf-Dokumentation nennt ein leeres Besitzer-Passwort nutzlos („setting a user password and leaving the owner password blank is useless“, Q2); ein zweiter Wert wäre ein zweites Geheimnis. | Autor, technische Begründung | F10, ALT7 |
| E6 | TUI-Framework: Textual. | Autor | Abschnitt 8, ALT2, ALT3, ALT4 |
| E7 | Überschreiben ist technisch ausgeschlossen: die geprüfte temporäre Datei wird per `os.link` auf den Zielnamen verlinkt. `FileExistsError` ist ein Fehler, kein Ersetzen. | Autor, Folge aus Z8 | F9, F16, RIS8, RIS12, ALT13 |
| E8 | Kein Zielfeld, weil eine Liste von Eingaben keinen einzelnen Zielnamen hat und E1 den Namen festlegt. | Autor, Folge aus E1 und E3 | F8 |
| E9 | Rechte-Beschränkungen sind nicht enthalten; alle Rechte bleiben erhalten. | Frank, 2026-11-22 | F10, N1, RIS1 |
| E10 | Die Ausgabe beim Entschlüsseln heißt `<stamm>_open.pdf`. | Frank, 2026-11-22 | F8, T9 |

## 4. Abgrenzung (N)

Die beiden früheren Fragen D3 und D5 sind entschieden: E9 (keine
Rechte-Beschränkungen) und E10 (Name `<stamm>_open.pdf`). Es gibt keine offene
Entscheidung mehr.

| ID | Nicht enthalten | Grund | Entscheidung |
|---|---|---|---|
| N1 | Rechte-Beschränkungen | Nicht verlangt, im PDF-Format nicht durchsetzbar. | E9 |
| N2 | Verzeichnis-Scan als Stapelquelle | Nicht verlangt; ein Scan verarbeitet Dateien, die Frank nicht genannt hat. | ALT12 |
| N3 | Netzwerk, Cloud, Mailversand | Nicht verlangt. Die Anwendung arbeitet nur lokal. | IN1 |
| N4 | Wiederherstellen eines vergessenen Passworts | PDF-Passwörter sind nicht umkehrbar; die Anwendung kann das nicht leisten. | RIS4 |

## 5. Anforderungen (F)

| ID | Anforderung | Nachweis |
|---|---|---|
| F1 | `uv run pdfsec` startet die TUI ohne Argumente. | T20 |
| F2 | Die TUI zeigt: Moduswahl (Verschlüsseln / Entschlüsseln), Dateiliste (mehrzeilig), Passwortfeld, Schalter „Passwort anzeigen“, Schaltfläche „Start“, Ergebnistabelle, Statuszeile, Fußzeile. | T15 |
| F3 | Das Passwortfeld ist verdeckt (`Input(password=True)`) und die Voreinstellung. | T15 |
| F4 | Der Schalter „Passwort anzeigen“ zeigt den Wert im Klartext; seine Beschriftung wechselt zu „Passwort verbergen“. Beim Start eines Laufs schaltet er auf verdeckt zurück. | T16 |
| F5 | Das Passwort wird nach dem Lauf aus dem Feld gelöscht. Es steht in keiner Fehlermeldung, in keiner Ergebnistabelle und in keiner Ausnahme, die die TUI anzeigt. Die Anwendung schreibt keine Logdatei. | T16, T19 |
| F6 | Die Dateiliste enthält eine Pfadangabe pro Zeile. Leerzeilen werden ignoriert. Ein Pfad, der mehrfach in der Liste steht, wird als Fehlerzeile „Datei ist mehrfach in der Liste.“ geführt. Mindestens eine Zeile ist nötig, sonst „Bitte mindestens eine Datei angeben.“ | T16, T17, T24 |
| F7 | Vor dem Lauf wird jede Zeile geprüft: Pfad vorhanden, reguläre Datei, lesbar. Eine fehlerhafte Zeile wird als Fehlerzeile geführt; die übrigen Zeilen laufen weiter. | T7, T18 |
| F8 | Der Zielpfad je Eingabe ist der Ordner der Eingabe mit dem Namen `<stamm>_sec.pdf` (Verschlüsseln) beziehungsweise `<stamm>_open.pdf` (Entschlüsseln, E10). Es gibt kein Zielfeld. | T9 |
| F9 | Existiert der Zielpfad, wird die Datei als Fehler „Zieldatei existiert bereits“ geführt und nicht angefasst. Die Prüfung ist atomar beim Anlegen (E7). | T4, T21 |
| F10 | Verschlüsseln: `pikepdf.open(pfad)`, Prüfung `is_encrypted` ist falsch, `save` mit `pikepdf.Encryption(owner=passwort, user=passwort, R=6, aes=True, metadata=True)`. `allow` wird nicht gesetzt; laut pikepdf-Dokumentation (Q1) bleiben damit alle Rechte erhalten. | T1 |
| F11 | Entschlüsseln: `pikepdf.open(pfad, password=passwort)`, danach `save` ohne `encryption`. | T10 |
| F12 | Falsches Passwort beim Entschlüsseln (`pikepdf.PasswordError`) ergibt „Passwort falsch.“ und keine Ausgabe. | T11 |
| F13 | Eine nicht verschlüsselte Datei im Modus Entschlüsseln ergibt „Die Datei ist nicht verschlüsselt.“ und keine Ausgabe. | T12 |
| F14 | Leeres Passwort wird in beiden Modi abgelehnt: „Bitte ein Passwort eingeben.“ Es wird nichts geschrieben. | T3, T17 |
| F15 | Keine lesbare PDF ergibt „Die Datei ist keine lesbare PDF-Datei.“ und keine Ausgabe. | T7 |
| F16 | Schreiben ist atomar: `mkstemp` im Zielordner (Modus 0600), Datei schließen, von pikepdf beschreiben lassen, prüfen (F17 bis F19), dann `os.link` auf den Zielnamen, dann die temporäre Datei löschen. Die Ausgabe behält Modus 0600. Scheitert das Löschen der temporären Datei erst nach dem Link, gilt die Datei als fertig; die Statuszeile nennt zusätzlich „Temporäre Datei konnte nicht entfernt werden: <name>“. Fehler vor dem Link löschen die temporäre Datei. Eingaben werden nur lesend geöffnet. | T1, T8, T13, T14 |
| F17 | Nachprüfung Verschlüsseln: die temporäre Datei öffnet sich mit dem Passwort, und ohne Passwort scheitert sie mit `pikepdf.PasswordError`. | T2 |
| F18 | Nachprüfung Entschlüsseln: die temporäre Datei öffnet sich ohne Passwort, `is_encrypted` ist falsch. | T10 |
| F19 | Scheitert eine Nachprüfung, wird `VerificationFailed` ausgelöst, die temporäre Datei gelöscht und „Die Prüfung der Ausgabe ist fehlgeschlagen. Es wurde nichts gespeichert.“ angezeigt. Diese Meldung gilt nur für Fehler vor dem Link; nach dem Link ist die Datei fertig (F16). | T13, T14 |
| F20 | Der Lauf arbeitet in einem Worker-Thread (`@work(thread=True)`). Die Dateien werden nacheinander geöffnet, geschrieben und geschlossen. Ein Fehler bei einer Datei beendet den Lauf der übrigen Dateien nicht. Der Worker ändert Widgets ausschließlich über `App.call_from_thread`. | T18, T22 |
| F21 | Die Ergebnistabelle hat eine Zeile je Eingabe: Pfad, Ergebnis („Fertig“ / „Fehler“), Zielpfad oder Meldung. Die Statuszeile zeigt „x von y fertig, z Fehler“. | T18, T21, T22 |
| F22 | Ein Lauf verwendet das Passwort aus dem Feld für alle Dateien. Es wird nicht je Datei gefragt. | T18 |
| F23 | `q` und `Strg+Q` beenden die TUI. Ein laufender Batch endet mit der App. | T20 |
| F24 | Die Fußzeile zeigt die Tastenkürzel auf Deutsch. | T20 |
| F25 | Jeder Fehler erscheint als deutsche Meldung. Die TUI bleibt danach bedienbar. | T17, T19 |
| F26 | Die Erfolgszeile je Datei nennt den absoluten Zielpfad und die Seitenzahl der Ausgabe. | T1, T10 |
| F27 | Passwörter mit Umlauten und Sonderzeichen funktionieren in beiden Modi. | T6 |
| F28 | Die README beschreibt Zweck, Bedienung und die Grenzen aus RIS1 und RIS4. Sprache: Englisch. | ST5 |
| F29 | `Strg+V` fügt den Text der System-Zwischenablage in das Feld mit dem Fokus ein: in die Dateiliste mehrzeilig, in das Passwortfeld einzeilig (Zeilenumbrüche werden zu Leerzeichen). Ist die Zwischenablage leer oder nicht lesbar, erscheint „Zwischenablage ist leer oder nicht lesbar. Im Terminal hilft Strg+Umschalt+V.“ und es wird nichts eingefügt. | T25, T26, T27 |

## 6. Annahmen (A)

| ID | Annahme | Wenn falsch |
|---|---|---|
| A1 | Linux, Python 3.12 über `uv` (`.python-version` = 3.12). | Andere Version: `requires-python` anpassen. |
| A2 | Terminal mit mindestens 80×24 Zeichen; das Layout ist darauf geprüft. | Kleinere Fenster: Text bricht um, Bedienung bleibt möglich, ungeprüft. |
| A3 | Frank hat Schreibrechte im Ordner der Eingaben. | Fehlende Rechte: Meldung aus F16, keine Datei. |
| A4 | Der Zielordner unterstützt Hardlinks. | Kein Hardlink: Fehlerzeile „Der Zielordner unterstützt kein atomares Anlegen.“ (RIS12), keine Ausgabe. |

## 7. Alternativen (ALT)

| ID | Alternative | Warum verworfen |
|---|---|---|
| ALT1 | CLI mit `getpass` | Verworfen, weil Frank eine TUI verlangt hat (Z3). Technisch zusätzlich schwach: kein Zustand, keine Pfadvorbelegung, eine Fehlermeldung beendet den Ablauf. |
| ALT2 | `questionary` oder `rich.prompt` | Verworfen. Beide stellen nur Fragen und beenden den Ablauf bei einem Fehler. Es fehlen Batch-Tabelle, Moduswahl und Worker; ein Fehler in Zeile 3 würde den ganzen Lauf beenden. |
| ALT3 | `prompt_toolkit` | Technisch möglich. Verworfen, weil Fokus, Statuszeile, Ergebnistabelle und Worker selbst gebaut werden müssten; Textual bringt diese Teile mit (`App`, `run_test`). |
| ALT4 | `urwid` | Verworfen. Ältere API ohne eingebaute Worker und ohne einfache asynchrone Tests. |
| ALT5 | Security-Handler-Revision 4 (AES-128) | Verworfen. Revision 6 ist stärker und laut pikepdf-Dokumentation (Q1) die Voreinstellung (`R=6`). |
| ALT6 | Revision 2 oder 3 (RC4) | Verworfen. RC4 gilt als gebrochen. |
| ALT7 | Eigener Besitzer-Passwort-Wert oder leerer Besitzer | Verworfen. Die pikepdf-Dokumentation (Q2) nennt einen leeren Besitzer nutzlos, und ein zweiter Wert wäre ein zweites Geheimnis (E5). |
| ALT8 | Verschlüsseln ohne Nachprüfung | Verworfen. Ohne Prüfung meldet die TUI Erfolg, auch wenn das Passwort nicht greift (RIS4). |
| ALT9 | Direkt auf den Zielpfad schreiben | Verworfen. Ein Abbruch hinterlässt eine halbe Datei. Deshalb temporäre Datei plus `os.link` (F16). |
| ALT10 | `qpdf` als Unterprozess oder `pypdf` statt pikepdf | Verworfen. `qpdf` als Unterprozess übergibt das Passwort als Argument oder über eine Pipe und verletzt Z5; `pypdf` deckt AES-256 nicht so direkt ab und gilt als langsamer. pikepdf ist die Bibliothek, die Frank genannt hat. |
| ALT11 | Zweites Passwortfeld zur Bestätigung | Verworfen. Zwei Felder verdoppeln die Tipparbeit und zeigen den Fehler nicht; der Sichtbar-Schalter zeigt den tatsächlichen Wert (E4). |
| ALT12 | Verzeichnis-Scan als Stapelquelle | Verworfen. Verarbeitet Dateien, die Frank nicht genannt hat, und braucht Filterregeln. Die Pfadliste ist explizit (N2). |
| ALT13 | Temporäre Datei plus `os.replace` | Verworfen. `os.replace` ersetzt ein vorhandenes Ziel still und bricht damit F9 und Z8. Ein vorab mit `O_EXCL` angelegtes Ziel hinterlässt bei einem Abbruch eine leere Datei am Zielnamen. `os.link` liefert beides: kein Überschreiben und kein leerer Zielname. Preis: Hardlink-Unterstützung nötig (RIS12). |

## 8. Architektur

| Datei | Inhalt |
|---|---|
| `src/pdfsec/__init__.py` | `main()` startet `PdfSecApp().run()`; Einstiegspunkt `pdfsec` aus pyproject.toml. |
| `src/pdfsec/core.py` | `encrypt_pdf(input_path, password) -> Result` und `decrypt_pdf(input_path, password) -> Result`. Reine Logik ohne Textual. Ausnahmen: `PdfSecError` mit `EmptyPassword`, `OutputExists`, `AlreadyEncrypted`, `NotEncrypted`, `InvalidPdf` (Feld `reason`), `WrongPassword`, `VerificationFailed`, `TargetNotSupported`. `Result` hat die Felder `source: Path`, `target: Path`, `pages: int`, `warning: str oder None`. |
| `src/pdfsec/tui.py` | `PdfSecApp(App)`: Moduswahl, Dateiliste, Passwortfeld, Sichtbar-Schalter, Start-Schaltfläche, Ergebnistabelle, Statuszeile, Worker, deutsche Texte. |
| `src/pdfsec/clipboard.py` | `read_clipboard() -> str oder None`: liest die System-Zwischenablage über `tkinter`, ohne Unterprozess. Jeder Fehler ergibt `None`. |
| `README.md` | Zweck, Bedienung, Grenzen (englisch). |
| `tests/test_core.py` | T1 bis T14, T23. |
| `tests/test_tui.py` | T15 bis T22, T24. |

Datenfluss: Die TUI liest Modus, Zeilen und Passwort. Sie prüft Passwort (F14),
Zeilen (F7) und doppelte Pfade (F6), setzt den Sichtbar-Schalter zurück (F4)
und startet den Worker. Der Worker ruft je Zeile `encrypt_pdf` oder
`decrypt_pdf` auf und gibt jede Ergebniszeile über `App.call_from_thread` an
die TUI. Erst nach dem letzten Ergebnis zeigt die Statuszeile die Summe, und
die TUI löscht das Passwort (F5).

Zielpfad-Bildung: `Path(pfad).with_name(Path(pfad).stem + "_sec.pdf")`
beziehungsweise `+ "_open.pdf"`, im Ordner der Eingabe.

## 9. Fehlerbehandlung

| Situation | Ausnahme | Meldung in der TUI |
|---|---|---|
| Passwort leer | `EmptyPassword` | „Bitte ein Passwort eingeben.“ |
| Zieldatei existiert | `OutputExists` | „Zieldatei existiert bereits.“ |
| Eingabe schon verschlüsselt (Modus Verschlüsseln) | `AlreadyEncrypted` | „Die Datei ist bereits verschlüsselt.“ |
| Eingabe nicht verschlüsselt (Modus Entschlüsseln) | `NotEncrypted` | „Die Datei ist nicht verschlüsselt.“ |
| Falsches Passwort (Modus Entschlüsseln) | `WrongPassword` | „Passwort falsch.“ |
| Pfad fehlt | `InvalidPdf(reason="not_found")` | „Die Datei wurde nicht gefunden.“ |
| Pfad ist keine reguläre Datei | `InvalidPdf(reason="not_a_file")` | „Der Pfad ist keine Datei.“ |
| Keine lesbare PDF | `InvalidPdf(reason="not_a_pdf")` | „Die Datei ist keine lesbare PDF-Datei.“ |
| Schreibfehler, Rechte | `OSError` | „Die Zieldatei konnte nicht geschrieben werden: <Grund>“ |
| Zielordner ohne Hardlink-Unterstützung | `TargetNotSupported` (bei `EPERM` oder `EXDEV`) | „Der Zielordner unterstützt kein atomares Anlegen: <Grund>“ |
| Nachprüfung fehlgeschlagen (vor dem Link) | `VerificationFailed` | „Die Prüfung der Ausgabe ist fehlgeschlagen. Es wurde nichts gespeichert.“ |
| Leere Dateiliste | — | „Bitte mindestens eine Datei angeben.“ |
| Pfad mehrfach in der Liste | — | „Datei ist mehrfach in der Liste.“ |
| Temporäre Datei nach dem Link nicht löschbar | — | Zeile „Fertig“ plus „Temporäre Datei konnte nicht entfernt werden: <name>“ |

## 10. Sicherheit und Risiken (RIS)

| ID | Risiko | Maßnahme | Grenze |
|---|---|---|---|
| RIS1 | PDF-Passwörter sind offline unbegrenzt ratbar; AES-CBC im PDF hat keine Integritätsprüfung; Rechte-Bits sind Empfehlungen an den Betrachter (Q2). | AES-256, Revision 6, Metadaten verschlüsselt (F10); Grenzen in der README (F28). | Formatbedingt nicht behebbar. |
| RIS2 | Passwort in Shell-History, Prozessliste, Ausgabe. | Nur im TUI-Feld, nie als Argument (F5); keine Logdatei. | Ein Abbild des Prozessspeichers ist nicht geschützt. |
| RIS3 | Halb geschriebene Datei, überschriebenes Original. | Temporäre Datei, `os.link`, Original nur lesend (F9, F16). | Ein hartes Ende (SIGKILL, Stromausfall) hinterlässt `.pdfsec-*.pdf` im Zielordner. Kein automatisches Löschen, weil die Anwendung keine fremden Dateien entfernt. |
| RIS4 | Tippfehler im Passwort erzeugt eine Datei mit unbekanntem Passwort. | Sichtbar-Schalter (F4), Nachprüfung mit demselben Wert (F17). | Die Nachprüfung erkennt nur, dass der Wert greift, nicht, dass er gemeint war. Ein vergessenes Passwort ist nicht wiederherstellbar (N4). |
| RIS5 | Große Datei blockiert die Oberfläche. | Worker-Thread (F20). | Kein Abbruchknopf; ein Lauf endet mit der letzten Datei. Messwert in SP2. |
| RIS6 | Speicherbedarf wächst mit der Dateigröße. | Dateien nacheinander verarbeiten und je Datei schließen (F20). | pikepdf hält das Dokument im Speicher; keine Obergrenze im Code. Getestete Größe aus SP2, darüber ungeprüft. |
| RIS7 | Passwort mit Umlauten schlägt fehl. | Test T6 in beiden Modi. | Keine. |
| RIS8 | Zwei Läufe schreiben dieselbe Zieldatei. | `os.link` scheitert mit `FileExistsError`, der zweite Lauf meldet „Zieldatei existiert bereits“ (F9). | Keine stille Überschreibung. |
| RIS9 | Sichtbares Passwort auf dem Bildschirm (Blick von außen). | Verdeckt als Voreinstellung, Rückschaltung beim Laufstart (F4). | Wer den Bildschirm sieht, solange der Schalter an ist, liest das Passwort. |
| RIS10 | Ein Fehler im Batch verhindert die übrigen Dateien. | Je Datei eine Ergebniszeile, Lauf geht weiter (F20, F21). | Kein Wiederholungslauf für Fehlerzeilen; Frank startet sie erneut. |
| RIS11 | Entschlüsselte Datei liegt ungeschützt auf der Platte. | Das ist der Zweck des Modus (E2). | Frank entscheidet über den Verbleib der Datei. |
| RIS12 | Der Zielordner unterstützt keine Hardlinks (Netz-Mount, manche Dateisysteme). `os.link` scheitert mit `EPERM` oder `EXDEV`. | Eigene Fehlerzeile, temporäre Datei wird gelöscht, Ziel bleibt unberührt (F16, A4). | Kein Ausweichverfahren, weil `os.replace` die Zusage aus Z8 bricht (ALT13). Frank wählt einen anderen Zielordner. |
| RIS13 | Die Zwischenablage ist nicht lesbar: reines Wayland ohne XWayland, kein `tkinter`, oder ein Besitzer, der nicht antwortet. | Hinweis in der Statuszeile (F29), Terminal-Einfügen `Strg+Umschalt+V` bleibt als Weg. | Kein Unterprozess als Ersatzweg, weil IN1 das ausschließt. |

## 11. Abhängigkeiten und Setup-Plan

| Paket | Version | Zweck | Lizenz |
|---|---|---|---|
| pikepdf | >=10.18,<11 | PDF lesen, verschlüsseln, entschlüsseln, schreiben | MPL-2.0 |
| textual | >=8.2,<9 | TUI | MIT |
| pytest | >=9 (dev) | Tests | MIT |
| pytest-asyncio | >=1 (dev) | TUI-Tests mit `run_test` | MIT |
| ruff | dev | Lint und Format | MIT |
| mypy | dev | Typprüfung | MIT |

Setup: `uv add pikepdf textual`, `uv add --dev pytest pytest-asyncio ruff mypy`.
Eintrag `pdfsec = "pdfsec:main"` bleibt. `asyncio_mode = "auto"` in der
pytest-Konfiguration. Kein `git init`; Checkpoint-Commits nur auf Wunsch von
Frank.

## 12. Tests (T)

| ID | Test | Datei | prüft |
|---|---|---|---|
| T1 | Verschlüsseln: Ausgabe entsteht, `is_encrypted` ist wahr, Öffnen mit Passwort gelingt, Seitenzahl gleich der Eingabe, Ausgabe hat Modus 0600. | tests/test_core.py | F10, F16, F26 |
| T2 | Ausgabe ohne Passwort: `pikepdf.PasswordError`. | tests/test_core.py | F17 |
| T3 | Leeres Passwort: `EmptyPassword`, keine Datei. | tests/test_core.py | F14 |
| T4 | Vorhandene Zieldatei: `OutputExists`, ihr Hash bleibt gleich. | tests/test_core.py | F9 |
| T5 | Verschlüsselte Eingabe im Modus Verschlüsseln: `AlreadyEncrypted`, keine Ausgabe. | tests/test_core.py | F10 |
| T6 | Passwort `Grüße-2026-äöüß`: Verschlüsseln und Entschlüsseln im Rundlauf. | tests/test_core.py | F27 |
| T7 | Textdatei als Eingabe: `InvalidPdf` mit `reason="not_a_pdf"`, keine temporäre Datei im Zielordner. | tests/test_core.py | F7, F15 |
| T8 | Zielordner ohne Schreibrecht: `OSError`, keine temporäre Datei, keine Ausgabe. | tests/test_core.py | F16 |
| T9 | Zielpfad-Bildung: `a.pdf` → `a_sec.pdf`, `b.PDF` → `b_sec.pdf`, `c_sec.pdf` im Modus Entschlüsseln → `c_sec_open.pdf`, jeweils im gleichen Ordner. | tests/test_core.py | F8, E10 |
| T10 | Entschlüsseln: Ausgabe entsteht, `is_encrypted` falsch, Öffnen ohne Passwort gelingt, Seitenzahl gleich. | tests/test_core.py | F11, F18, F26 |
| T11 | Falsches Passwort beim Entschlüsseln: `WrongPassword`, keine Ausgabe. | tests/test_core.py | F12 |
| T12 | Nicht verschlüsselte Datei im Modus Entschlüsseln: `NotEncrypted`, keine Ausgabe. | tests/test_core.py | F13 |
| T13 | Nachprüfung Verschlüsseln scheitert (Prüffunktion ersetzt): `VerificationFailed`, keine temporäre Datei, keine Ausgabe. | tests/test_core.py | F19 |
| T14 | Nachprüfung Entschlüsseln scheitert: `VerificationFailed`, keine temporäre Datei, keine Ausgabe. | tests/test_core.py | F19 |
| T15 | App startet headless: alle Widgets aus F2 vorhanden, Passwortfeld maskiert. | tests/test_tui.py | F2, F3 |
| T16 | Schalter zeigt das Passwort, Beschriftung wechselt, Start schaltet zurück und leert das Feld. | tests/test_tui.py | F4, F5, F6 |
| T17 | Leeres Passwort und leere Dateiliste: Meldungen aus F14 und F6, keine Datei. | tests/test_tui.py | F14, F25 |
| T18 | Batch mit drei Zeilen, eine davon defekt: zwei Erfolge, eine Fehlerzeile, Statuszeile „2 von 3 fertig, 1 Fehler“, Passwortfeld leer. | tests/test_tui.py | F20, F21, F22 |
| T19 | Nach einem Fehler ist die TUI bedienbar: zweiter Lauf gelingt. | tests/test_tui.py | F5, F25 |
| T20 | `q` beendet die App; die Fußzeile enthält deutsche Beschriftungen. | tests/test_tui.py | F1, F23, F24 |
| T21 | Vorhandene Zieldatei im Batch: Fehlerzeile „Zieldatei existiert bereits“, die andere Datei wird fertig. | tests/test_tui.py | F9, F21 |
| T22 | Der Aufruf von `encrypt_pdf` läuft nicht im Thread der Oberfläche; nach dem Lauf nennt die Statuszeile die Summe (Update über `call_from_thread`). | tests/test_tui.py | F20, F21 |
| T23 | Hash jeder Eingabedatei ist vor und nach `encrypt_pdf` und `decrypt_pdf` gleich, auch im Fehlerfall (falsches Passwort, vorhandene Zieldatei). | tests/test_core.py | IN2, Z8 |
| T24 | Doppelter Pfad in der Liste: Fehlerzeile „Datei ist mehrfach in der Liste.“, die Datei wird genau einmal verarbeitet. | tests/test_tui.py | F6 |
| T25 | `Strg+V` mit gefüllter Zwischenablage füllt die Dateiliste. | tests/test_paste.py | F29 |
| T26 | `Strg+V` im Passwortfeld fügt einzeilig ein (Zeilenumbrüche werden entfernt). | tests/test_paste.py | F29 |
| T27 | `Strg+V` ohne lesbare Zwischenablage zeigt den Hinweis und fügt nichts ein. | tests/test_paste.py | F29 |
| T28 | Ohne Tkinter oder ohne Display liefert der Zwischenablage-Leser `None` statt eines Fehlers. | tests/test_clipboard.py | F29, IN1 |

## 13. Phasen (ST)

| ID | Phase | Inhalt | Nachweis |
|---|---|---|---|
| ST0 | Setup | Abhängigkeiten, Projektgerüst, pytest-Konfiguration, leere Testdateien. | `uv run pytest` läuft und sammelt 0 Tests. |
| ST1 | Kern Verschlüsseln | Vor dem ersten Test SP1 und SP3 ausführen. Dann `core.py`: Ausnahmen, `Result`, `encrypt_pdf` mit RED, GREEN, REFACTOR. | T1 bis T9, T23 |
| ST2 | Kern Entschlüsseln | `decrypt_pdf`, Nachprüfung für beide Richtungen. RED, dann GREEN, dann REFACTOR. | T10 bis T14 |
| ST3 | TUI Einzeldatei | `tui.py`, `main()`, Moduswahl, Passwortfeld mit Schalter, Worker mit `call_from_thread`, Fehlermeldungen. | T15, T16, T17, T19, T20 |
| ST4 | Batch | Dateiliste, Ergebnistabelle, Statuszeile, doppelte Pfade, Weiterlaufen bei Fehlern. | T18, T21, T22, T24 |
| ST5 | Gauntlet und Nachweis | SP2 messen; pytest, ruff, mypy, manuelle Mutanten, echter Lauf auf echten PDF-Dateien in beiden Modi und im Batch, README, EVIDENCE. | EVIDENCE-Datei unter `evidence/` |

## 14. Spikes (SP)

| ID | Frage | Vorgehen | Phase | Ergebnis gehört in |
|---|---|---|---|---|
| SP1 | Nimmt `pikepdf.Pdf.save()` eine vorhandene, leere Datei aus `mkstemp` als Ziel? | Einmal mit einer erzeugten PDF testen. | ST1 | Abschnitt 8, EVIDENCE |
| SP2 | Zeit und Speicher für eine echte PDF-Datei (eine Seite, viele Seiten, größte vorhandene Datei)? | `time` und Speichermessung um `encrypt_pdf` auf Kopien im Scratch-Verzeichnis. | ST5 | RIS5, RIS6, EVIDENCE |
| SP3 | Funktioniert `os.link` von der temporären Datei auf den Zielnamen im Zielordner, und scheitert es bei vorhandenem Ziel? | Einmal im Scratch-Verzeichnis prüfen. | ST1 | F9, F16, EVIDENCE |

## 15. Invarianten

| ID | Invariante | Nachweis |
|---|---|---|
| IN1 | Keine Netzwerkverbindung, kein Unterprozess, keine Umgebungsvariable mit Passwort. Die Zwischenablage liest `tkinter` direkt aus dem Display-Server, ohne Hilfsprogramm wie `xclip` oder `wl-paste`. | `ruff` und `mypy` sauber; kein Import von Netz- oder Unterprozessmodulen im Quelltext. |
| IN2 | Jede Eingabedatei wird nur lesend geöffnet; ihr Hash bleibt vor und nach dem Lauf gleich. | T23 |
| IN3 | Der Einstiegspunkt `pdfsec` in pyproject.toml bleibt gültig; `uv run pdfsec` startet die TUI. | T20 |
| IN4 | Alle sichtbaren Texte sind Deutsch, auch die Tastenkürzel in der Fußzeile (F24). | T15, T20 |

## 16. Offene Punkte

Keine. D3 ist mit E9 entschieden (keine Rechte-Beschränkungen), D5 mit E10
(Ausgabe beim Entschlüsseln heißt `<stamm>_open.pdf`). Die Revision 4 ist
freigegeben.

## 17. Quellen

| ID | Quelle | Verweis | Stand |
|---|---|---|---|
| Q1 | pikepdf-Dokumentation, `Encryption` und `Pdf.save` | https://pikepdf.readthedocs.io/en/latest/api/main.html | Version 10.18, geprüft 2026-11-22 |
| Q2 | pikepdf-Dokumentation, „PDF security“ | https://pikepdf.readthedocs.io/en/latest/topics/security.html | Version 10.18, geprüft 2026-11-22 |

## 18. Revisionen (REV)

| ID | Stand | Änderung |
|---|---|---|
| REV1 | 2026-11-22 | Erste Fassung. |
| REV2 | 2026-11-22 nach Review 1 | Entschlüsseln, Sichtbar-Schalter, Batch, atomares Anlegen per `os.link`, Nachprüfung mit Test, Quellen. |
| REV3 | 2026-11-22 nach Review 2 | `os.replace` als Alternative, Hardlink-Grenze, Eingabe-Hash-Test, `call_from_thread`, doppelte Pfade, Spikes mit Phase, Dateirechte, `reason`-Feld. |
| REV4 | 2026-11-22, Freigabe | E9 (keine Rechte-Beschränkungen), E10 (Ausgabe `_open.pdf`). |
| REV5 | 2026-11-22 nach Umsetzung | `TargetNotSupported` als eigene Ausnahme, Feld `warning` am `Result` (Befund aus F16). Die Erfolgszeile nennt den Zielnamen, den Ordner und die Seitenzahl, damit die Zeile in 80 Spalten lesbar bleibt (F26). |
| REV6 | 2026-11-22 auf Meldung von Frank | `Strg+V` fügt die Zwischenablage ein (F29, T25 bis T28, `clipboard.py`), Risiko RIS13, Knopfbreite des Sichtbar-Schalters auf 20 Zeichen festgelegt. |
