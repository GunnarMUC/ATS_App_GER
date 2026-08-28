# Update1.md – Empfehlungen für ATS_App_GER

Repo: `github.com/GunnarMUC/ATS_App_GER`
Ziel: Gezielte Weiterentwicklung mit bestem Aufwand-Nutzen-Verhältnis. Kein Feature-Creep, kein Bruch der Lokal/Privacy-Prinzipien.
Format: Taskliste mit Checkboxen, nach Priorität gestaffelt. Zur Übergabe an opencode.

Legende Priorität:
- 🟢 P1 = hoher Nutzen, geringer Aufwand – zuerst machen
- 🟡 P2 = sinnvoll, mittlerer Aufwand – nach P1
- 🔴 P3 = bewusst zurückstellen (Negativliste)

---

## 🟢 P1 – Top 5 (zuerst umsetzen)

### 1. Rollenfamilien ausbauen
Das Alleinstellungsmerkmal. Mit nur CEO/COO bleibt die App eine Demo.

- [ ] `app/domain/role_taxonomy.py` erweitern um weitere ROLE_FAMILIES:
      CTO, CFO, Head of Operations, Projektmanager, Berater/Consultant,
      Vertriebsleiter, HR-Leitung, Produktmanager, Data/Engineering-Lead
- [ ] `app/domain/lens_weights.json` pro neuer Rolle:
      `terms` (Boost), `downweight_terms`, reasoning-Kommentar
- [ ] `spec/ROLE-ADAPTATION.md` um neue Rollen ergänzen
- [ ] Fixtures unter `spec/fixtures/`:
      pro Rolle eine Beispiel-Stellenanzeige (z. B. `job-cto.txt`, `job-cfo.txt`)
- [ ] Tests in `tests/test_role_score.py` erweitern:
      jede neue Rolle wird als `top.role_family` erkannt
- [ ] Lens-Ranker-Tests für mind. 2 neue Rollen (andere Reihenfolge/Skills als CEO/COO)

### 2. Bewerbungs-Status-Dashboard
Macht die App zum Werkzeug für den Alltag, nicht nur zum Generator.

- [ ] Neues ORM-Modell `Application` (status, job_id, created_at, updated_at,
      notes, stage: offen/eingereicht/interview/absage/angebot/zusage)
- [ ] Alembic-Migration dafür (nicht nur `create_all`)
- [ ] Router `app/routers/applications.py` (Liste, Anlegen, Status-Update, Löschen)
- [ ] Template `dashboard.html` erweitern: Tabelle aller Bewerbungen mit Status-Badge
- [ ] Verknüpfung: generiertes Dokument ↔ Bewerbung (FK auf GeneratedDocument)
- [ ] Test: Bewerbung anlegen, Status wechseln, erscheint im Dashboard
- [ ] Nav-Eintrag „Übersicht" zeigt Dashboard statt nur Start

### 3. Vor-/Nachher-Vergleich (Master vs. rollenspezifisch)
Macht FactGuard-Fairstellung im UI sichtbar → Vertrauen.

- [ ] View/Route `/cv/compare/{job_id}`: Master-CV (gesperrt) neben gerolltem CV
- [ ] Diff-Highlight: geänderte Reihenfolge, ausgeblendete Stationen, betonte Skills
- [ ] FactGuard-Ergebnis inline zeigen (OK / Warnungen-Liste)
- [ ] Template `compare.html` (zweispaltig, kennzeichne Änderungen)
- [ ] Test: Vergleichsseite lädt, zeigt beide Seiten, Guard-Status sichtbar

### 4. Backup/Export als ZIP
Datenportabilität – bei lokalem Tool essenziell.

- [ ] Route `/settings/backup` → ZIP mit `ats_app.db` + `data/uploads` + `data/generated`
- [ ] Optional Passwortschutz (zip-PW) via Einstellung
- [ ] Restore-Route `/settings/restore` (Upload ZIP, validiert, importiert)
- [ ] Template-Button in `settings.html` unter „Daten"
- [ ] Test: Backup erstellen, Inhalt prüfen, Restore in leere DB

### 5. CSRF-Middleware + harter Loopback-Check
Schließt die eine offene Sicherheitslücke sauber.

- [ ] CSRF-Middleware (z. B. `starlette-csrf` oder Double-Submit-Token) für alle POST-Formulare
- [ ] CSRF-Token in `base.html` Helper, in alle Formulare einbinden
- [ ] Loopback-Check verschärfen: `APP_HOST != 127.0.0.1/localhost/::1` → App startet nicht
      (außer explizit `APP_ALLOW_NONLOCAL=true`)
