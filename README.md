# ATS-Bewerbungs-APP

[![CI](https://github.com/GunnarMUC/ATS_App_GER/actions/workflows/ci.yml/badge.svg)](https://github.com/GunnarMUC/ATS_App_GER/actions/workflows/ci.yml)
[![Lint](https://github.com/GunnarMUC/ATS_App_GER/actions/workflows/lint.yml/badge.svg)](https://github.com/GunnarMUC/ATS_App_GER/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20local-black?logo=ollama&logoColor=white)](https://ollama.com)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)](#was-sie-brauchen)
[![Privacy](https://img.shields.io/badge/Privacy-local%20first-success)](#datenschutz-in-klartext)
[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](tests/)
[![No cloud SDK](https://img.shields.io/badge/Cloud%20SDK-none%20in%20app-important)](#datenschutz-in-klartext)

**Lokale App für den DACH-Bewerbungsmarkt:** Aus einem echten Master-Lebenslauf und einer konkreten Stellenanzeige entstehen ein **rollenspezifischer, ATS-tauglicher CV** und ein **Anschreiben** — als DOCX, PDF, TXT oder ZIP.

Die App läuft **nur auf Ihrem Rechner**. Sie schickt Ihre Daten nicht an OpenAI, Google oder ähnliche Dienste. Optional nutzt sie **Ollama** auf demselben Gerät (beliebiges Modell, das Sie dort installiert haben).

**Lizenz:** MIT · **Plattform:** macOS, Windows, Linux · **Kein Docker, kein Account, kein API-Key**

---

## Was die App macht (in einem Satz)

Sie hinterlegen Ihren Werdegang **einmal** (Fakten werden gesperrt). Für jede Stelle wählt die App eine **Rollensicht** (CEO, COO, CFO, CTO, Vertrieb, HR, Projekt, …): andere Reihenfolge, anderes Profil-Summary, andere Betonung — **ohne** Arbeitgeber, Daten oder Zahlen zu erfinden.

| Ohne diese App | Mit dieser App |
|---|---|
| Ein CV für alle Rollen | Viele Sichten auf dieselben Fakten |
| ChatGPT riskiert erfundene Stationen | FactGuard blockiert Erfindungen |
| Lebenslauf in der Cloud | Daten bleiben lokal (App → Ollama auf localhost) |

---

## Was Sie brauchen

1. **Python 3.12** (oder neuer)  
   - macOS (Homebrew): `brew install python@3.12`  
   - Windows: [python.org](https://www.python.org/downloads/) — Häkchen „Add Python to PATH“ setzen  
   - Linux: Paketmanager, z. B. `python3.12`

2. **Ollama** (kostenlos) — [ollama.com](https://ollama.com)  
   Mindestens **ein** Sprachmodell (Instruct). Empfehlung für gutes Deutsch/JSON:
   - `qwen2.5:7b` (schneller, weniger RAM)  
   - `qwen2.5:14b` (stärker, mehr RAM)  
   Ein Modell reicht: in den Einstellungen „Ein Modell für beides“ wählen.

3. **Einen Browser** (Chrome, Firefox, Safari, Edge …)

4. **Optional:** Ihren Lebenslauf als PDF, DOCX, TXT oder Markdown (max. 8 MB). Gescannte PDFs ohne Text gehen in v1 **nicht** (kein OCR).

**Hardware (Richtwert, kein Zwang):**

| RAM ca. | Praktisch |
|---|---|
| ab ~8 GB | ein kleines Modell (7B/8B) für alles |
| 16–24 GB | 7B + 14B nacheinander |
| mehr | größeres Modell, wenn Sie wollen |

---

## Installation — Schritt für Schritt

### Schritt 1: Projektordner öffnen

Laden Sie das Projekt herunter (ZIP oder `git clone`) und öffnen Sie ein Terminal **im Projektordner** (dort liegen `README.md` und der Ordner `app/`).

```bash
cd Pfad/zu/ATS_App_GER
```

### Schritt 2: Ollama starten und Modell holen

**Terminal 1** (kann im Hintergrund laufen):

```bash
ollama serve
```

**Weiteres Terminal** — Modell herunterladen (einmalig, kann einige Minuten dauern):

```bash
# Empfehlung — eines oder beide:
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b

# Oder jedes andere Instruct-Modell, das Sie bevorzugen, z. B.:
# ollama pull llama3.2
# ollama pull mistral
```

Prüfen, ob Ollama antwortet:

```bash
ollama list
```

### Schritt 3: Python-Umgebung und Abhängigkeiten

**macOS / Linux:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

**Windows (Eingabeaufforderung oder PowerShell):**

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Die Datei `.env` müssen Sie in der Regel **nicht** ändern. Standard:

- App nur unter `127.0.0.1` (nicht im ganzen Netzwerk). Anderer Host → Start bricht ab, außer Sie setzen bewusst `APP_ALLOW_NONLOCAL=true`.
- Ollama unter `http://127.0.0.1:11434`

### Schritt 4: App starten

Mit aktivierter Umgebung (`.venv`):

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Im Browser öffnen:

**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

Die App beenden: im Terminal `Ctrl+C` (Windows: `Strg+C`).

---

## Erste Einrichtung in der App (2 Minuten)

1. Linke Seite → **Einstellungen**
2. Prüfen: Status **Ollama = connected** (grün/ohne Warnung)
3. **Modell fast** und **Modell strong** wählen  
   - Beide dürfen **gleich** sein („Ein Modell für beides“)  
   - Fehlt ein Modell: gelber Hinweis + Befehl `ollama pull …`
4. Speichern

**Hinweis zu Cloud-Modellen in Ollama:**  
Manche Ollama-Tags laufen nicht auf Ihrem PC, sondern Ollama leitet sie weiter. Die App blockiert das nicht. Dann verlassen die Daten den Rechner **über Ollama**, nicht über einen zweiten Cloud-Client in dieser App. Ein Banner weist darauf hin.

---

## So bewerben Sie sich — kompletter Ablauf

### A) Master-Lebenslauf einmal anlegen

1. Menü **Master-CV**
2. Datei hochladen **oder** Text einfügen  
3. **Hochladen und Text lesen** → Rohtext prüfen  
4. **Fakten prüfen / sperren**  
   - Optional: „Mit Ollama strukturieren“ (braucht starkes Modell)  
   - Oder JSON manuell korrigieren / **Fixture** nur zum Testen  
5. **Entwurf speichern**, dann **Fakten sperren**  
   - Ab jetzt: umsortieren und umformulieren ja, **erfinden nein**  
6. Optional: **Export** → Master roh als DOCX/PDF/TXT (ohne Rollensicht)

**Tipp zum Testen ohne eigenen CV:** Auf der Master-CV-Seite „Fixture-Master laden“ (fiktive Person Alex Morgenstern).

### B) Stelle anlegen

1. Menü **Stellen** → Anzeige **einfügen** oder Datei laden  
2. **Analysieren**  
3. **Erkannte Rolle** prüfen (z. B. COO vs. CEO)  
4. Bei Bedarf Rolle manuell überschreiben  
5. **Rolle übernehmen und Plan öffnen**

### C) Anpassungsplan bestätigen

Sie sehen einen **Vorschlag**, keine Blackbox:

- Reihenfolge der Stationen (per Drag & Drop änderbar)
- Stationen ausblenden
- Richtung des Profiltexts (Summary)
- Keywords: vorhanden / Lücke (Lücken werden **nicht** erfunden)
- Warnungen (z. B. „Titel bleibt Geschäftsleitung Operations“)

Optional: **Als Rollenprofil speichern** (z. B. „COO Logistik“ für später).

Dann: **Plan bestätigen und weiter**.

### D) CV und Anschreiben erzeugen

1. **CV + Anschreiben erzeugen** (oder nur CV / nur Anschreiben)  
2. Status **Guard OK** = FactGuard hat keine erfundenen Arbeitgeber/Zahlen gefunden  
3. **Master vs. Rolle vergleichen** — gesperrte Fakten links, rollenspezifische Sicht rechts  
4. Download: DOCX / PDF / TXT  
5. **ZIP** = Bewerbungsmappe mit beiden Dokumenten + kurzer `INHALT.txt`

**Empfehlung für ATS (Personio, SuccessFactors, Softgarden, …):**  
→ **DOCX** hochladen. PDF zusätzlich für Menschen im Versand.

---

## Typischer Alltag (ab dem zweiten Mal)

1. App + Ollama starten  
2. Neue Stelle einfügen  
3. Rolle und Plan in 1–2 Minuten bestätigen  
4. Generieren → Vergleich prüfen → ZIP  
5. Auf **Übersicht** den Bewerbungsstatus setzen (offen / eingereicht / Interview / …)

Der Master-CV bleibt gesperrt, bis Sie bewusst neu ableiten.

---

## Menü kurz erklärt

| Menü | Zweck |
|---|---|
| **Übersicht** | Master-CVs, Bewerbungstabelle mit Status, Ollama |
| **Master-CV** | Upload, Fakten, Schloss, Export roh |
| **Stellen** | Anzeige → Rolle → Plan → Review → Vergleich |
| **Profile** | Gespeicherte Rollensichten (keine zweiten Biografien) |
| **Einstellungen** | Ollama-Host, Modelle, Backup/Restore-ZIP, alle Daten löschen |

---

## Datenschutz in Klartext

- Die App bindet nur **127.0.0.1**. Ein anderer Host startet nicht, außer `APP_ALLOW_NONLOCAL=true`.  
- Formulare sind CSRF-geschützt (lokales Token).  
- **Kein** eingebauter OpenAI-/Anthropic-/xAI-Client, **keine** Telemetrie.  
- Einziger Netz-Kontakt der App: **Ollama** (meist localhost).  
- Uploads und Ergebnisse liegen unter `data/` auf Ihrer Festplatte.  
- **Einstellungen → Daten:** Backup-ZIP (optional mit Passwort) und Restore.  
- **Einstellungen → Alle Bewerberdaten löschen** (Bestätigungswort `LOESCHEN`) löscht DB, Uploads und Generierungen unwiderruflich.

---

## Häufige Probleme

### „Ollama ist nicht erreichbar“

1. Läuft `ollama serve`?  
2. Einstellungen: Host = `http://127.0.0.1:11434`  
3. Browser neu laden  

Die App bleibt ohne Ollama **lesbar** (alte Dokumente, Fakten). Generieren mit LLM braucht Ollama; der Hybrid-Pfad (Heuristik + Vorlagen) kann vieles auch ohne starkes Modell.

### „Gewähltes Modell fehlt“

```bash
ollama pull NAME-DES-MODELLS
```

Danach in den Einstellungen neu wählen und speichern.

### Upload schlägt fehl / „kein brauchbarer Text“

- Datei zu groß? Max. **8 MB**  
- Erlaubt: **.pdf .docx .md .txt**  
- Scan-PDF ohne Text → in v1 nicht unterstützt → DOCX oder Klartext nutzen  

### App startet nicht: „APP_HOST ist nicht Loopback“

Die App darf standardmäßig nur auf `127.0.0.1` lauschen. Bewusst im Netz: in `.env` `APP_ALLOW_NONLOCAL=true` setzen — dann sind Bewerberdaten im LAN erreichbar.

### Backup / Umzug auf einen anderen Rechner

Einstellungen → **Daten** → Backup-ZIP. Auf dem Zielrechner Restore aus derselben ZIP. Optional Passwort (AES).

### Port 8000 schon belegt

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Dann im Browser `http://127.0.0.1:8001` öffnen.

### Windows: `python` / `uvicorn` nicht gefunden

- `py -3.12` statt `python`  
- Nach `activate` sollte `pip` und `uvicorn` im venv liegen  
- Ausführungspolitik in PowerShell: ggf. `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Generierung dauert lange

Normale Modelle brauchen oft **30–90 Sekunden**. Fortschritt läuft schrittweise. Ein Request gleichzeitig (bewusst, wegen RAM).

---

## Was die App bewusst **nicht** macht

- Keine Jobbörsen, kein LinkedIn-Scraping, kein automatischer Versand  
- Kein Multi-User-Login / keine Cloud-Sync  
- Kein erzwungenes Foto, Geburtsdatum oder Familienstand im ATS-Output (AGG)  
- Kein „schöner erfundener“ Lebenslauf  

---

## Für Entwicklerinnen und Entwickler

| Pfad | Inhalt |
|---|---|
| `app/` | Anwendungscode |
| `spec/` | Produktvertrag, Meilensteine, Prompts, Schemas |
| `tests/` | pytest |
| `AGENTS.md` | Anweisungen für Coding-Agents |

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
PYTHONPATH=. pytest -q
```

Spec-Karte: [`spec/README.md`](spec/README.md) · Vertrag: [`spec/MASTERPLAN.md`](spec/MASTERPLAN.md)

---

## English summary

Local single-user web app for German/Austrian/Swiss job applications: one locked master CV, role-specific views (CEO, COO, CFO, CTO, …), application dashboard, side-by-side compare, backup ZIP. ATS-safe DOCX/PDF/TXT/ZIP. The app talks only to **your** Ollama on localhost (any tag you install). No cloud SDK inside the app. No Docker. No API key. Loopback bind is enforced.

1. Install Python 3.12 + [Ollama](https://ollama.com) + pull any instruct model  
2. `python3.12 -m venv .venv` → activate → `pip install -r requirements.txt` → `cp .env.example .env`  
3. `uvicorn app.main:app --host 127.0.0.1 --port 8000`  
4. Open http://127.0.0.1:8000 → Settings (pick models) → upload CV → lock facts → paste job → confirm plan → generate → ZIP  

If you use an Ollama *cloud* tag, data may leave the machine via Ollama — your choice.

---

## Support & Mitwirken

- Fehler und Ideen: GitHub Issues des Repos  
- Pull Requests willkommen (Tests grün halten)  
- Keine echten Lebensläufe ins Repository committen — nur die fiktiven Fixtures unter `spec/fixtures/`

**Viel Erfolg bei der Bewerbung — mit echten Fakten, klarer Rolle, lokal.**
