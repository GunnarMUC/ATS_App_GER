# ROLE-ADAPTATION.md — das Kernfeature

## These

**Ja: Rollenfokus erkennen und den CV darauf umbauen ist das Produkt.**  
Nicht „ATS-Score von 64 auf 81“. Der Score ist ein Hilfsmittel. Der Wert entsteht, wenn dieselbe Person für eine CEO-Stelle *anders erzählt wird* als für eine COO-Stelle — ohne Fälschung.

Ein statisches „Profil COO“ allein reicht nicht. „CEO einer 40-Personen-Spedition“ und „CEO einer PE-finanzierten Tech-Firma“ brauchen unterschiedliche Sichten, auch wenn beide `CEO` heißen. Deshalb:

```
Master-Fakten  →  role_score + Stelle  →  Ranker-Skelett  →  Sicht-Vorschlag
                 →  Nutzer bestätigt    →  jobspezifischer CV
```

Rollenerkennung und Plan-IDs sind zuerst Heuristik (`role_score.py`, `lens_ranker.py`). Das LLM schreibt Text und bricht Gleichstände. CEO≠COO darf nicht an einem bestimmten Ollama-Tag hängen.

Wiederverwendbare Profile (COO, CEO, Logistik-Leiter) sind **gespeicherte Default-Sichten**, die der Job noch überschreibt.

## Was die App erkennen muss

Aus Titel, Einstiegsabsatz und Anforderungsblock der Stelle:

| Signal | Beispiel | Wirkung auf die Sicht |
|---|---|---|
| Rollenfamilie | CEO, Geschäftsführer, COO, Leiter Logistik | Narrative-Archetyp |
| Seniorität | C-Level, VP, Head of, Specialist | Ton, Scope-Wörter |
| Funktion | Operations, General Management, Sales, Finance | welche Stationen führen |
| Branche | Spedition, Industrie, SaaS, Handel | Keyword-Aliase |
| Unternehmensgröße | Mittelstand, Konzern, Startup | welche KPIs betonen |
| Sprache | de / en | Output-Sprache |
| Tonalität | Sie / Du, förmlich / start-up | Anschreiben + Summary |
| Muss-Keywords | S&OP, P&L, Board, OTIF | Coverage-Plan |

Ausgabe ist **kein** einzelner String „COO“, sondern ein Objekt `RoleDetection` (Schema: `schemas/role-detection.schema.json`).

## Rollenfamilie (v1-Taxonomie)

Stabil, klein, erweiterbar. IDs fest (englisch), Labels deutsch:

| `role_family` | Labels (de) | Erzählfokus |
|---|---|---|
| `ceo` | CEO, Geschäftsführer, Vorstandsvorsitz, Managing Director | P&L, Organisation, Strategie, Stakeholder, Wachstum |
| `coo` | COO, Geschäftsleitung Operations, Leiter Operations | Delivery, Prozesse, Supply Chain, KPIs, Transformation |
| `cfo` | CFO, kfm. Geschäftsführung | Finanzen, Controlling, Working Capital |
| `cso_sales` | CSO, Vertriebsleitung | Pipeline, Key Accounts, Wachstum |
| `cto` | CTO, technischer Geschäftsführer | Technologie, Architektur, Engineering-Organisation |
| `chro` | HR-Leitung, CHRO, Head of HR | Personal, Talent, Tarif, Organisation |
| `head_ops` | Head of Operations, VP Operations | Tagesgeschäft, SLA, Standortprozesse (nicht C-Level) |
| `head_logistics` | Leiter Logistik, Head of Logistics, VP Supply Chain | Netz, Lager, Transport, OTIF, Kosten |
| `plant_ops` | Werkleiter, Plant Manager, Operations Manager | Produktion, OEE, Safety, Schicht |
| `program` | Program Director, Transformationsleitung | Governance, Change, Multi-Projekt |
| `project` | Projektmanager, Projektleiter | Scope, Meilensteine, Stakeholder |
| `consultant` | Berater, Consultant | Analyse, Empfehlung, Mandanten |
| `product` | Produktmanager, Head of Product | Roadmap, Discovery, Go-to-Market |
| `eng_lead` | Engineering-Lead, Head of Engineering | Plattform, Squads, technische Führung |
| `functional_expert` | Fachliche Expert:innenrolle | Tiefe, Tools, Methoden |
| `other` | Fallback | Nutzer muss Familie wählen |

Mehrdeutige Stellen (`Geschäftsführer Operations` ≈ COO, `CEO & COO in Personalunion`) → Top-2 vorschlagen, Nutzer wählt.

## Der Anpassungsplan (AdaptationPlan)

Bevor eine Zeile generiert wird, sieht der Nutzer eine Karte, keine Blackbox.

Pflichtfelder:

- Erkannte Rolle + Konfidenz (0–1) + Alternative
- Sprache und Sie/Du
- **Neue Reihenfolge** der Experience-Einträge (Drag&Drop vorausgefüllt)
- **Ausblenden**-Vorschläge mit Begründung („Buchhaltung 2011–2013: geringe Relevanz für COO“)
- Summary-Richtung in 2–3 Sätzen (nicht der finale Text)
- Skill-Reihenfolge (Top 8–12 für diese Stelle)
- Keyword-Matrix: vorhanden / als Synonym vorhanden / fehlt
- Warnungen: fehlende Muss-Anforderung, die ehrlich nicht im Master steht → **nicht erfinden**, sondern als Lücke zeigen („Stellen verlangt IFRS; nicht in Ihren Fakten“)

