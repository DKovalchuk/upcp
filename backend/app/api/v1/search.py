from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.search.service import SearchService
from app.shared.database import get_session

router = APIRouter(tags=["search"])


@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    session: Session = Depends(get_session),
) -> list[dict[str, str]]:  # noqa: B008
    return SearchService(session).search(query=q, limit=limit)
