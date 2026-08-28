from __future__ import annotations

ROLE_FAMILIES: list[str] = [
    "ceo",
    "coo",
    "cfo",
    "cso_sales",
    "head_logistics",
    "plant_ops",
    "program",
    "functional_expert",
    "other",
]

LABELS_DE: dict[str, str] = {
    "ceo": "CEO / Geschäftsführung",
    "coo": "COO / Operations",
    "cfo": "CFO / Finanzen",
    "cso_sales": "CSO / Vertrieb",
    "head_logistics": "Leiter Logistik / Supply Chain",
    "plant_ops": "Werkleitung / Plant Ops",
    "program": "Programm / Transformation",
    "functional_expert": "Fachliche Expertenrolle",
    "other": "Sonstige / unklar",
}
