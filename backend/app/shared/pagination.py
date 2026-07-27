from dataclasses import dataclass

from fastapi import Query


@dataclass(frozen=True)
class PaginationParams:
    offset: int = 0
    limit: int = 20


def pagination_dependency(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(offset=offset, limit=limit)


class PaginatedResponse[T]:
    def __init__(self, *, items: list[T], total: int, offset: int, limit: int) -> None:
        self.items = items
        self.total = total
        self.offset = offset
        self.limit = limit

    def model_dump(self) -> dict[str, object]:
        return {
            "items": self.items,
            "total": self.total,
            "offset": self.offset,
            "limit": self.limit,
        }
