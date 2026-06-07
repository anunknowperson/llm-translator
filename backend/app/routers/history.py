from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Translation
from app.schemas import (
    DailyStat,
    LanguagePairStat,
    StatsResponse,
    TranslationHistoryItem,
    TranslationHistoryPage,
)

router = APIRouter(tags=["history"])


@router.get("/history", response_model=TranslationHistoryPage)
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> TranslationHistoryPage:
    total = await session.scalar(select(func.count(Translation.id)))

    rows = await session.scalars(
        select(Translation)
        .order_by(Translation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [TranslationHistoryItem.model_validate(row) for row in rows.all()]
    return TranslationHistoryPage(items=items, total=total or 0, limit=limit, offset=offset)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(session: AsyncSession = Depends(get_session)) -> StatsResponse:
    total = await session.scalar(select(func.count(Translation.id))) or 0

    pair_rows = await session.execute(
        select(Translation.source_lang, Translation.target_lang, func.count(Translation.id))
        .group_by(Translation.source_lang, Translation.target_lang)
        .order_by(func.count(Translation.id).desc())
    )
    by_pair = [
        LanguagePairStat(source_lang=src, target_lang=tgt, count=count)
        for src, tgt, count in pair_rows.all()
    ]

    since = datetime.now(timezone.utc) - timedelta(days=14)
    day_expr = func.date(Translation.created_at)
    day_rows = await session.execute(
        select(day_expr, func.count(Translation.id))
        .where(Translation.created_at >= since)
        .group_by(day_expr)
        .order_by(day_expr)
    )
    by_day = [DailyStat(date=str(day), count=count) for day, count in day_rows.all()]

    return StatsResponse(total_translations=total, by_language_pair=by_pair, by_day=by_day)
