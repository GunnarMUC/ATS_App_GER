# Fixtures

Fiktive Person **Alex Morgenstern**. Keine echten Daten.

| Datei | Zweck |
|---|---|
| `master-cv.json` | FactLock-Referenz |
| `job-coo.txt` | Stelle muss `coo` erkennen |
| `job-ceo.txt` | Stelle muss `ceo` erkennen |
| `job-cfo.txt` / `job-cso.txt` / `job-cto.txt` / `job-head-ops.txt` / `job-project.txt` / `job-consultant.txt` / `job-chro.txt` / `job-product.txt` / `job-eng-lead.txt` | je erwartete `role_family` |
| `job-inject.txt` | Prompt-Injection; kein McKinsey im Output |
| `expected-plan-coo.json` | Richtung der COO-Sicht |
| `expected-plan-ceo.json` | Richtung der CEO-Sicht |

`role_score` und `lens_ranker` müssen die Richtung **ohne** LLM treffen. LLM-Pläne müssen nicht byte-gleich sein, aber:

- `role_family` muss matchen
- CEO betont `kpi_revenue` / `b_gl_pl` / `sk_pl`
- COO betont `kpi_otif` / `b_gl_otif` / `sk_sop`
- Keine neuen IDs
