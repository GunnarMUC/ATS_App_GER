# TECH-STACK.md

Python gewinnt, weil Parser und Dokumentgeneratoren dort reif sind. Das Frontend bleibt bewusst dünn.

## Runtime

| Komponente | Version | Zweck |
|---|---|---|
| Python | 3.12 | App |
| FastAPI | 0.115+ | HTTP, OpenAPI |
| Uvicorn | 0.30+ | ASGI |
| Pydantic | 2.7+ | Settings, Schemas |
| SQLAlchemy | 2.0+ | ORM, SQLite |
| Alembic | 1.13+ | Migrationen |
| Jinja2 | 3.1+ | HTML + LLM-Prompts |
| httpx | 0.27+ | async Ollama-Client |
| aiofiles | 24+ | async Files |
| python-multipart | 0.0.9+ | Uploads |

## Dokumente

| Komponente | Version | Zweck |
|---|---|---|
| python-docx | 1.1+ | DOCX raus **und** rein |
| PyMuPDF (fitz) | 1.24+ | PDF-Text, primär |
| pdfplumber | 0.11+ | Fallback, Tabellen-Erkennung für ATS-Struktur |
| ReportLab | 4.0+ | PDF-Output, einspaltig |
| langdetect | 1.0.9+ | schnelle de/en-Hilfe, LLM bestätigt |

Kein WeasyPrint (System-Libs). Kein LibreOffice-Headless. Kein OCR in v1.

## Frontend

| Komponente | Version | Zweck |
|---|---|---|
| htmx | 2.x, vendored | Partials |
| Alpine.js | 3.14+, vendored | Drag&Drop-State, Toggles |
| SortableJS | 1.15+, vendored | Experience-Reihenfolge im Plan |
| CSS | committed `app/static/css/app.css` | Kein CDN, kein Node zum Starten |

Kein React in v1. Kein Tailwind-CDN. Tailwind darf der Maintainer lokal bauen und das Ergebnis committen; Endnutzer führt kein `npm` aus.

## LLM

| Komponente | Setup |
|---|---|
| Ollama | Default `http://127.0.0.1:11434` |
| strong / fast | beliebige Tags aus `/api/tags`; Defaults siehe `.env.example` |
| embeddings v1 | **nicht**. Keyword-Match regelbasiert + Alias-Tabelle + LLM-Extraction |

Client: eigenes `llm_client.py`, **kein** LangChain, **kein** LlamaIndex.

## Qualität

| Komponente | Zweck |
|---|---|
| pytest | Unit / Integration |
| pytest-asyncio | |
| jsonschema | Validate LLM-JSON |
| ruff | Lint + Format |
| mypy | optional ab Milestone 7, Type Hints trotzdem von Tag 1 |

## Was bewusst fehlt

- Docker-Pflicht, Compose, Redis, Celery, Postgres
- Node-Backend und Node als Runtime-Abhängigkeit
- Tailwind-CDN
- Poetry (pip + `requirements.txt` + `requirements-dev.txt`; `uv` darf in README stehen)

## Settings (Pydantic + DB-Overlay)

`.env.example` ohne Secrets:

```
APP_HOST=127.0.0.1
APP_PORT=8000
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL_STRONG=qwen2.5:14b
OLLAMA_MODEL_FAST=qwen2.5:7b
OLLAMA_ALLOW_NONLOCAL=false
DATA_DIR=./data
MAX_UPLOAD_MB=8
LLM_TIMEOUT_S=180
```

UI-Settings überlagern die Env-Defaults (gewählte Tags, Host). Keine API-Keys. Wenn jemand einen Key in `.env` legt, darf die App ihn **nicht** verwenden.
