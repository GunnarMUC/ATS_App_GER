# ARCHITECTURE.md

## Übersicht

Single-user, lokal, synchron genug für einen Menschen. Kein Message-Bus.

```
┌──────────────────────────────────────────────┐
│  Browser                                      │
│  Jinja2 + htmx + Alpine.js + CSS (committed)  │
└────────────────────┬─────────────────────────┘
                     │ HTTP 127.0.0.1:8000
┌────────────────────▼─────────────────────────┐
│  FastAPI (nativ, Host-OS)                     │
│  Routers → Ranker/Guard → Services → Builders │
│  SQLite (WAL)    data/uploads  data/generated │
└────────────────────┬─────────────────────────┘
                     │ HTTP 127.0.0.1:11434
┌────────────────────▼─────────────────────────┐
│  Ollama (Host)                                │
│  fast / strong: beliebige Tags aus Settings   │
└──────────────────────────────────────────────┘
```

Kein App-Container in v1. Ollama und App teilen localhost (oder den bewusst gesetzten Host). GPU-Backend ist Ollama-Sache (Metal, CUDA, ROCm).

## Datenfluss

### 1. Master-CV Onboarding

```
Upload PDF/DOCX/MD/TXT
  → document_parser        (deterministisch; Scan → 422)
  → cv_structurer + LLM    (JSON laut cv.schema.json, Modell: strong)
  → UI Faktenprüfung
  → fact_lock.commit()     (Hash, confirmed_at)
  → ats_structural         (deterministisch, kein LLM)
  → DB: ReferenceCV + FactLock
```

### 2. Stelle aufnehmen

```
Paste oder Upload
  → document_parser
  → keyword_match + role_score     (kein LLM)
  → analyze_and_detect + LLM fast  (ein Call; Fallback: zwei Prompts)
  → optional: gespeichertes RoleProfile als Default-Sicht
  → lens_ranker                    (kein LLM, Plan-Skelett)
  → lens_planner + LLM strong      (Brief/Warnings; ohne Modell: Template)
  → UI: Plan bestätigen
  → DB: JobDescription + RoleDetection + AdaptationPlan
```

### 3. Generierung

```
FactLock + confirmed AdaptationPlan + Job
  → cv_generator + LLM strong → CV JSON
  → fact_guard.validate()     → pass/fail
  → docx_builder / pdf_builder / text_builder
  → cover_generator + LLM strong (on-demand)
  → fact_guard.validate_cover()
  → DB: GeneratedDocument (versioniert)
```

### 4. Rollenprofil speichern

```
Bestätigte Sicht → RoleProfile (CRUD)
Wiederverwendbar als Default bei gleicher role_family
```

## Komponenten

### Router

| Modul | Verantwortung |
|---|---|
| `health.py` | App + Ollama-Status + installierte/gewählte Tags |
| `settings.py` | Host, Modell-Tags, Daten löschen |
| `upload.py` | Dateien, Paste-Text |
| `reference_cv.py` | Parse, Fakten, Lock, ATS-Struktur |
| `jobs.py` | Stellen CRUD, Analyse |
| `roles.py` | Detection, Plan, Profile CRUD |
| `generate.py` | CV, Cover, Retry |
| `documents.py` | Preview, Download, ZIP, Versionen |
| `progress.py` | SSE für lange LLM-Calls |

### Services (Kern)

| Service | LLM? | Pflicht |
|---|---|---|
| `document_parser.py` | nein | PDF/DOCX/Text |
| `ats_structural.py` | nein | Spalten, Tabellen, Bilder, Fonts |
| `llm_client.py` | — | Ollama, Semaphore, JSON-Mode, Retry, Tag aus Settings |
| `cv_structurer.py` | strong | unstrukturierter Text → CV JSON |
| `fact_lock.py` | nein | Commit, Hash, Load |
| `fact_guard.py` | nein | Output vs. Master |
| `keyword_match.py` | nein | Coverage, Komposita, Aliase |
| `role_score.py` | nein | role_family-Scores |
| `job_analyzer.py` | fast | Combined-Call / Fallback Keywords, Ton, Sprache |
| `role_detector.py` | fast | Combined-Call / Fallback RoleDetection |
| `lens_ranker.py` | nein | Plan-Skelett aus IDs |
| `lens_planner.py` | strong optional | Brief/Warnings auf Skelett |
| `profile_engine.py` | nein | CRUD, Overlay Job×Profil |
| `cv_generator.py` | strong | rollenspezifischer CV JSON |
| `cover_generator.py` | strong | Anschreiben |
| `docx_builder.py` | nein | Leitformat |
| `pdf_builder.py` | nein | ReportLab |
| `text_builder.py` | nein | ATS-Paste |

### LLM-Client-Vertrag

```python
async def generate(
    prompt: str,
    *,
    model_tier: Literal["fast", "strong"] | None = None,
    model: str | None = None,
    json_mode: bool = False,
    timeout_s: int = 180,
) -> str: ...
```

Tags aus Settings, nicht hardcodiert. Rest: `LOCAL-LLM.md`.

## Speicher

```
data/
  ats_app.db
  uploads/{uuid}_{safe_filename}
  generated/{cv|cover}/{uuid}_v{n}.{docx|pdf|txt}
```

- Originale nie überschreiben
- Generierte Versionen nie still überschreiben; `version` incrementiert pro `(RoleProfile, job, type)`
- SQLite `PRAGMA journal_mode=WAL` und `foreign_keys=ON`
- Pfade über `pathlib`, UTF-8, kein OS-spezifischer Hardcode

## Sync vs. Async

- FastAPI async.
- LLM und File-IO async (`httpx`, `aiofiles`).
- CPU-Parser (PyMuPDF, python-docx) in `asyncio.to_thread`.
- SQLAlchemy 2.0: in v1 reicht `StaticPool` + eine Writer-Connection; keine parallelen Writer nötig.

## Fehlergrenzen

- Parser-Fehler / Scan-PDF → 422 oder Rohtext + Warnung, kein Crash
- LLM-Timeout → User-Message, Retry-Button, kein korrupter FactLock
- FactGuard-Fail → Generierung nicht speichern
- Ollama fehlt / Tag fehlt → Health gelb, restliche UI lesend nutzbar
- Ranker-Skelett ohne LLM → gültiger Plan, knapper Template-Brief

## Warum kein Docker-Zwang in v1

Ollama soll die Host-GPU nutzen. Ein App-Container zwingt `host.docker.internal`, Volume-Mapping und RAM-Limits, ohne Nutzen für den einzelnen Nutzer. Native `uvicorn` ist die v1-Form. Docker kann später optional kommen, nicht als Blocker.
