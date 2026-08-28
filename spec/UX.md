# UX.md

## Ton

Ruhig, präzise, deutsch, kein Growth-SaaS. Die Person vertraut der App ihren Lebenslauf an.

Worte die passen: „Vorschlag“, „Sicht“, „Fakten unverändert“, „lokal“.  
Worte die nicht passen: „Wir haben Sie ATS-gehackt“, „Beat the bot“, Emoji-Feuerwerk.

## Informationsarchitektur

Ein Wizard + ein Dashboard. Keine zehn Hauptmenüs.

**Navigation (links oder top, schmal):**

- Übersicht
- Master-CV
- Rollenprofile
- Stellen / Bewerbungen
- Einstellungen (Ollama, Modelle, Daten löschen)

## Screens

### 1. Übersicht

Leerzustand: CTA „Master-CV hochladen“.  
Danach: Master-CV-Liste plus **Bewerbungstabelle** (Stelle, Rolle, Status-Badge offen/eingereicht/interview/absage/angebot/zusage, letzter CV, Vergleichslink). Status ist direkt änderbar.

### 2. Master-CV

- Dropzone + Dateiwahl
- Parser-Preview (Rohtext ausklappbar)
- Struktur-Editor: Felder korrigieren **bevor** Lock — das ist der Hauptweg, nicht der Notausgang
- Button „Fakten sperren“ (irreversibel bis „neu ableiten“)
- ATS-Strukturreport: Liste mit Ampel (Tabellen, Spalten, Bild, Fonts)
- Banner: „Die App sendet nur an Ollama auf diesem Rechner (Default localhost).“
- Scan-PDF / kein extrahierbarer Text: klarer Fail, kein OCR

### 3. Stelle anlegen

Zwei gleichwertige Wege:

- große Textarea (Placeholder: „Stellenanzeige hier einfügen“)
- Upload txt/docx/pdf

Danach automatisch: Sprache, Sie/Du, Keyword-Wolke (nur Anzeige), **Rollenkarte**.

### 4. Rollenkarte + Anpassungsplan (wichtigster Screen)

Layout Desktop: zwei Spalten.

**Links:** Stelle kompakt (Titel, Firma wenn erkennbar, Top-Anforderungen).  
**Rechts:** Detection.

```
Erkannte Rolle: COO — Operations  (hohe Sicherheit)
Alternative: CEO / Geschäftsführung  (mittel)

[ COO verwenden ]  [ Als CEO behandeln ]  [ Andere Rolle… ]
```

Darunter Plan:

- Drag&Drop Experience (SortableJS), Eye-Icon ausblenden
- Summary-Richtung (editierbares Textfeld, kein fertiger CV)
- Skills Top-n, verschiebbar
- Keyword-Matrix: grün vorhanden / gelb Alias / rot fehlt (rot = Lücke, kein Auto-Fill)
- Warnungen

Buttons: „Als Rollenprofil speichern“, „Plan bestätigen und CV erzeugen“

Mobile: eine Spalte, Stelle zuerst, Plan darunter. Touch-Targets ≥ 44 px. Kein horizontales Scrollen.

### 5. Review Generierung

Tabs: Lebenslauf | Anschreiben | Diff zur vorigen Version.

- Inline-Edit der Texte (werden in JSON zurückgeschrieben, FactGuard bei Save erneut)
- Rote Markierung, falls FactGuard unsichere Spans findet (sollte selten sein, weil Gate davor liegt)
- Downloads erst nach Guard-Pass
- „Neue Version“ erzeugt v+1, alte bleibt
- Anschreiben on-demand, CV-Download wartet nicht darauf

### 6. Rollenprofile

Liste CEO / COO / … — Name, role_family, letzte Nutzung. Edit = Sicht, nicht Fakten.

### 7. Einstellungen

- Ollama-Status (connected/down)
- Host-Feld (Default Loopback)
- Dropdown fast / strong aus installierten Tags; dürfen identisch sein
- Hinweis wenn Liste leer: `ollama pull …` für das, was der Nutzer will — kein festes Qwen
- Banner wenn gewähltes Tag `cloud` enthält (kein Deny)
- Banner wenn Host nicht Loopback und `OLLAMA_ALLOW_NONLOCAL`
- „Alle Daten löschen“
- Keine Account-Settings

## Mikrocopy (Pflichtsätze)

Lock: „Ab jetzt dürfen Generierungen diese Fakten nur umsortieren und umformulieren, nicht erweitern.“

Plan: „Keine Fakten werden geändert. Es ändert sich, welche Stationen führen und wie sie formuliert sind.“

Lücke: „Die Stelle verlangt {X}. Das steht nicht in Ihren Fakten. Wir erfinden es nicht.“

Ollama down: „Ollama ist nicht erreichbar. Läuft der Dienst? Host in den Einstellungen prüfen.“

Tag fehlt: „Das gewählte Modell ist in Ollama nicht installiert. Im Terminal: ollama pull {tag}“

Cloud-Tag: „Dieses Modell-Tag sieht nach einem Cloud-Modell in Ollama aus. Dann verlassen die Daten den Rechner über Ollama.“

OCR: „Aus dieser PDF ließ sich kein Text lesen. Gescannte Dateien werden in v1 nicht unterstützt. Bitte DOCX oder Text.“

Injection: nicht den Nutzer ängstigen. Intern flaggen reicht, außer FactGuard schlägt an — dann: „Die Anzeige enthält widersprüchliche Anweisungen. Es wurden nur Ihre bestätigten Fakten verwendet.“

## Loading

SSE oder htmx-Polling: Schritte „Stelle lesen → Rolle erkennen → Plan bauen → CV schreiben → prüfen“. Kein unbestimmter Spinner > 5 s ohne Text. Ein 14B-Tag darf 30–90 s brauchen; kleinere Tags weniger — die UI spricht von Schritten, nicht von „Qwen“.

## Accessibility / Qualität

- Kontrast WCAG AA
- Fokus sichtbar
- Buttons sind Buttons
- Fehlende Alt-Texte: keine sinnlosen Icons ohne Label
- Dark Mode **nicht** in v1 (optional Milestone Polish, Default hell, papierähnlich — passt zu Dokumenten)

## Visuelle Richtung

Papier, Tinte, eine Akzentfarbe (tiefes Tintenblau), viel Weißraum. Kein Neon-Dashboard, kein Fake-3D-Score-Ring als Held. Coverage als nüchterne Brüche: „11 von 14 Muss-Begriffen abgedeckt“.
