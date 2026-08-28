# IMPLEMENTATION-LOG

## M0 — Vertrag (Spec v1.1)

Fertig:

- `MASTERPLAN.md` als Implementierungsvertrag
- Spec nachgezogen: beliebiges Ollama-Tag, Mac/Windows/Linux, MIT, Hybrid Ranker, ein Combined-Call, FactGuard-Zahlen mit Herkunft, CSS ohne Node
- Neu: `LICENSE`, `prompts/analyze_and_detect.j2`, `domain/lens_weights.json`
- Schema-Prosa: `skill_ids`, nicht `skill_refs`

Offen:

- M1 App-Code (uvicorn, Health, Parser, Settings)

Kein Anwendungscode in diesem Schritt, wie vereinbart.

## M0b — Ordnerstruktur

Fertig:

- Wurzel nur README, LICENSE, AGENTS.md
- Spec nach `spec/` (inkl. prompts, schemas, fixtures, domain)
- `app/` und `tests/` als Gerüst
- Pfade in AGENTS, README, MASTERPLAN, OPENCODE, FILE-STRUCTURE nachgezogen

## M1 — Gerüst, Health, Upload, Parser

Fertig:

- FastAPI `app/main.py`, Config, SQLite ORM, Alembic 001
- `llm_client` tag-agnostisch, `/health` laut LOCAL-LLM
- Settings-UI + `POST /api/settings` (fast=strong erlaubt)
- `document_parser` pdf/docx/md/txt, Scan/leer → 422
- Upload-UI + Text-Preview, Vendor JS, committed CSS
- Tests: 15 grün (Health ohne Ollama, Parser, Settings)
- `.env.example`, requirements, pyproject pythonpath

Offen / nächster Schritt:

- M2 Structurer + Fakten-Editor + FactLock

Manuell: `uvicorn app.main:app --host 127.0.0.1 --port 8000`

## M2 — Structurer + FactLock

Fertig:

- `cv_structurer.py` + Repair einmal, dann Fail
- Pydantic `CVStructure`, `fact_lock.py` (Hash, is_active, Archiv)
- Fakten-UI `/cv/{id}/facts`, PUT/POST facts, POST lock
- Fixture-Laden `/cv/load-fixture`
- Tests: 22 grün (roundtrip, mock structure, repair, lock archive)

Offen: M3 ATS-Struktur + Builder roh

## M3 — ATS-Struktur + Builder

Fertig:

- `ats_structural.py` (DOCX-Tabellen/Bilder/Textboxen, PDF-Spalten/Fonts)
- `text_builder`, `docx_builder` (keine Tabellen), `pdf_builder` (Font-Fallback)
- Export-UI `/cv/{id}/export`, Download `?format=docx|pdf|txt`
- Tests: 29 grün

Offen: M4 Stelle + Hybrid-Rolle

## M4–M8 — Kern bis Polish

Fertig:

- M4: jobs UI, keyword_match, role_score (CEO≠COO ohne LLM), Injection-Flag
- M5: lens_ranker, plan UI, confirm, RoleProfile speichern
- M6: cv_generator deterministisch, fact_guard Pflicht-Tests, Review/Download nur bei Guard-Pass
- M7: cover_generator, Cover-Guard, ZIP
- M8: Dashboard-Links, SSE progress, wipe, responsive CSS, README

Tests: gesamter Suite grün (Heuristik + Guard + Happy-Path ZIP).

LLM-Calls optional (use_llm); Default-Pfad läuft ohne Ollama-Generierung über Ranker/Templates.

## Update 1 — P1

Fertig:

- Rollenfamilien: `cto`, `chro`, `head_ops`, `project`, `consultant`, `product`, `eng_lead`; CFO/CSO-Gewichte und Fixtures
- Application-ORM + Dashboard-Status (offen…zusage), Alembic 002
- Compare `/cv/compare/{job_id}` (Master vs. Plan, FactGuard)
- Backup/Restore ZIP, optionales AES-Passwort (`pyzipper`)
- CSRF Double-Submit (403 ohne Token); Loopback-Start hart außer `APP_ALLOW_NONLOCAL=true`

P2 nicht in diesem Schritt: LLM-Mocks, Keyword-Gap-Vorschläge, Alembic-only-Boot, Rollen-Templates, OCR.
