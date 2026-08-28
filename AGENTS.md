# AGENTS.md — verbindliche Anweisungen für OpenCode + SuperGrok 4.6

Du implementierst **ATS-Bewerbungs-APP** (Arbeitstitel, lokal, DACH, OSS).  
Dieses Dokument ist die **erste Datei**, die du liest. Spec liegt unter `spec/`. Du darfst keine Datei dieses Packs ignorieren.

## Wer du bist

- Coding-Agent: OpenCode
- Modell: SuperGrok 4.6
- Auftrag: die App **vollständig implementieren**, milestoneweise, laut `spec/MASTERPLAN.md`
- Du bist **nicht** das In-App-LLM. Das In-App-LLM ist **Ollama** mit dem vom Nutzer gewählten Tag. Verwechsle die beiden nie.

## Lesereihenfolge (Pflicht, in dieser Reihenfolge)

1. `spec/CONSTRAINTS.md` — harte Verbote (Datenschutz, Fakten-Schloss, Injection)
2. `spec/MASTERPLAN.md` — Implementierungsvertrag (Modell, Plattform, Hybrid-Plan, Meilensteine)
3. `spec/DECISIONS.md` — nicht neu verhandeln
4. `spec/PRODUCT.md` — was das Produkt ist
5. `spec/ROLE-ADAPTATION.md` — Kernfeature, ohne das die App wertlos ist
6. `spec/DOMAIN.md` — DACH/ATS-Fachlogik
7. `spec/SECURITY.md` — lokal, keine Cloud-SDKs, Prompt-Injection
8. `spec/ARCHITECTURE.md` + `spec/DATA-MODEL.md` + `spec/FILE-STRUCTURE.md`
9. `spec/TECH-STACK.md` + `spec/LOCAL-LLM.md`
10. `spec/PROMPTS.md` + `spec/prompts/` + `spec/schemas/`
11. `spec/OUTPUT-SPEC.md` + `spec/UX.md` + `spec/API.md`
12. `spec/RULES.md` + `spec/TESTING.md`
13. `spec/MILESTONES.md` + `spec/INSTRUCTIONS.md`
14. `spec/fixtures/` — Testdaten für Rolle CEO vs. COO

`README.md` und `spec/GLOSSARY.md` bei Bedarf. Karte: `spec/README.md`.

## Non-Negotiables

1. **Kein Cloud-SDK in der App.** Kein Telemetrie, kein stiller xAI/OpenAI/Anthropic-Call. Einziger Outbound: `OLLAMA_HOST` (Default Loopback). Was Ollama intern mit einem Tag macht (lokal oder Cloud-Tag), ist Nutzersache — nicht nachbauen, nicht verbieten.
2. **Kein Scraping.** Stellen nur per Copy-Paste oder Upload (txt/docx/pdf/md).
3. **Fakten-Schloss.** Das Modell darf keine Arbeitgeber, Titel, Zeiträume, Abschlüsse, KPIs oder Skills **erfinden**. Nur umsortieren, kürzen, umformulieren, übersetzen, betonen.
4. **Rollensicht vor Generierung.** Jede Stelle bekommt eine erkannte Rolle + einen sichtbaren Anpassungsplan. Der Nutzer bestätigt, dann erst wird generiert.
5. **Ein Master-CV, viele Sichten.** CEO-Bewerbung und COO-Bewerbung sind zwei *Sichten* auf dieselben Fakten, nicht zwei Biografien.
6. **Meilensteine strikt nacheinander.** Kein Milestone N+1 bevor N grün ist (Tests + manuelle Akzeptanz).
7. **Prompts nur in `app/prompts/*.j2`.** Quelle: `spec/prompts/`. Keine Prompt-Strings in Python.
8. **JSON-Zwischenformat.** Parser → CV-JSON → Rollensicht → CV-JSON → Builder. Nie DOCX→DOCX.
9. **Kein Docker-Zwang in v1.** App nativ, Ollama nativ auf dem Host.
10. **Deutsch als UI- und Default-Dokumentsprache.** Job auf Englisch → Output auf Englisch.

## Definition of Done (gesamt)

- `docker` wird nicht benötigt
- `uvicorn` startet die App auf `http://127.0.0.1:8000`
- Health-Check zeigt Ollama-Status (connected/down) ohne zu crashen; gewählte Tags, nicht fest Qwen
- Beliebiges installiertes Ollama-Tag in Settings wählbar; fast und strong dürfen identisch sein
- Fixture-Master-CV + Fixture-Stelle-COO → COO-Sicht, Plan, CV
- Dieselben Master-Fakten + Fixture-Stelle-CEO → **andere** Reihenfolge, anderes Summary, **identische** Arbeitgeber/Daten/Titel-Felder
- Hallucination-Tests in `spec/TESTING.md` sind grün
- DOCX, PDF, TXT, ZIP funktionieren
- App-Code enthält keine Cloud-Provider-Clients und liest keine API-Keys

## Wenn etwas unklar ist

1. In `spec/` nachschlagen (`MASTERPLAN.md`, `GLOSSARY.md`, `CONSTRAINTS.md`).
2. Die **engere**, datensparsamere, lokalere Interpretation wählen.
3. Nicht raten: lieber eine explizite `TODO(spec)`-Marke als eine Cloud-API.

## Was du NICHT tun sollst

- Das Spec-Pack „verbessern“, indem du Cloud-SDKs in die App einbaust
- Jobbörsen anbinden
- Ein Foto, Geburtsdatum oder Familienstand erzwingen
- Einen US-Resume-Zweispalter als Default bauen
- Modelle verbieten oder auf Qwen festnageln
- FactGuard lockern, damit ein schwaches Modell „irgendwas“ liefert
- Meilensteine parallel vollenden und am Ende „zusammensetzen“
