# INSTRUCTIONS.md — Arbeitsmodus für OpenCode + SuperGrok 4.6

## Auftrag

Implementiere die App milestoneweise nach `MILESTONES.md` und `MASTERPLAN.md`. Lies zuerst `/AGENTS.md` und `CONSTRAINTS.md` (dieser Ordner).

## Vorgehen pro Meilenstein

1. Akzeptanzkriterien lesen.
2. Dateien anlegen, die der Meilenstein nennt — nicht die ganze App „auf Vorrat“.
3. Unit-Tests schreiben (rot), Code (grün).
4. Manuell den Happy Path des Meilensteins durchspielen (ohne das zu überspringen, nur weil Tests da sind). Parser-Meilensteine: Fixture-Dateien verwenden.
5. Kurz in `IMPLEMENTATION-LOG.md` 5–10 Zeilen: was fertig, was offen.
6. Erst dann nächster Meilenstein.

## Fixtures sind Gesetz

`spec/fixtures/master-cv.json`, `job-coo.txt`, `job-ceo.txt` sind die Referenz.  
Wenn Detection beide Jobs als dieselbe Rolle sieht, ist Role-Detection falsch — nicht die Fixtures „anpassen“, bis es passt, außer bei echten Tippfehlern.

M4/M5: Heuristik (`role_score`, `lens_ranker`) muss die Fixtures **ohne** LLM trennen. LLM darf verfeinern.

## Qualität vor Breite

Lieber Milestone 5 (Plan) perfekt als Milestone 8 halb. Ohne FactGuard kein Generator.

## Modelle während der Entwicklung

Tests müssen mit **Mocks** des `llm_client` grün werden, unabhängig welches Tag der Entwickler in Ollama hat. Integrationstests mit echtem Ollama sind markiert `@pytest.mark.ollama` und dürfen skippen, wenn Health down ist.

Kein festes Qwen im Testcode außer als Beispiel-Default in `.env.example`.

Schreibe **keine** Fake-CVs in der UI als Fallback-Demo-Daten, die wie echte Generierung aussehen. Leerer State ist ehrlich. Ein Plan-Skelett ohne LLM (Ranker) ist erlaubt und gewollt.

## Commits (wenn Git genutzt)

Kleine Commits pro Meilenstein. Message: `m3: fact lock + struktureller ATS-report`.

## Wenn RAM knapp

README: ein Tag für beide Tiers. Der Code-Pfad `model_tier` bleibt. Ranker liefert den Plan auch ohne strong-Modell.

## Nicht tun

- Spec-Dateien löschen, um Widersprüche zu verstecken
- `fact_guard` „lockern“, damit ein Prompt durchgeht
- Scraping „nur einmal, zum Testen“
- `0.0.0.0` als Default
- Cloud-SDK „nur als Fallback“
- Modelle verbieten