- [ ] `spec/SECURITY.md` aktualisieren: CSRF jetzt aktiv, Loopback enforced
- [ ] Test: POST ohne CSRF-Token → 403; mit Token → ok; non-loopback start blockiert

---

## 🟡 P2 – nach den Top 5

### 6. LLM-Pfade test-abdecken
- [ ] Mock für `app.services.llm_client.generate` in `conftest.py`
- [ ] Tests für `cv_generator` (mit und ohne LLM-Pfad), `cover_generator`, `job_analyzer`-LLM-Pfad
- [ ] CI bleibt grün auch ohne Ollama (ist schon, aber LLM-Code ungetestet)

### 7. Keyword-Gap mit Rückgriff auf existierende Fakten
Macht das Versprechen „Lücken werden nicht erfunden" konkret nutzbar.

- [ ] Im Anpassungsplan: pro fehlendes Keyword Vorschlag aus vorhandenem FactLock
      („Lücke X könnte durch KPI Y / Skill Z gedeckt werden – keine Erfindung")
- [ ] `lens_planner.py`: `gaps`-Liste mit Vorschlägen anreichern, nur aus Facts
- [ ] Template `plan.html`: Lücken + Vorschläge anzeigen, keine „erfinden"-Option
- [ ] Test: Lücke erkannt, Vorschlag verweist auf existierende Fact-ID

### 8. Alembic-Migration aktivieren
- [ ] Erste echte Migration statt `init_db()` → `create_all`
- [ ] `alembic/versions/` befüllen, `init_db` auf `alembic upgrade head` umstellen
- [ ] Docker/Setup-Doku: Migration läuft automatisch beim Start

### 9. Vorgefertigte Rollenprofil-Templates
- [ ] Vorlagen wie „COO Logistik", „CTO SaaS", „Projektmanager Bau" als startbare Vorlagen
- [ ] In `settings.html` oder `profiles.html` als „Aus Vorlage laden"
- [ ] Senkt Einstiegshürde für neue Nutzer

### 10. Optionale OCR (Tesseract) für Scan-PDFs
- [ ] Optionale Dependency (`pytesseract` + System-Tesseract), nicht in `requirements.txt` default
- [ ] `document_parser.py`: bei wenig Text aus PDF → OCR-Fallback, falls Tesseract vorhanden
- [ ] Einstellung „OCR aktivieren" (opt-in)
- [ ] Hinweis in README: OCR ist optional und nur lokal

---

## 🔴 P3 – bewusst zurückstellen (Negativliste)

Diese Punkte bewusst NICHT angehen – hoher Aufwand, geringer/kein Nutzen oder Bruch der Prinzipien:

- Multi-User / Authentifizierung (bricht „lokales Einzelplatz-Tool"-Versprechen)
- Cloud-Sync / Cloud-SDK in der App (zerstört Datenschutz-Keise)
- Jobbörsen-/LinkedIn-Scraping (in AGENTS.md verboten, rechtlich heikel)
- Eigenes OCR-Engine schreiben (Tesseract-Anbindung reicht)
- Voll-i18n / komplette EN-UI (Job-EN-Output funktioniert schon)
- Docker-Erzwingung (v1 explizit kein Docker; nur optional anbieten)
- Neues Frontend-Framework React/Vue (htmx+Alpine reicht)

---

## Empfohlene Reihenfolge

1. **P1.1 Rollenfamilien** (größter Produkt-Nutzen, geringster Aufwand)
2. **P1.2 Dashboard** (Alltagswert)
3. **P1.5 CSRF + Loopback** (Sicherheit sauber abschließen)
4. **P1.3 Vergleichsansicht** (Vertrauen/Transparenz)
5. **P1.4 Backup/Export** (Datenhoheit)
6. **P2.7 Keyword-Gap-Rückgriff** (macht FactGuard-Konzept komplett)
7. **P2.6 LLM-Tests** (CI-Stabilität)
8. **P2.8 Alembic** (saubere Schema-Evolution)
9. **P2.9 Rollen-Templates** (Einstiegshürde)
10. **P2.10 OCR optional** (Abrundung)

## Akzeptanzkriterien „Update 1 fertig"

- [ ] Mindestens 6 Rollenfamilien funktionieren (Tests grün)
- [ ] Dashboard zeigt Bewerbungen mit Status
- [ ] Vergleichsansicht lädt für jede generierte Bewerbung
- [ ] Backup-ZIP lässt sich in frischer Instanz restoren
- [ ] POST ohne CSRF-Token → 403
- [ ] Non-Loopback-Start blockiert (außer explizit freigeschaltet)
- [ ] CI grün, ruff bindend, alle neuen Tests bestanden
- [ ] Keine neuen Cloud-Dependencies, kein Scraping, keine Auth – Prinzipien erhalten