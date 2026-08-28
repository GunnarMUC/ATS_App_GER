# PRODUCT.md

## One-liner

Lokale App, die aus einem gesperrten Master-CV und einer Stelle einen **rollenspezifischen ATS-CV** plus Anschreiben baut — CEO-, COO-, CFO- oder CTO-Bewerbung sind Sichten auf dieselben Fakten, nicht zwei Lebensläufe. Bewerbungsstatus, Vorher/Nachher-Vergleich und Backup bleiben auf dem Rechner.

## Zielperson

Eine Person (typisch: Führungskraft / Fachexperte im DACH-Raum), die sich **parallel auf unterschiedliche Rollen** bewirbt und deren echten Werdegang nicht in ein Cloud-SDK dieser App geben will.

Die App läuft auf dem Rechner der Person (Mac, Windows oder Linux) gegen **deren** Ollama. Welches Modell dort liegt, entscheidet sie.

Beispielnutzer: Logistik-/Operations-Führungskraft, die sowohl COO-Rollen (operativ, Supply Chain, Delivery) als auch CEO-/Geschäftsführer-Rollen (P&L, Organisation, Wachstum) anstrebt.

## Jobs-to-be-done

1. „Ich will meinen echten Werdegang einmal hinterlegen und nie wieder abtippen.“
2. „Ich will sehen, *warum* mein CV zu *dieser* Stelle nicht passt.“
3. „Ich will, dass der CV für COO anders erzählt als für CEO — ohne dass etwas erfunden wird.“
4. „Ich will ein Anschreiben, das Sie/Du und Sprache der Anzeige trifft, auf einer Seite.“
5. „Ich will Dateien, die Personio/SuccessFactors/Softgarden lesen können.“

## Kernschleife (Happy Path, < 5 Minuten ab dem zweiten Mal)

```
Master-CV vorhanden (Fakten gesperrt)
        ↓
Stelle einfügen (Paste oder Datei)
        ↓
App erkennt Rollenfokus + Sprache + Tonalität
        ↓
Anpassungsplan (Reihenfolge, Keywords, was ausgeblendet wird)
        ↓
Nutzer bestätigt oder korrigiert die Rolle / die Linse
        ↓
CV + Anschreiben generieren
        ↓
Review (Diff, rote Claims falls verdächtig)
        ↓
Editieren → DOCX / PDF / TXT / ZIP
```

Beim ersten Mal kommt davor: Upload → Parse → Faktenprüfung → ATS-Strukturreport. Settings: Ollama-Tags wählen.

## Drei Schichten, nicht zwei Profile

Viele Tools speichern „CV Version COO“ und „CV Version CEO“ als getrennte Dokumente. Das driftet.

Diese App hat drei Schichten:

| Schicht | Lebensdauer | Inhalt |
|---|---|---|
| **Master-CV** | Monate/Jahre | Vollständige Fakten, gesperrt |
| **Rollenprofil** | wiederverwendbar | Linse: „Wenn COO, dann …“ |
| **Bewerbung** | einmal pro Stelle | Job + Linse + generierte Artefakte + Versionen |

Ein Rollenprofil ist ein **Startpunkt**. Jede Stelle darf die Linse noch verfeinern (andere Keywords, andere Muss-Anforderungen, andere Branche).

## Was „Umarbeiten“ konkret heißt

Erlaubt und gewünscht:

- Summary neu, rollenspezifisch
- Experience-Reihenfolge nach Relevanz für *diese* Rolle
- Bullets umformulieren, damit Stellen-Keywords natürlich vorkommen
- Skills neu gewichten
- Irrelevante Stationen kürzen oder ausblenden
- Sprache de/en an die Stelle koppeln

Nicht erlaubt:

- Neue Biografie schreiben
- Aus einem Bereichsleiter stillschweigend einen CEO machen
- Zahlen aufblasen

Siehe `ROLE-ADAPTATION.md`.

## Erfolgskriterien (Produkt)

- Dieselben Fixture-Fakten ergeben für CEO-Stelle und COO-Stelle **sichtbar verschiedene** CVs.
- Arbeitgeber, Daten, Titel bleiben **byte-gleich** in den Faktenfeldern (nur Narrative-Felder ändern sich).
- Nutzer kann den Anpassungsplan in einem Screen verstehen, ohne Prompt-Engineering.
- Kein Schritt erfordert ein Cloud-SDK in der App. Ollama-Modell-Download ist optional und Sache des Nutzers.
- Die Unterscheidung CEO/COO darf nicht davon abhängen, dass genau Qwen 14B installiert ist (Heuristik + Ranker, siehe `MASTERPLAN.md`).

## Nicht-Ziele

- Die App bewirbt sich nicht selbstständig.
- Die App ist kein allgemeiner Chat mit dem Lebenslauf.
- Die App ersetzt keine Rechtsberatung (AGG, Foto, Angaben zur Person).
- Die App ist in v1 kein Multi-User-SaaS.
