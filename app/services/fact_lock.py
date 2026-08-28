from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.orm import FactLock, ReferenceCV
from app.models.schemas import CVStructure


def canonical_hash(facts: dict[str, Any] | CVStructure) -> str:
    if isinstance(facts, CVStructure):
        data = facts.to_canonical_dict()
    else:
        data = facts
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_active_lock(db: Session) -> FactLock | None:
    return (
        db.query(FactLock)
        .filter(FactLock.is_active.is_(True))
        .order_by(FactLock.confirmed_at.desc())
        .first()
    )


def commit_lock(
    db: Session,
    *,
    reference_cv_id: str,
    facts: dict[str, Any] | CVStructure,
) -> FactLock:
    cv = db.get(ReferenceCV, reference_cv_id)
    if cv is None:
        raise ValueError("reference_cv_not_found")

    if isinstance(facts, CVStructure):
        structure = facts
    else:
        structure = CVStructure.model_validate(facts)
    facts_dict = structure.to_canonical_dict()
    digest = canonical_hash(facts_dict)

    for old in db.query(FactLock).filter(FactLock.is_active.is_(True)).all():
        old.is_active = False
        db.add(old)

    lock = FactLock(
        reference_cv_id=reference_cv_id,
        facts_json=facts_dict,
        content_hash=digest,
        confirmed_at=datetime.now(UTC),
        is_active=True,
    )
    db.add(lock)
    cv.structured_json = facts_dict
    db.add(cv)
    db.commit()
    db.refresh(lock)
    return lock


def save_draft(
    db: Session, reference_cv_id: str, facts: dict[str, Any] | CVStructure
) -> ReferenceCV:
    cv = db.get(ReferenceCV, reference_cv_id)
    if cv is None:
        raise ValueError("reference_cv_not_found")
    if isinstance(facts, CVStructure):
        data = facts.to_canonical_dict()
    else:
        data = CVStructure.model_validate(facts).to_canonical_dict()
    cv.structured_json = data
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv
