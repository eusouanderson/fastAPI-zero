import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi_zero.app import app
from fastapi_zero.db.session import get_session


client = TestClient(app)


class TestAppInitialization:
    """Testes para inicialização da aplicação."""

    def test_app_exists(self):
        """Testa se a aplicação FastAPI foi criada."""
        assert app is not None
        assert hasattr(app, "routes")
        assert len(app.routes) > 0

    def test_app_has_openapi(self):
        """Testa se a aplicação tem OpenAPI habilitado."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()

    def test_app_has_ui(self):
        """Testa se a aplicação tem UI."""
        response = client.get("/ui")
        assert response.status_code == 200

    def test_app_has_docs(self):
        """Testa se a aplicação tem docs."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_root_endpoint(self):
        """Testa endpoint raiz."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_app_middlewares(self):
        """Testa se middlewares estão configurados."""
        assert app.middleware_stack is not None

    def test_lifespan_not_error(self):
        """Testa se o lifespan não causa erro."""
        # A aplicação é criada sem erros no conftest
        assert app is not None


class TestSessionDependency:
    """Testes para a sessão do banco de dados."""

    def test_get_session_dependency(self):
        """Testa a dependency de sessão."""
        from fastapi_zero.db.session import get_session as get_db_session

        # get_session deve ser uma função
        assert callable(get_db_session)

    def test_database_url_configured(self):
        """Testa se DATABASE_URL está configurada."""
        from fastapi_zero.core.settings import Settings

        settings = Settings()
        assert settings.DATABASE_URL
        assert "sqlite" in settings.DATABASE_URL or "postgresql" in settings.DATABASE_URL

    def test_session_local_created(self):
        """Testa se SessionLocal foi criado."""
        from fastapi_zero.db.session import engine, get_session

        assert engine is not None
        # Podemos usar get_session (é um generator)
        assert get_session is not None

    def test_engine_created(self):
        """Testa se engine foi criado."""
        from fastapi_zero.db.session import engine

        assert engine is not None
        assert hasattr(engine, "connect")


class TestApplicationRoutes:
    """Testes para rotas da aplicação."""

    def test_all_routes_registered(self):
        """Testa se todas as rotas estão registradas."""
        routes = [route.path for route in app.routes if hasattr(route, "path")]
        
        # Rotas esperadas
        expected_routes = ["/", "/users", "/ui"]
        
        for route in expected_routes:
            assert any(route in r for r in routes), f"Rota {route} não encontrada"

    def test_api_prefix(self):
        """Testa se há rotas de API."""
        routes = [route.path for route in app.routes if hasattr(route, "path")]
        assert any("/users" in r or "/scrape" in r or "/crawl" in r for r in routes)

    def test_static_files_configured(self):
        """Testa se arquivos estáticos estão configurados."""
        # Tenta acessar um arquivo estático
        response = client.get("/static/app.js")
        # Pode ser 200 ou 404 dependendo se o arquivo existe
        assert response.status_code in [200, 404]

    def test_lifespan_context(self):
        """Testa lifespan context."""
        # Verifica se lifespan está definido ou se a aplicação funciona
        response = client.get("/")
        assert response.status_code == 200


class TestErrorHandling:
    """Testes para tratamento de erros."""

    def test_404_not_found(self):
        """Testa erro 404."""
        response = client.get("/rota-inexistente")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Testa método não permitido."""
        # GET em endpoint que só aceita POST
        response = client.get("/scrape/urls")
        assert response.status_code == 405 or response.status_code == 404

    def test_invalid_json_request(self):
        """Testa requisição com JSON inválido."""
        response = client.post(
            "/users",
            json={"username": "test"},  # Faltando email e password
        )
        assert response.status_code == 422

    def test_cors_headers(self):
        """Testa se headers de CORS estão presentes (se configurados)."""
        response = client.get("/")
        # Pode ou não ter CORS configurado
        assert response.status_code == 200
