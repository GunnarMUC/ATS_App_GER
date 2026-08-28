# RULES.md — Code-Regeln für OpenCode

1. Python 3.12, PEP 8, Ruff-format. Type Hints an allen öffentlichen Funktionen.
2. Async an I/O-Grenzen. CPU-Parser in `to_thread`.
3. Kein Prompt-String in `.py`.
4. Kein Inline-JS in Templates außer einem Vendor-Include in `base.html`. Logik: Alpine / kleines `app.js`.
5. SQLAlchemy 2.0 Style. `PRAGMA foreign_keys=ON`, WAL.
6. Pydantic-Settings, kein `os.environ.get` verstreut.
7. User-Input: Größenlimit, Extension, Sanitize. IDs nur UUID aus der DB.
8. LLM: Semaphore(1), Timeout, Retry nur Transport, JSON validieren. Modell-Tags aus Settings, nicht hardcodieren.
9. FactGuard vor jedem Persist einer Generierung. Nicht lockern.
10. Keine Cloud-Imports (`openai` SDK nur falls OpenAI-**kompatibler** lokaler Adapter, Base-URL Loopback, **kein** Default-Key). Bevorzugt nativer Ollama-Adapter ohne openai-Paket.
11. Tests für jeden Service in dem Milestone, in dem der Service entsteht.
12. Kommentare nur wo die Regel nicht aus dem Namen spricht. Keine Narration.
13. UI-Strings deutsch. Code-Identifiers englisch.
14. Keine `print`-Debugs im Merge. `logging` mit IDs, ohne PII.
15. Wenn du ein Package hinzufügst: `requirements.txt` und Begründung in Commit-Message.
16. `pathlib`, UTF-8. Keine Mac-only-Pfade, kein Node zum App-Start.
