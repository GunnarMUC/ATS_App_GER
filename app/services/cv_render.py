from __future__ import annotations

from typing import Any

from app.models.schemas import CVStructure


def load_cv(facts: dict[str, Any] | CVStructure) -> CVStructure:
    if isinstance(facts, CVStructure):
        return facts
    return CVStructure.model_validate(facts)


def format_month(value: str, language: str = "de") -> str:
    if value == "present":
        return "heute" if language == "de" else "present"
    if len(value) >= 7 and value[4] == "-":
        y, m = value[:4], value[5:7]
        return f"{m}/{y}"
    return value


def contact_line(cv: CVStructure) -> str:
    p = cv.personal
    parts = [x for x in (p.city, p.phone, p.email, p.linkedin or p.xing) if x]
    return " · ".join(parts)


def section_labels(language: str) -> dict[str, str]:
    if language == "en":
        return {
            "profile": "Profile",
            "experience": "Experience",
            "education": "Education",
            "skills": "Skills",
            "languages": "Languages",
            "certifications": "Certifications",
        }
    return {
        "profile": "Profil",
        "experience": "Berufserfahrung",
        "education": "Ausbildung",
        "skills": "Kompetenzen",
        "languages": "Sprachen",
        "certifications": "Zertifikate",
    }
