from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import llm_client
from app.services.settings_service import ensure_settings_row

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: Session = Depends(get_db)) -> dict:
    ensure_settings_row(db)
    return await llm_client.check_health(db)
