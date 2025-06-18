from http import HTTPStatus

from fastapi.testclient import TestClient

from fastapi_zero.app import app

client = TestClient(app)


def test_root_deve_retornar_ola_mundo():
    response = client.get('/')
    assert response.json() == {'message': 'Olá mundo!'}
    assert response.status_code == HTTPStatus.OK


def test_html_deve_retornar_um_html():
    response = client.get('/html')
    assert response.status_code == HTTPStatus.OK
    assert response.headers['content-type'].startswith('text/html')
    assert '<html>' in response.text
    assert 'Olá, Mundo!' in response.text
