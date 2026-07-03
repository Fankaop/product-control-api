from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from core.dependencies import DBSession

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: DBSession) -> JSONResponse:
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )
    return JSONResponse(content={"status": "ok", "database": "ok"})
