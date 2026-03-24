"""Category detail API endpoint."""
from fastapi import APIRouter, HTTPException
from api.services.dragon_keeper.category_detail import get_category_detail

router = APIRouter()


@router.get("/category/{category_id}")
def category_detail(category_id: str):
    data = get_category_detail(category_id)
    if data["category_name"] == "Unknown" and data["transaction_count"] == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return data
