# FILE-STRUCTURE.md

Repo-Wurzel bleibt schlank. Spec unter `spec/`, Code unter `app/`, Tests unter `tests/`.

```
ATS_App_GER/
  README.md
  LICENSE
  AGENTS.md                 # OpenCode liest hier zuerst
  .gitignore
  .env.example              # ab M1
  requirements.txt          # ab M1
  requirements-dev.txt      # ab M1
  alembic.ini               # ab M1
  alembic/versions/         # ab M1
  spec/
    README.md               # Karte dieses Ordners
    MASTERPLAN.md
    CONSTRAINTS.md
    DECISIONS.md
    …                       # übrige Spec-Markdowns
    prompts/                # → Kopie nach app/prompts/
    schemas/                # Vertrag; App spiegelt in Pydantic
    fixtures/
    domain/
      aliases_de.json       # → Kopie nach app/domain/
      lens_weights.json
  app/                      # Anwendung, ab M1
    README.md
    main.py
    config.py
    database.py
    domain/
    models/
    routers/
    services/
    prompts/
    templates/
    static/
      vendor/
      css/app.css
      js/app.js
  tests/                    # ab M1
    fixtures/               # Kopie oder Pfad auf spec/fixtures
  data/                     # gitignored
```

`data/` und `.env` in `.gitignore`. Keine echten CVs committen.
