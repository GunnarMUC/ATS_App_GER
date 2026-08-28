# DECISIONS.md — festgezogene Entscheidungen

OpenCode soll diese Punkte nicht neu aufrollen. Zuschnitt Modell/Plattform: `MASTERPLAN.md`.

| ID | Entscheidung | Begründung |
|---|---|---|
| D1 | Hier bauen, dieses Verzeichnis = GitHub-Repo | Spec und App an einem Ort; `app/` entsteht ab M1 |
| D2 | Ollama Default, LM Studio nur Loopback-OpenAI-Adapter | App-Integration, headless, Host-GPU (Metal/CUDA/ROCm über Ollama) |
| D3 | Beliebiges Ollama-Tag; Defaults `qwen2.5:14b` / `qwen2.5:7b`; fast=strong erlaubt | DACH-Empfehlung Qwen; andere Tags Nutzersache; kein Modellverbot |
| D3b | Kein zweiter Cloud-Client; Ollama-Cloud-Tags nicht blocken | App sendet nur an `OLLAMA_HOST`; was Ollama intern tut, entscheidet der Nutzer |
| D4 | Kein Docker-Zwang v1 | Host-GPU, Single-User, weniger RAM-Kampf. Compose optional später |
| D5 | FastAPI + htmx/Alpine, kein React v1 | Dokument-Pipeline ist Python; Wizard server-rendered |
| D6 | Kein Scraping | Recht, Stabilität, Privacy |
| D7 | Bind 127.0.0.1 | Bewerberdaten nicht ins LAN |
| D8 | Drei Schichten: Master, Rollenprofil, Bewerbung | CEO/COO sind Sichten, nicht zwei Biografien |
| D9 | Plan bestätigen vor Generierung | Keine Blackbox-Umschreibung |
| D10 | FactGuard deterministisch, nicht per LLM | Halluzination ist Blocker |
| D11 | DOCX Leitformat | DACH-ATS |
| D12 | Kein Foto/Geburtsdatum im Default-Output | ATS + AGG |
| D13 | Embeddings nicht in v1 | RAM; Keyword+Alias reicht |
| D14 | Kein LangChain | Kontrolle über JSON und Prompts |
| D15 | SuperGrok nur zum Coden, nie in der App | Privacy-Versprechen |
| D16 | Kein Hardware-Gate; Mac/Windows/Linux | OSS; Empfehlungen in README, keine Pflicht-Pulls |
| D17 | CSS committed, kein Node zum Starten | Endnutzer-Pfad: Python + Ollama |
| D18 | Heuristik zuerst für Rolle und Plan-Skelett | CEO≠COO auch ohne starkes Modell; LLM schreibt Text / Tie-Break |
| D19 | License MIT | Öffentliches GitHub |
