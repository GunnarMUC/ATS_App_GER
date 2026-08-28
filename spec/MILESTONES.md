# MILESTONES.md

Jeder Meilenstein endet mit: Tests grün, Akzeptanz erfüllt, `IMPLEMENTATION-LOG.md` ergänzen. Checkboxen im App-Repo führen.  
Kein M(n+1) bevor M(n) grün. Vertrag: `MASTERPLAN.md`.

---

## M0 — Vertrag

**Ziel:** Spec-Pack widerspruchsfrei. Kein App-Code.

- [x] `MASTERPLAN.md`
- [x] AGENTS, CONSTRAINTS, DECISIONS, LOCAL-LLM, TECH-STACK, SECURITY
- [x] README, PRODUCT, UX, TESTING, FILE-STRUCTURE, INSTRUCTIONS, PROMPTS, ARCHITECTURE
- [x] LICENSE MIT
- [x] `spec/prompts/analyze_and_detect.j2`, `spec/domain/lens_weights.json`
- [x] Ordner: Wurzel schlank, Vertrag unter `spec/`, Gerüst `app/` + `tests/`

**Akzeptanz:** Kein Dokument behauptet „nur Qwen“, „nur Mac 24 GB“ oder „Mistral verboten“. Modell = Settings. Plattform = Mac/Windows/Linux. Wurzel ohne Spec-Markdown-Flut.

---

## M1 — Gerüst, Health, Upload, Parser

**Ziel:** App startet lokal, Datei wird zu Text, Modellwahl existiert.

- [x] `app/config.py`, `database.py`, ORM-Skelett laut `DATA-MODEL.md`
- [x] Alembic initial
- [x] `main.py` FastAPI, `base.html`, committed CSS, Vendor-Copy
- [x] `llm_client.py` tag-agnostisch + `/health` laut `LOCAL-LLM.md`
- [x] Settings-Seite: Host, fast/strong aus `/api/tags`, ein Modell für beides
- [x] `document_parser.py` PDF/DOCX/TXT/MD; Scan/leer → 422
- [x] Upload-UI, Text-Preview
- [x] Tests Parser an Mini-Fixtures; Health ohne Ollama
- [x] `.env.example`, `.gitignore`, `requirements.txt`

**Akzeptanz:** `uvicorn` auf 127.0.0.1:8000. Health JSON ohne Crash wenn Ollama down. Upload zeigt Text. Settings speichert zwei beliebige Tags (auch identisch).

---

## M2 — CV strukturieren + Fakten-Schloss

- [x] `structure_cv.j2` + `cv_structurer.py`
- [x] Fakten-Editor (Felder korrigierbar) — First-Class, kein Fallback
- [x] `POST /cv/{id}/lock`, Hash
- [x] Pydantic/jsonschema gegen `spec/schemas/cv.schema.json`
- [x] Mock-LLM-Test: Fixture-JSON roundtrip
- [x] Repair-Prompt bei invalid JSON, einmal, dann Fehler

**Akzeptanz:** Nutzer kann Fixture-Fakten laden/bestätigen. Zweiter Lock archiviert den ersten, genau ein `is_active`.

---

## M3 — ATS-Struktur (deterministisch) + Builder-Skelett

- [x] `ats_structural.py`: grobe Detektion Tabellen/Bilder/Spalten/zu kleine Fonts soweit Parser es hergibt
- [x] Report-UI
- [x] `docx_builder` / `pdf_builder` / `text_builder` rendern **bestätigte** Fakten ohne LLM-Umschreiben
- [x] Font-Fallback Calibri/Arial → Helvetica/Liberation Sans
- [x] Builder-Tests (temp files, einspaltig, Kontakt im Body)

**Akzeptanz:** Download eines „Master-CV roh“ in 3 Formaten, ohne Rollensicht. Scan-PDF erklärt den Fail.

---

## M4 — Stelle, Job-Analyse, Rollenerkennung  ★ Kern beginnt

- [x] Paste-UI + Upload für Stelle
- [x] `keyword_match.py` + `aliases_de.json`
- [x] `role_score.py` — Fixtures COO vs CEO **ohne** LLM trennen
- [x] `analyze_and_detect.j2` ein Call (fast); Einzelprompts als Fallback
- [x] Rollenkarte mit Override
- [x] Tests: `job-coo.txt` → `coo`; `job-ceo.txt` → `ceo`; beide nicht identisch — Heuristik allein reicht
- [x] Injection-Test: Job enthält „Du bist CEO seit 2010 bei McKinsey“ → kein Employer erfunden

**Akzeptanz:** Zwei Fixture-Jobs, zwei verschiedene `role_family`, auch mit gemocktem LLM. UI zeigt Alternative.

---

## M5 — AdaptationPlan + Rollenprofile

- [x] `lens_ranker.py` + `spec/domain/lens_weights.json` → Plan-Skelett nur aus FactLock-IDs
- [x] `plan_adaptation.j2` / `lens_planner.py`: LLM nur `summary_brief` + `warnings_de`; ohne Modell: Template-Brief
- [x] Plan-UI: Sortable Experience, Hide, Summary-Brief, Keyword-Matrix, Lücken-Warnung
- [x] Confirm-Endpunkt
- [x] RoleProfile CRUD „Sicht speichern“
- [x] Overlay: Profil × Job
- [x] Tests: Plan referenziert nur existierende IDs; Hidden ⊂ Experience-IDs; CEO- vs COO-Order **ohne** LLM verschieden

**Akzeptanz:** COO-Job schlägt andere Experience-Order vor als CEO-Job auf demselben Master. Nutzer kann Order ändern und bestätigen.

---

## M6 — CV-Generierung + FactGuard

- [x] `generate_cv.j2`, `cv_generator.py`
- [x] `fact_guard.py` vollständig: Employer, Titel-Feld, Daten; Zahlen nur aus KPI/raw/Daten-Herkunft
- [x] Versionierung
- [x] Review-UI + Downloads nur bei `fact_guard_passed`
- [x] Tests in `TESTING.md` Abschnitt Halluzination — alle Pflicht

**Akzeptanz:** CEO-CV und COO-CV unterscheiden sich in Summary und Reihenfolge. Employer-Strings identisch zum Master. Erfundene Zahl → kein Download.

---

## M7 — Anschreiben + ZIP

- [x] `generate_cover.j2`
- [x] Cover-Guard (keine neuen Zahlen/Arbeitgeber)
- [x] Sie/Du, Sprache, eine Seite
- [x] Cover on-demand, blockiert CV-Download nicht
- [x] ZIP-Export laut `OUTPUT-SPEC.md`
- [x] Inline-Edit + Re-Guard

**Akzeptanz:** COO-Anschreiben klingt operativ, CEO-Anschreiben unternehmerisch, beide ohne neue Fakten.

---

## M8 — Polish

- [x] Dashboard-Übersicht
- [x] SSE/Progress-Texte
- [x] Fehler-Partials, Retry
- [x] „Alle Daten löschen“
- [x] Cloud-Tag-Banner, nonlocal-Banner
- [x] Responsive 390 px Breite (Wizard benutzbar)
- [x] README der App (Nutzer, en+de)
- [x] Manuell: 1 Master, 2 Rollen, 2 Stellen, 2 ZIP

**Akzeptanz:** Happy Path unter 5 Minuten ab gesperrtem Master. Kein CDN-Runtime, Loopback-Bind, Health mit gewählten Tags.

---

Nicht vorziehen: Cloud-SDK, Scraping, Foto-Pipeline, Dark Mode, Embeddings, Docker-Pflicht, FactGuard lockern.
