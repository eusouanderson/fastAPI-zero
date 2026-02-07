# ruff: noqa: PLR2004, E501
from http import HTTPStatus

from fastapi_zero.db.models import Cart, CartItem, PriceRecord, Product


def _create_product(session, *, name="Produto Teste", normalized="produto-teste-1"):
    product = Product(
        display_name=name,
        normalized_name=normalized,
        category="hardware",
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def test_get_cart_empty(client):
    response = client.get("/cart")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"id": 0, "items": []}


def test_add_to_cart_creates_item(client, session):
    product = _create_product(session)

    response = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 2},
    )

    assert response.status_code == HTTPStatus.CREATED
    payload = response.json()
    assert payload["product_id"] == product.id
    assert payload["quantity"] == 2

    cart = client.get("/cart").json()
    assert cart["id"] == 1
    assert cart["items"][0]["product_id"] == product.id
    assert cart["items"][0]["name"] == product.display_name


def test_add_to_cart_existing_item_increments_quantity(client, session):
    product = _create_product(session, normalized="produto-teste-inc")

    response = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
    )
    assert response.status_code == HTTPStatus.CREATED

    response = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 2},
    )
    assert response.status_code == HTTPStatus.CREATED

    cart = client.get("/cart").json()
    assert cart["items"][0]["quantity"] == 3


def test_add_to_cart_missing_product(client):
    response = client.post(
        "/cart/items",
        json={"product_id": 9999, "quantity": 1},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "product not found"}


def test_cart_includes_lowest_price_and_link(client, session):
    product = _create_product(session, normalized="produto-teste-2")

    cart = Cart()
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    session.add(item)

    session.add_all(
        [
            PriceRecord(
                product_id=product.id,
                source_url="https://example.com/a",
                price=199.9,
                currency="BRL",
            ),
            PriceRecord(
                product_id=product.id,
                source_url="https://example.com/b",
                price=149.9,
                currency="BRL",
            ),
        ]
    )
    session.commit()

    response = client.get("/cart")
    assert response.status_code == HTTPStatus.OK
    items = response.json()["items"]
    assert items[0]["lowest_price"] == 149.9
    assert items[0]["source_url"] == "https://example.com/b"


def test_remove_item(client, session):
    product = _create_product(session, normalized="produto-teste-3")
    cart = Cart()
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    session.add(item)
    session.commit()
    session.refresh(item)

    response = client.delete(f"/cart/items/{item.id}")
    assert response.status_code == HTTPStatus.NO_CONTENT

    cart_response = client.get("/cart")
    assert cart_response.status_code == HTTPStatus.OK
    assert cart_response.json()["items"] == []


def test_remove_item_not_found(client):
    response = client.delete("/cart/items/9999")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "item not found"}
