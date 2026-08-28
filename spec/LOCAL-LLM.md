# LOCAL-LLM.md

## Zwei verschiedene LLMs in diesem Projekt

| LLM | Wer | Aufgabe |
|---|---|---|
| SuperGrok 4.6 | OpenCode, beim Programmieren | Code schreiben |
| Ollama-Tag nach Wahl | die fertige App | CV/Stelle/Sicht/Generierung |

Die App ruft **niemals** Grok, xAI, OpenAI, Anthropic oder ein anderes Cloud-SDK auf. Einziger Outbound: `OLLAMA_HOST`.

## Warum Ollama, nicht LM Studio

Ollama ist der App-Server: headless, `localhost:11434`, Modell-Pull per CLI. LM Studio ist zum Ausprobieren gut. Die App darf optional einen OpenAI-kompatiblen Base-URL in Settings haben **nur wenn Host Loopback ist** — damit LM-Studio-Nutzer `http://127.0.0.1:1234/v1` eintragen können. Default bleibt Ollama-nativ (`/api/chat`).

Implementierung: ein Client, zwei Adapter (`ollama`, `openai_compat`). Default `ollama`.

## Modellwahl

Kein festes Modell. Settings listen `GET {OLLAMA_HOST}/api/tags`. Nutzer wählt **fast** und **strong** (dürfen identisch sein).

Defaults nur in `.env.example` / leerer Settings-DB:

| Tier | Default-Tag | Rolle |
|---|---|---|
| fast | `qwen2.5:7b` | Sprache, Ton, Keywords, JSON-Repair, Tie-Break Detection |
| strong | `qwen2.5:14b` | Structuring, Summary-Brief, CV, Cover |

Empfehlung für DACH-Deutsch+JSON: Qwen 2.5/3 Instruct. Andere Familien (Llama, Gemma, Mistral, …) sind erlaubt. Die App verbietet keine Tags.

Ein-Modell-Modus: beide Tiers derselbe Tag. Sinnvoll bei wenig RAM.

Kein Auto-Pull. Health: „Modell X fehlt. Im Terminal: `ollama pull …`“ — nur für das **gewählte** Tag, nicht als Pflicht-Qwen.

### Ollama-Cloud-Tags

Manche Ollama-Tags laufen nicht auf der GPU des Rechners, sondern Ollama leitet weiter. Die App unterscheidet das nicht über eine zweite API. Wenn der Tag `cloud` enthält: Banner, kein Deny. Siehe `MASTERPLAN.md` D3b.

### Hardware (Empfehlung, kein Gate)

| RAM (ca.) | Praxis |
|---|---|
| 8 GB | ein 7B/8B-Tag für beide Tiers |
| 16–24 GB | 7B fast + 14B strong nacheinander, nicht beide resident |
| mehr | größeres Instruct-Modell als strong, wenn der Nutzer will |

macOS/Windows/Linux über Ollama (Metal, CUDA, ROCm — Ollama-Sache, nicht App-Sache).

## Routing

| Aufgabe | Tier | LLM? | json_mode |
|---|---|---|---|
| CV strukturieren | strong | ja | ja |
| ATS-Struktur | — | nein | — |
| Job Keywords+Ton + RoleDetection | fast, **ein** Call `analyze_and_detect.j2` | ja | ja |
| Role-Score / Ranker-Skelett | — | nein | — |
| AdaptationPlan Brief/Warnings | strong, auf Ranker-Skelett | ja, optional | ja |
| CV generieren | strong | ja | ja |
| Cover generieren | strong | ja | nein (Fließtext) + JSON-Metadaten separat |
| FactGuard | — | nein | — |
| JSON-Repair | fast | ja, einmal | ja |

Einzelprompts `analyze_job.j2` / `detect_role.j2` bleiben Fallback/Repair.

## Betriebsregeln

- `Semaphore(1)`
- Timeout 180 s strong, 60 s fast
- Temperature: Extraction/Detection `0.1`, Plan/CV `0.3`, Cover `0.4`
- `num_ctx` 8192 Default; nicht still auf 32k heben
- Keep-alive: Ollama Default. Nicht beide Modelle dauerhaft geladen halten, wenn es zwei verschiedene sind.

## JSON-Mode

1. Ollama `format: json` wenn möglich
2. Prompt verlangt Schema-IDs
3. Parse → jsonschema + Pydantic
4. Bei Fail: ein Repair-Call (`prompts/json_repair.j2`) mit dem Schema-Fehler, dann Abbruch
5. Nie stillschweigend „best effort“-CV speichern

## Health

`GET /health`:

```json
{
  "app": "ok",
  "ollama": "connected",
  "models_installed": ["qwen2.5:7b"],
  "selected": { "fast": "qwen2.5:7b", "strong": "qwen2.5:14b" },
  "fast_present": true,
  "strong_present": false,
  "privacy_note": null
}
```

`ollama`: `"connected"` | `"down"`.  
`privacy_note`: `"ollama_cloud_tag"` | `null`.

UI: gelber Banner, wenn Ollama down oder gewähltes Tag fehlt. Rest der App lesend.

## Erstinstallation (Nutzer)

Ollama starten, irgendein Instruct-Modell pullen, in Settings wählen. Beispiel:

```
ollama serve
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b
```

Nicht Pflicht. Ein Tag reicht, wenn fast=strong.
