# DOMAIN.md — DACH-Bewerbung und ATS

## Markt, nicht Silicon Valley

Die App optimiert für **Deutschland/Österreich/Schweiz**. US-Resume-Ästhetik (Zweispalter, Skill-Balken, Foto-Header, „Objective“) ist schädlich.

### Typische ATS in DACH

Personio, SAP SuccessFactors, Workday, Softgarden, onlyfy, d.vinci, Recruitee, Greenhouse, Haufe.

Praxisregeln, die zählen:

- **DOCX oft robuster als PDF** beim Parsen
- Einspaltig, Standardfonts
- Kontakt im Body
- Keine Text-in-Bildern, keine SmartArt, keine Layout-Tabellen für Skills
- Keywords in Experience-Bullets schlagen Keyword-Listen ohne Kontext

## Deutscher Lebenslauf vs. ATS

Klassisch gewünscht (Mensch): Foto, Geburtsdatum, Familienstand, oft chronologisch aufsteigend.  
ATS und AGG: Foto/Alter/Familie sind Ballast oder Risiko.

v1-Default:

- Reverse-chronologisch
- Kein Foto
- Keine Pflicht-Personalien jenseits von Name, Stadt, Kontakt, LinkedIn/Xing
- Klare Blöcke: Name → Kontakt → rollenspezifisches Profil (Summary) → Erfahrung → Ausbildung → Skills → Sprachen → Zertifikate

Der Nutzer kann „klassische Angaben“ einschalten; der ATS-Strukturreport warnt dann.

## Anschreiben

- Eine Seite, 3–4 Absätze
- DIN-5008-angelehnt (kein Zwang zu jedem Leerzeilen-Dogma, aber: Absender, Datum, Betreff, Anrede)
- Betreff enthält Rollenbezeichnung
- Sie/Du aus der Stelle; Emotionalität 1–2 Stufen unter der Anzeige
- Keine Erfindung von Motiven („seit Kindheit Logistik-leidenschaftlich“), wenn nicht im Master

## Komposita und Aliase (ATS-Deutsch)

Deutsche Stellen zerreißen Keywords. `keyword_match.py` braucht Normalisierung:

| Stelle | Master darf matchen |
|---|---|
| Logistikleiter | Leiter Logistik, Logistik-Leiter, Head of Logistics |
| Supply-Chain-Management | SCM, Supply Chain, Lieferkette |
| Geschäftsführer | CEO, Managing Director, GF |
| Personalführung | Führung, Leadership, Teamleitung |
| S&OP | Sales and Operations Planning, S+OP |
| OTIF | On Time In Full, Liefertermintreue |

Regeln:

- Lowercase, ß→ss, Bindestriche/Spaces strippen für Vergleich
- Alias-Tabelle in `app/domain/aliases_de.json` (pflegebar, keine Magie)
- LLM darf Aliase **vorschlagen**, FactGuard lässt sie nur als `skills[].aliases` zu, nicht als neue Skill-Entität ohne Bezug

Englisch/Deutsch parallel ausgeben, wenn die Stelle gemischt ist: Skill „Projektmanagement / Project Management“, wenn beides zum Master passt.

## Rollensprache

- CEO-Stellen: Ergebnisverantwortung, Organisation, Stakeholder, Strategie, Wachstum, Governance
- COO-Stellen: Prozesse, Skalierung, OTIF, Kosten, Delivery, S&OP, Shopfloor/Netzwerk
- Nicht-synonym: Wer nie P&L hatte, bekommt in der CEO-Linse **keine** erfundenen 80 Mio. — wenn die Zahl im Master steht, darf sie nach oben

## Dateiformat-Empfehlung in der UI

Nach Generierung klar sagen:

> „Für ATS: DOCX verwenden. PDF zusätzlich für den Menschen im Versand.“

TXT existiert für Karriereportale mit Paste-Feld.

## Bewerbungsmappe

v1 erzeugt CV + Anschreiben. Zeugnisse werden nicht geparst. ZIP = diese beiden in 3 Formaten, plus eine `INHALT.txt` mit Stellen-Titel und Datum. Kein Motivationsschreiben-Chat.
