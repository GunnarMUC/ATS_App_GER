# MASTERPLAN.md — Implementierungsvertrag

Nach M0 gilt dieses Dokument als **Implementierungsvertrag**.  
Produktkern: `ROLE-ADAPTATION.md`, FactLock, FactGuard, kein Cloud-SDK in der App.  
Bei Restkonflikt zu älterem Text in `DECISIONS.md` / `LOCAL-LLM.md` / Hardware-Sätzen: **dieses Dokument**.  
`CONSTRAINTS.md` bleibt die harte Wand für Datenschutz, Fakten-Schloss und Injection.

Repo: **dieses Verzeichnis**. Wurzel nur `README.md`, `LICENSE`, `AGENTS.md`. Spec unter `spec/`. App unter `app/`. Tests unter `tests/`. Kein zweites Repo.

---

## 1. Zielbild

Lokale Single-User-Webapp: ein gesperrter Master-CV + Stelle → sichtbare Rollensicht → bestätigter ATS-CV + Anschreiben.

Öffentliches GitHub (MIT). Mac / Windows / Linux. UI Deutsch. In-App-LLM = **jedes Modell, das Ollama auf `OLLAMA_HOST` anbietet**. Qwen 2.5/3 7B+14B ist Empfehlung, kein Zwang.

---

## 2. Entscheidungs-Deltas

| ID | Inhalt |
|---|---|
| D3 | Beliebiges Ollama-Tag. Defaults in `.env.example`: `qwen2.5:14b` / `qwen2.5:7b`. Fast und strong **dürfen identisch** sein. |
| D3b | App spricht nur Ollama (oder Loopback-OpenAI-Adapter). Was Ollama intern macht (lokales GGUF vs. Cloud-Tag), ist Nutzersache. |
| D4 | Kein Docker-Zwang in v1. Optional später, nicht Blocker. |
| D7 | Bind `127.0.0.1` Default. `0.0.0.0` → Start-Warnung + UI-Banner. |
| D16 | Kein Hardware-Gate. README nennt Empfehlungen, keine Pflicht-Pulls. |
| D17 | Endnutzer braucht **kein Node**. CSS liegt unter `app/static/css/`. |
| D18 | Rollen-Score + AdaptationPlan-Skelett **regelbasiert**. LLM ergänzt Text / Tie-Break. |
| D19 | License MIT. |

Privacy-Satz (UI + README):

> Die App sendet nur an Ollama unter der konfigurierten Adresse (Default localhost). Ein Cloud-Modell in Ollama verlässt den Rechner über Ollama, nicht über einen zweiten Client in dieser App.

---

## 3. Architektur

### 3.1 LLM-Client

Ein Client, zwei Adapter: `ollama` nativ `/api/chat`, `openai_compat` nur Loopback.

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

- Tags aus Settings (DB, überlagert `.env`), nicht hardcodiert
- `asyncio.Semaphore(1)`
- JSON: `format: json` → Fence-Extract → Pydantic/jsonschema → ein `json_repair.j2` → Fail
- Host muss Loopback sein, außer `OLLAMA_ALLOW_NONLOCAL=true`
- Kein Auto-Pull
- Modell-Tag enthält `cloud` (case-insensitive) → nicht blocken, gelbes Banner

`GET /health`:

```json
{
  "app": "ok",
  "ollama": "connected",
  "models_installed": [],
  "selected": { "fast": "qwen2.5:7b", "strong": "qwen2.5:14b" },
  "fast_present": true,
  "strong_present": false,
  "privacy_note": null
}
```

`privacy_note`: `"ollama_cloud_tag"` wenn ein gewähltes Tag `cloud` enthält, sonst `null`.  
Ollama down oder Tag fehlt: App lesend nutzbar, LLM-Routen 503.

### 3.2 Settings

- Ollama-Host (Default `http://127.0.0.1:11434`)
- Modell fast / strong: Dropdown aus Ollama `/api/tags`
- Ein Modell für beides erlaubt
- „Alle Daten löschen“
- Keine API-Keys; ein Key in `.env` wird **nicht** gelesen

### 3.3 Hybrid Role + Plan

**`role_score.py` (kein LLM)**  
Taxonomie + `aliases_de.json` + Titel/Muss-Keywords → Score je `role_family`. Top-1 wenn Abstand ≥ Schwelle, sonst Top-2. LLM-Tie-Break nur dann (`detect_role.j2` oder der Detection-Teil von `analyze_and_detect.j2`). Nutzer-Override immer.

