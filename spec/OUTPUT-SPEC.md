# OUTPUT-SPEC.md

## Leitformat: DOCX

Viele DACH-ATS parsen DOCX zuverlässiger. PDF ist Beigabe für den Menschen. TXT für Paste-Felder.

## Typografie

| Element | Font | Size | Weight |
|---|---|---|---|
| Name | Arial | 16 pt | Bold |
| Abschnittstitel | Arial | 12 pt | Bold |
| Body | Calibri | 11 pt | Regular |
| Meta (Kontakt, Daten) | Calibri | 10.5–11 pt | Regular |

- Seitenränder 1,8–2,2 cm
- Zeilenabstand einfach bis 1.08
- Keine mehrspaltigen Section Breaks
- Keine Tabellen für Layout. Eine einfache einzeilige Tabelle ist trotzdem verboten — ATS liest Zellenreihenfolge falsch
- Keine Kopf-/Fußzeilen mit Name/Telefon (doppelte oder verlorene Kontakte)
- Keine Textboxen, SmartArt, Shapes, Icons, Skill-Bars
- Schriftfarbe nahezu schwarz, Überschriften dürfen 10–15 % dunkleres Grau sein, kein Hellgrau
- Links: echte URLs, nicht nur Display-Text ohne Hyperlink-Target im TXT

## Reihenfolge CV

1. Name
2. Kontaktzeile (Stadt · Telefon · E-Mail · LinkedIn/Xing)
3. Profil / Summary (4–6 Zeilen, rollenspezifisch)
4. Berufserfahrung (reverse-chronologisch **in der Linsen-Reihenfolge**, nicht zwingend kalendarisch wenn der Nutzer das im Plan so bestätigt hat — Default bleibt kalendarisch innerhalb der vom Plan gesetzten Order)
5. Ausbildung
6. Kompetenzen (kommagetrennt oder einfache Bullet-Liste, **keine** Tabelle)
7. Sprachen
8. Zertifikate

Erfahrungseintrag:

```
Titel, Arbeitgeber, Ort
MM/YYYY – MM/YYYY  |  „heute“ lokalisiert (de: heute, en: present)

• Bullet mit Ergebnis, wo KPI existiert
• Bullet mit Keyword-Bindung, wo geplant
```

Max ~5 Bullets bei der führenden Station, 2–3 bei nachrangigen, 1 bei ausgeblendet-aber-doch-kurz.

## Anschreiben (Brief)

```
Name
Straße optional (nur wenn im FactLock und Nutzer will)
PLZ Ort
Telefon, E-Mail

Ort, Datum

Firma
optional Ansprechpartner
Betreff: Bewerbung als {Rollenbezeichnung}

Anrede,

Absatz 1: Bezug Stelle + Passung (Rolle)
Absatz 2: 2–3 Belege aus FactLock, keywords natürlich
Absatz 3: Motivation konkret an Unternehmen (nur aus Jobtext, keine erfundenen Produktnamen)
Schluss, Gruß
```

Eine Seite. Wenn länger: Generator kürzen, nicht Schrift auf 8 pt.

## TXT

Reine UTF-8, Überschriften in CAPS oder mit `## `, Trennlinien `---`. Keine Markdown-Tabellen. Für ATS-Paste.

## PDF

ReportLab, identische Reihenfolge. Fonts: Calibri/Arial wenn auf dem Host vorhanden, sonst Helvetica bzw. Liberation Sans (Linux). Kein macOS-Hardcode. Kein „Scan-PDF“ als Input (Parser 422).

## ZIP

```
Bewerbung_{Rolle}_{Firma}_{YYYYMMDD}/
  Lebenslauf_v{n}.docx
  Lebenslauf_v{n}.pdf
  Lebenslauf_v{n}.txt
  Anschreiben_v{n}.docx
  Anschreiben_v{n}.pdf
  Anschreiben_v{n}.txt
  INHALT.txt
```

`INHALT.txt`: Stelle-Titel, erkannte Rolle, Sprache, Version, Hinweis „lokal erzeugt, Faktenstand {hash kurz}“.

## Dateinamen

ASCII-safe Fallback plus Original-Umlaute wo das FS es kann. Niemals User-Input roh (`../../`).
