from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Personal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1)
    city: str = ""
    country: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    xing: str = ""
    address_line: str = ""
    birth_date: str | None = None
    nationality: str | None = None
    marital_status: str | None = None


class Bullet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    kpi_ids: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    employer: str
    title: str
    start: str
    end: str
    location: str = ""
    bullets: list[Bullet] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)


class Education(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    institution: str
    degree: str
    field: str = ""
    start: str | None = None
    end: str | None = None


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    category: Literal["leadership", "functional", "technical", "language", "other"] = "other"


class Language(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    level: str


class Certification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    year: str | None = None
    issuer: str | None = None


class Kpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    value: str
    raw: str = ""
    experience_id: str = ""


class CVStructure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    language: Literal["de", "en"] = "de"
    personal: Personal
    summary: str = ""
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    kpis: list[Kpi] = Field(default_factory=list)

    def to_canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