Der Nutzer kann:

- Rolle überschreiben
- Reihenfolge ändern
- Ausblenden rückgängig machen
- ein Rollenprofil speichern („als COO-Profil merken“)
- Generierung starten

Ohne Bestätigung keine Generierung.

## Wie Umschreiben funktioniert (mechanisch)

Quelle der Wahrheit: `FactLock.facts` (JSON laut `schemas/cv.schema.json`). Jede Experience hat eine stabile `id`.

Die Rollensicht speichert **keine neuen Fakten**, nur IDs aus dem FactLock (`sk_`, `exp_`, `b_`, `kpi_` — Schema: `adaptation-plan.schema.json`). Beispiel:

```json
{
  "role_family": "coo",
  "experience_order": ["exp_gl_ops", "exp_head_log", "exp_wh"],
  "hidden_experience_ids": ["exp_student_job"],
  "skill_order": ["sk_sop", "sk_otif", "sk_sap", "sk_leadership"],
  "summary_brief": "Operative Transformation, Netzwerk, OTIF, Kosten",
  "emphasis_kpi_ids": ["kpi_otif", "kpi_cts"],
  "emphasis_bullet_ids": ["b_gl_otif"],
  "keyword_bindings": [
    {"job_keyword": "Control Tower", "fact_kind": "bullet", "fact_id": "b_gl_otif"}
  ]
}
```

Plan-Skelett kommt von `lens_ranker.py` (kein LLM). Das Modell schreibt `summary_brief` / `warnings_de` und darf IDs nicht erfinden.

Der Generator:

1. Nimmt Fakten in `experience_order`
2. Lässt hidden weg
3. Schreibt Summary nur aus `emphasis_kpi_ids` / `emphasis_bullet_ids` + erlaubten Fakten
4. Bindet Keywords nur dort, wo `keyword_bindings` auf reale Bullets zeigen
5. Validiert Output gegen FactLock (siehe unten)

### Beispiel CEO vs. COO (gleiche Fakten)

Master (vereinfacht):

- 2020–2026: Geschäftsleitung Operations, 80-Mio-P&L, 200 FTE, Netzwerk 12 Standorte, OTIF +12 pp, S&OP eingeführt
- 2015–2020: Leiter Logistik, 3PL-Ausschreibung, SAP-Rollout
- 2010–2015: Projektleiter Warehouse

**Sicht COO** (Stelle: COO Mittelstand Logistik)

1. Geschäftsleitung Operations — Bullets: OTIF, S&OP, Netzwerk, Kosten
2. Leiter Logistik — 3PL, SAP
3. Projektleiter — kurz
4. Summary: operative Exzellenz, Delivery, Transformation

**Sicht CEO** (Stelle: Geschäftsführer / CEO)

1. Geschäftsleitung Operations — Bullets: P&L 80 Mio., 200 FTE, Organisation, Ergebnisverantwortung
2. Leiter Logistik — nur soweit sie unternehmerische Ownership zeigt
3. Projektleiter — eine Zeile oder ausblenden
4. Summary: P&L, Führung, Wachstum/Stabilität, Stakeholder

Titel „Geschäftsleitung Operations“ bleibt. Es wird **kein** „CEO seit 2020“ daraus.

## Validierung nach Generierung (Gate)

`app/services/fact_guard.py` prüft den generierten CV-JSON gegen den FactLock:

- Jeder Employer-String muss im Master vorkommen (Normalisierung: Whitespace, Bindestriche)
- Jedes Datum muss exakt matchen
- Zahlen nur mit Herkunft: `kpis[].value` / `kpis[].raw`, Experience-Daten, strukturelle Felder. Kein „jede Ziffer im Fließtext muss irgendwo vorkommen“
- Neue Skill-Namen nur, wenn Alias-Tabelle sie auf einen Master-Skill abbildet
- Bei Verstoß: Generierung verwerfen, Fehler an UI, **kein** Download

Das ist die wichtigste Testfamilie (`TESTING.md`).

## Zusammenspiel Rollenprofil vs. Stelle

1. Stelle kommt rein.
2. `role_score.py` liefert Familien-Scores; LLM nur bei knappem Abstand oder zur Anreicherung. Detection liefert `role_family`.
3. Wenn ein gespeichertes Profil zu dieser Familie existiert → als Default-Sicht laden.
4. Job-Keywords und Muss-Anforderungen **überlagern** das Profil (Reihenfolge kann sich pro Stelle ändern).
5. Nutzer sieht Diff „Profil COO, angepasst an diese Stelle“.
6. Optional: „Profil mit diesen Änderungen aktualisieren“ oder „nur für diese Bewerbung“.

## UX-Copy (Ton)

Nicht: „Wir haben Ihren CV für den CEO-Job optimiert.“  
Sondern: „Diese Stelle zielt auf Geschäftsführung (CEO). Vorschlag: P&L und Organisation nach oben, operative KPIs kürzen. Keine Fakten werden geändert.“

Transparenz schafft Vertrauen. ATS-Tools, die heimlich umschreiben, sind das Gegenteil.

## Abgrenzung zu reinem Keyword-Stuffing

Keyword-Coverage ist ein **Constraint**, nicht die Zielfunktion. Natürliche Integration in existierende Bullets. Kein Skill-Dump „CEO, Leadership, Vision, Synergies“ am Ende. Maximal die Skills, die im Master sind, in der für die Rolle richtigen Reihenfolge.
