# DATA-MODEL.md

Single-User. Trotzdem saubere IDs, weil Versionierung und FactGuard darauf beruhen.

JSON-Felder werden gegen `schemas/*.json` validiert **bevor** sie in die DB geschrieben werden.

## ORM (SQLAlchemy 2.0)

### ReferenceCV

Master-Dokument.

| Spalte | Typ | Notes |
|---|---|---|
| id | UUID PK | |
| original_filename | str | sanitized |
| stored_path | str | unter `data/uploads/` |
| media_type | str | pdf/docx/md/txt |
| raw_text | text | Parser-Output |
| structured_json | JSON | CV-JSON vor Lock, draft |
| ats_structural_json | JSON | deterministischer Report |
| created_at | datetime | |

### FactLock

Unveränderliche, bestätigte Fakten. Neue Bestätigung = neue Zeile, alte bleibt (Audit).

| Spalte | Typ | Notes |
|---|---|---|
| id | UUID PK | |
| reference_cv_id | FK | |
| facts_json | JSON | `cv.schema.json` |
| content_hash | str | SHA-256 kanonisches JSON |
| confirmed_at | datetime | |
| is_active | bool | genau ein active pro App |

### RoleProfile

Wiederverwendbare Default-Linse (z. B. „COO“, „CEO“).

| Spalte | Typ | Notes |
|---|---|---|
| id | UUID PK | |
| name | str | Nutzername, z. B. „COO Logistik“ |
| role_family | str | Enum-Taxonomie |
| lens_json | JSON | `role-lens.schema.json` |
| created_at / updated_at | datetime | |

### JobDescription

| Spalte | Typ | Notes |
|---|---|---|
| id | UUID PK | |
| title_raw | str | |
| source | str | paste \| upload |
| raw_text | text | |
| stored_path | str nullable | |
| language | str | de \| en |
| analysis_json | JSON | Keywords, Ton, Muss/Kann |
| created_at | datetime | |

### RoleDetection

| Spalte | Typ | Notes |
|---|---|---|
| id | UUID PK | |
| job_id | FK | |
| detection_json | JSON | `role-detection.schema.json` |
| user_role_family | str nullable | Override |
| created_at | datetime | |

### AdaptationPlan

Bestätigbarer Plan. Generierung referenziert **diese** ID, nicht „was das LLM gerade denkt“.

| Spalte | Typ | Notes |
|---|---|---|
| id | UUID PK | |
| job_id | FK | |
| fact_lock_id | FK | |
| role_profile_id | FK nullable | |
| plan_json | JSON | `adaptation-plan.schema.json` |
| status | str | draft \| confirmed \| superseded |
| confirmed_at | datetime nullable | |

### GeneratedDocument

| Spalte | Typ | Notes |
|---|---|---|
| id | UUID PK | |
| type | str | cv \| cover |
| job_id | FK | |
| fact_lock_id | FK | Hash muss noch matchen |
| plan_id | FK | |
| version | int | |
| structured_json | JSON | generiertes CV oder Cover-Metadaten |
| docx_path / pdf_path / txt_path | str | |
| fact_guard_passed | bool | nur True-Zeilen sind downloadbar |
| created_at | datetime | |

Kein `Candidate`-User-Modell in v1. Ein lokaler Nutzer.

### AppSettings

Ein-Zeilen- bzw. Key-Value-Store für UI-Settings (überlagert `.env`).

| Spalte | Typ | Notes |
|---|---|---|
| id | int PK | singleton 1 |
| ollama_host | str | Default aus Env |
| model_fast | str | beliebiges Tag |
| model_strong | str | beliebiges Tag, darf = fast |
| updated_at | datetime | |

Keine API-Keys.

## CV-JSON (Kurzform)

Volles Schema: `schemas/cv.schema.json`.

- `personal`: name, city, email, phone, linkedin, xing — **kein** Foto, Geburtsdatum, Familienstand als Pflicht. Felder dürfen existieren, Default-Output lässt sie weg.
- `summary`: string, rollenspezifisch, gilt als Narrative (nicht als Fakt). Beim Master darf Summary leer oder original sein.
- `experience[]`: `id`, employer, title, start, end, location, `bullets[]` (mit `kpi_ids[]`), `skill_ids[]`
- `education[]`, `skills[]` (id `sk_…`, name + aliases[] + category), `languages[]`, `certifications[]`
- `kpis[]` top-level (`kpi_…`), nicht als freie Zahlen im Fließtext
- IDs nach Lock **nie** ändern. Schema gewinnt vor Prosa (`skill_ids`, nicht `skill_refs`).

## Zahlen als Fakten

KPIs separat, nicht nur im Fließtext:

```json
{ "id": "kpi_otif", "label": "OTIF", "value": "+12 pp", "raw": "OTIF +12 Prozentpunkte" }
```

FactGuard nutzt `value` und `raw` plus Datenfelder. Freie Zahlen in generierten Bullets brauchen diese Herkunft — nicht „Ziffer kommt irgendwo im Master-Text vor“.

## Migrationen

Alembic ab Milestone 1. Jede Schemaänderung = Migration. Kein `create_all` in Produktion nach Milestone 1, in Dev darf `create_all` den ersten Boot strappen, danach Alembic.

## Löschregeln

- Nutzer kann Job + Generierungen löschen.
- Master-CV löschen nur mit expliziter Bestätigung; FactLock wird mitgelöscht.
- RoleProfiles unabhängig löschbar.
- Dateien auf Disk mitlöschen (kein Orphan in `data/generated`).
