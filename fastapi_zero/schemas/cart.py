from typing import List

from pydantic import BaseModel


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemPublic(BaseModel):
    id: int
    product_id: int
    name: str | None
    quantity: int
    lowest_price: float | None = None
    currency: str | None = None
    source_url: str | None = None


class CartResponse(BaseModel):
    id: int
    items: List[CartItemPublic]
