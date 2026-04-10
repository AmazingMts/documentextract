from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Source
from app.schemas import SourceOut

router = APIRouter()


@router.get("/sources", response_model=List[SourceOut])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.company))
    return result.scalars().all()
