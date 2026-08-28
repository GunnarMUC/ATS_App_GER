# OPENCODE.md — Übergabe an OpenCode + SuperGrok 4.6

## Ziel

OpenCode soll aus **diesem Repo** die App implementieren. SuperGrok 4.6 ist nur der **Coding**-Agent. Das In-App-LLM ist Ollama mit dem Tag, das der Nutzer in Settings wählt.

Ablage: Spec unter `spec/`, Code unter `app/`, Tests unter `tests/`. `AGENTS.md` bleibt an der Wurzel. Kein zweites Repo.

## Modell in OpenCode

In den OpenCode-Einstellungen / `opencode.json` das Modell auf **SuperGrok 4.6** setzen. Keine API-Keys in die App schreiben.

```json
{
  "model": "grok-4.6",
  "instructions": ["AGENTS.md"]
}
```

## Erster Prompt an OpenCode (kopieren)

`spec/FIRST-PROMPT.txt` bzw.:

```
Lies AGENTS.md (Wurzel), dann spec/CONSTRAINTS.md, spec/MASTERPLAN.md, spec/MILESTONES.md.
Implementiere ausschließlich Milestone M1.
Kein Cloud-SDK in der App, kein Docker-Zwang, Bind 127.0.0.1:8000.
llm_client tag-agnostisch, Health laut spec/LOCAL-LLM.md, Settings mit beliebigen Ollama-Tags.
Fixtures in spec/fixtures/ nicht ändern, außer bei Syntaxfehlern.
Wenn fertig: Tests für M1 und 8 Zeilen in spec/IMPLEMENTATION-LOG.md.
Warte auf mein OK bevor M2.
```

Danach analog `Implementiere M2 …` bis M8. Nicht die ganze App in einem Rutsch.

## Check, ob das Kernfeature sitzt

Nach M4/M5 muss gelten:

- `spec/fixtures/job-coo.txt` → role_family `coo` **ohne** LLM (`role_score`)
- `spec/fixtures/job-ceo.txt` → role_family `ceo` ohne LLM
- AdaptationPlans verschieden (CEO: P&L nach vorn, COO: OTIF/S&OP nach vorn) über `lens_ranker`
- Titel `Geschäftsleitung Operations` bleibt in beiden CVs

Wenn die COO-Stelle zum CEO wird, weil „Geschäftsleitung“ vorkommt: Taxonomie und `lens_weights.json` zeigen, Fixtures nicht weichspülen.

## Häufige Agent-Fehler (abfangen)

| Fehler | Richtig |
|---|---|
| LangChain + Cloud-SDK | Nur `llm_client.py` + Ollama |
| Docker-Compose „für später“ als Pflicht | Nicht in v1 |
| Qwen hardcodieren / Mistral verbieten | Tags aus Settings |
| Tailwind CDN / Node zum Starten | Vendor + committed CSS |
| `0.0.0.0` | `127.0.0.1` |
| Profile = zweite Fakten-DB | Profile = Linse, Fakten nur im Lock |
| ATS-Score als Haupt-UI | Rollenkarte + Plan sind Haupt-UI |
| FactGuard lockern für schwache Modelle | Ranker-Skelett ohne LLM, Guard bleibt hart |
