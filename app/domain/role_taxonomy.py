from __future__ import annotations

ROLE_FAMILIES: list[str] = [
    "ceo",
    "coo",
    "cfo",
    "cso_sales",
    "cto",
    "chro",
    "head_ops",
    "head_logistics",
    "plant_ops",
    "program",
    "project",
    "consultant",
    "product",
    "eng_lead",
    "functional_expert",
    "other",
]

LABELS_DE: dict[str, str] = {
    "ceo": "CEO / Geschäftsführung",
    "coo": "COO / Operations",
    "cfo": "CFO / Finanzen",
    "cso_sales": "CSO / Vertrieb",
    "cto": "CTO / Technik",
    "chro": "HR-Leitung / CHRO",
    "head_ops": "Head of Operations",
    "head_logistics": "Leiter Logistik / Supply Chain",
    "plant_ops": "Werkleitung / Plant Ops",
    "program": "Programm / Transformation",
    "project": "Projektmanager",
    "consultant": "Berater / Consultant",
    "product": "Produktmanager",
    "eng_lead": "Data / Engineering-Lead",
    "functional_expert": "Fachliche Expertenrolle",
    "other": "Sonstige / unklar",
}