**`analyze_and_detect.j2` (ein Call)**  
Happy Path statt analyze → detect. Schreibt weiter `JobDescription.analysis_json` und `RoleDetection.detection_json`. Einzelprompts bleiben Repair/Fallback.

**`lens_ranker.py` (kein LLM)**  
Pro Experience: Keyword-Hits gegen Job-Muss/Kann. Gewichte in `app/domain/lens_weights.json` (Spec-Quelle: `spec/domain/lens_weights.json`). Skelett nur mit IDs aus dem FactLock: `experience_order`, `hidden_experience_ids` (Vorschlag), `skill_order`, `keyword_bindings`, `gaps`, `emphasis_kpi_ids`, `emphasis_bullet_ids`.

**`lens_planner.py`** nimmt das Skelett, LLM nur für `summary_brief` + `warnings_de`, merged, validiert IDs. Fehlt das Modell: Skelett ist trotzdem ein gültiger Plan (kurze Template-Briefs aus den Gewichten).

### 3.4 FactGuard

- Employer / Titel-Feld / Daten: Normalisierung (Whitespace, Bindestriche, ß/ss), exakter Feld-Match
- Zahlen: nur Herkunft aus FactLock `kpis[].value|raw`, Experience-Daten, bekannten strukturellen Zahlen. Kein „jede Ziffer im Fließtext muss irgendwo vorkommen“
- Skills: Name oder `aliases[]`
- Titel-Feld unverändert; Summary darf rollensprachlich sein, ohne neuen Employer/KPI
- Fail → nichts persistieren, kein Download

### 3.5 Parser / Fonts / CSS

- Gescannte PDF / quasi kein Text: 422, UI „kein OCR in v1“
- ReportLab/DOCX: Calibri/Arial wenn vorhanden, sonst Helvetica / Liberation Sans
- `pathlib`, UTF-8
- Vendor JS lokal; CSS committed; kein Tailwind-CDN; kein Node zum Starten

### 3.6 Pipeline

```
Upload → Parser → (LLM strong) Structurer → Fakten-Editor → FactLock
Stelle → Parser → Heuristik Keywords+Rolle → (1× LLM) Analyse+Detection
      → Ranker-Skelett → (LLM strong optional) Brief → Plan-UI → Confirm
      → (LLM strong) CV JSON → FactGuard → Builder
      → (LLM strong) Cover on-demand → Cover-Guard → ZIP
```

Cover blockiert den CV-Download nicht.

---

## 4. Meilensteine

Strikt nacheinander. Jeder Schritt: Tests grün, manuelle Akzeptanz, 5–10 Zeilen `IMPLEMENTATION-LOG.md`. Details: `MILESTONES.md`.

| ID | Inhalt |
|---|---|
| M0 | Dieser Vertrag + Spec-Patches. Kein App-Code. |
| M1 | Gerüst, Parser, Health tag-agnostisch, Settings |
| M2 | Structurer, Fakten-Editor, FactLock |
| M3 | ATS-Struktur, Builder roh, Font-Fallback, OCR-Fail |
| M4 | Stelle, Heuristik, ein LLM-Call, Rollenkarte |
| M5 | Ranker, Plan-UI, Profile |
| M6 | CV-Generator, FactGuard |
| M7 | Anschreiben, ZIP |
| M8 | Polish, README-Nutzerpfad |

---

## 5. Definition of Done (gesamt)

- `uvicorn` auf `http://127.0.0.1:8000`, kein Docker nötig
- Health ohne Crash, Ollama optional
- Beliebiges installiertes Ollama-Tag in Settings wählbar
- Fixture-Master + COO-Stelle → COO-Sicht; dieselben Fakten + CEO-Stelle → andere Sicht, identische Employer/Daten/Titel-Felder
- Halluzinationstests grün
- DOCX, PDF, TXT, ZIP
- App-Code enthält keine Cloud-Provider-Clients und liest keine API-Keys
- LICENSE MIT, keine echten CVs im Repo
- Start: Python 3.12 + Ollama (irgendein Instruct-Modell) + `pip install -r requirements.txt`

---

## 6. Nicht in v1

Multi-User, Scraping, Versand, OCR, Embeddings, React, LangChain, Docker-Pflicht, Dark Mode, Auto-Pull, FactGuard lockern, zweites Cloud-SDK „nur als Fallback“.
