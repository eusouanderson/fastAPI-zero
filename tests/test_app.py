from http import HTTPStatus


def test_root_deve_retornar_ola_mundo(client):
    response = client.get('/')
    assert response.json() == {'message': 'Olá mundo!'}
    assert response.status_code == HTTPStatus.OK


def test_create_user(client):
    response = client.post(
        '/users/',
        json={
            'username': 'teste',
            'email': 'teste@teste.com',
            'password': 'teste123',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': 'teste',
        'email': 'teste@teste.com',
        'id': 1,
    }


def test_read_users(client):
    response = client.get('/users/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'users': [
            {
                'username': 'teste',
                'email': 'teste@teste.com',
                'id': 1,
            },
        ]
    }


def test_update_user(client):
    response = client.put(
        '/users/1',
        json={
            'username': 'eusouanderson',
            'email': 'eusouanderson@eusouanderson.com',
            'password': 'teste123',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'eusouanderson',
        'email': 'eusouanderson@eusouanderson.com',
        'id': 1,
    }


def test_update_user_error(client):
    response = client.put(
        '/users/-1',
        json={
            'username': 'eusouanderson',
            'email': 'eusouanderson@eusouanderson.com',
            'password': 'teste123',
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User Not Found'}


def test_delete_user(client):
    response = client.delete(
        '/users/1',
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'eusouanderson',
        'email': 'eusouanderson@eusouanderson.com',
        'id': 1,
    }


def test_delete_error(client):
    response = client.delete('/users/-1')
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User Not Found'}
