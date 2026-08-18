from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination_params(
    page: int = Query(1, ge=1, description="Page number, starting at 1"),
    page_size: int = Query(31, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)
