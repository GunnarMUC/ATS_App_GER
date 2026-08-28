# API.md

HTML-first: die meisten Endpunkte liefern HTML-Partials für htmx. JSON wo der Client State braucht (Plan-Editor). OpenAPI automatisch durch FastAPI.

Basis: `http://127.0.0.1:8000`

## Health / Settings

- `GET /health` → JSON, siehe `LOCAL-LLM.md` (`selected`, `models_installed`, `privacy_note`)
- `GET /settings` Seite
- `PUT /settings` JSON `{ "ollama_host", "model_fast", "model_strong" }` — Tags frei, dürfen identisch sein
- `POST /settings/wipe` 2-Klick-Löschen aller Bewerberdaten
- `GET /settings/backup` und `POST /settings/backup` → ZIP (`ats_app.db` + uploads + generated), optional `password`
- `POST /settings/restore` ZIP-Upload, optional `password`

## Pages (volle Templates)

- `GET /` Dashboard inkl. Bewerbungstabelle
- `GET /cv`
- `GET /cv/compare/{job_id}` Master vs. rollenspezifischer Plan
- `GET /jobs/new`
- `GET /jobs/{id}`
- `GET /jobs/{id}/plan`
- `GET /jobs/{id}/review`
- `GET /profiles`
- `GET /settings`

## Upload / Master

- `POST /upload/cv` multipart → redirect oder Partial mit Draft
- `GET /cv/{id}/facts` Editor
- `PUT /cv/{id}/facts` JSON Korrekturen vor Lock
- `POST /cv/{id}/lock` → FactLock aktiv
- `GET /cv/{id}/ats-structural` Partial

## Jobs

- `POST /jobs` JSON `{text}` oder multipart file
- `GET /jobs/{id}/analysis` Partial/JSON
- `POST /jobs/{id}/detect-role` startet Heuristik + Combined-Call (SSE optional)
- `POST /jobs/{id}/plan` erzeugt Ranker-Skelett, optional LLM-Brief, AdaptationPlan (draft)
- `PUT /jobs/{id}/plan/{plan_id}` Nutzer-Edits (Order, Hidden, role override)
- `POST /jobs/{id}/plan/{plan_id}/confirm`

## Bewerbungen

- `POST /applications` Form `job_id` — legt Application an (`stage=offen`)
- `POST /applications/{id}/stage` Form `stage`
- `POST /applications/{id}/notes` Form `notes`
- `POST /applications/{id}/delete`

## Profile

- `GET /api/profiles`
- `POST /api/profiles` aus bestätigtem Plan
- `PUT /api/profiles/{id}`
- `DELETE /api/profiles/{id}`

## Generierung

- `POST /jobs/{id}/generate?type=cv|cover|both`
- `GET /jobs/{id}/progress` SSE `text/event-stream`
- `GET /documents/{id}`
- `GET /documents/{id}/download?format=docx|pdf|txt`
- `GET /jobs/{id}/zip`
- `POST /documents/{id}/edit` Inline-Edit + FactGuard

## Fehler

JSON:

```json
{ "error": "fact_guard_failed", "message": "…", "details": [] }
```

HTML: Partial `partials/error.html`. Keine Tracebacks.

`503` wenn Ollama down bei einem LLM-Endpunkt. `422` Validierung. `413` Upload zu groß. `404` unbekannte IDs.

## Idempotenz

`POST generate` bei bestehender Version legt **neue** Version an, überschreibt nicht. Doppelklick darf nicht zwei parallele LLM-Jobs starten — Server-Flag `job.generating`.
