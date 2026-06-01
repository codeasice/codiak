"""Category Explorer API endpoints."""
from fastapi import APIRouter
from api.services.dragon_keeper.category_explorer import (
    get_categories_with_spending,
    get_category_explorer,
)

router = APIRouter()


@router.get("/category-explorer/categories")
def list_categories():
    return get_categories_with_spending()


@router.get("/category-explorer")
def category_explorer(category_name: str = "Dining Out", weeks: int = 12):
    return get_category_explorer(category_name, weeks)
