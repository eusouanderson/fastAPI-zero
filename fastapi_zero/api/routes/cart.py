from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fastapi_zero.db.models import Cart, CartItem, PriceRecord, Product
from fastapi_zero.db.session import get_session
from fastapi_zero.schemas import AddToCartRequest, CartItemPublic, CartResponse

router = APIRouter(tags=['cart'])


@router.post('/cart/items', status_code=HTTPStatus.CREATED)
def add_to_cart(
    payload: AddToCartRequest, session: Session = Depends(get_session)
):
    # For this MVP we use a single cart (id=1).
    # In a real app tie carts to users/sessions.
    cart = session.scalar(select(Cart).where(Cart.id == 1))
    if not cart:
        cart = Cart()
        session.add(cart)
        session.commit()
        session.refresh(cart)

    # ensure product exists
    product = session.scalar(
        select(Product).where(Product.id == payload.product_id)
    )
    if not product:
        raise HTTPException(status_code=404, detail='product not found')

    item = session.scalar(
        select(CartItem).where(
            (CartItem.cart_id == cart.id)
            & (CartItem.product_id == payload.product_id)
        )
    )

    if item:
        item.quantity += payload.quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        session.add(item)

    session.commit()
    session.refresh(item)

    return {
        'id': item.id,
        'product_id': item.product_id,
        'quantity': item.quantity,
    }


@router.get('/cart', response_model=CartResponse)
def get_cart(session: Session = Depends(get_session)):
    cart = session.scalar(select(Cart).where(Cart.id == 1))
    if not cart:
        return CartResponse(id=0, items=[])

    price_subquery = (
        select(
            PriceRecord.product_id,
            func.min(PriceRecord.price).label('min_price'),
        )
        .group_by(PriceRecord.product_id)
        .subquery()
    )

    rows = session.execute(
        select(CartItem, Product, PriceRecord)
        .where(CartItem.cart_id == cart.id)
        .join(Product, CartItem.product_id == Product.id)
        .join(
            price_subquery,
            Product.id == price_subquery.c.product_id,
            isouter=True,
        )
        .join(
            PriceRecord,
            (PriceRecord.product_id == price_subquery.c.product_id)
            & (PriceRecord.price == price_subquery.c.min_price),
            isouter=True,
        )
    ).all()

    items = []
    for item, product, price_record in rows:
        items.append(
            CartItemPublic(
                id=item.id,
                product_id=item.product_id,
                name=product.display_name,
                quantity=item.quantity,
                lowest_price=price_record.price if price_record else None,
                currency=price_record.currency if price_record else None,
                source_url=price_record.source_url if price_record else None,
            )
        )

    return CartResponse(id=cart.id, items=items)


@router.delete('/cart/items/{item_id}', status_code=HTTPStatus.NO_CONTENT)
def remove_item(item_id: int, session: Session = Depends(get_session)):
    item = session.scalar(select(CartItem).where(CartItem.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail='item not found')
    session.delete(item)
    session.commit()
