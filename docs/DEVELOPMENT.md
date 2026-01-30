# 📖 Guia de Desenvolvimento

Documentação técnica para contribuintes e desenvolvedores.

---

## 🏗️ Arquitetura

### Padrão de Camadas (Layered Architecture)

```
┌─────────────────────────────────────┐
│       FastAPI Routes (API)          │ ← HTTP Endpoints
├─────────────────────────────────────┤
│    Pydantic Schemas (DTOs)          │ ← Validação/Serialização
├─────────────────────────────────────┤
│     Business Logic (Services)       │ ← Lógica Principal
├─────────────────────────────────────┤
│  Database (SQLAlchemy + Alembic)    │ ← Persistência
├─────────────────────────────────────┤
│        SQLite (or PostgreSQL)       │ ← Dados
└─────────────────────────────────────┘
```

### Componentes Principais

#### 1. **Core** - Configurações
```python
# fastapi_zero/core/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./database.db"
    debug: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000
```

#### 2. **DB** - Banco de Dados
```python
# fastapi_zero/db/models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
```

#### 3. **Services** - Lógica de Negócio
```python
# fastapi_zero/services/scraper.py
class Scraper:
    async def scrape_urls(self, urls: list[str]) -> list[Product]:
        # Implementação do scraping
        pass
```

#### 4. **Schemas** - Validação Pydantic
```python
# fastapi_zero/schemas/__init__.py
from pydantic import BaseModel

class ScrapeUrlsRequest(BaseModel):
    urls: list[str]
    max_concurrency: int = 20
```

#### 5. **API** - Endpoints FastAPI
```python
# fastapi_zero/api/routes/scrape.py
@app.post("/scrape/urls")
async def scrape_urls(payload: ScrapeUrlsRequest):
    scraper = Scraper()
    results = await scraper.scrape_urls(payload.urls)
    return {"total": len(results), "products": results}
```

---

## 🔄 Fluxo de Dados

### Exemplo: POST /scrape/urls

```
1. Cliente envia JSON
   {
     "urls": ["https://..."],
     "max_concurrency": 20
   }
   
2. FastAPI recebe e valida com Pydantic
   → ScrapeUrlsRequest validado
   
3. API route chama Service
   → scraper.scrape_urls(urls)
   
4. Service usa DB para dados
   → session.add(Product(...))
   
5. Service retorna resultado
   → list[ScrapedItem]
   
6. API serializa com Response Schema
   → ScrapeResponse validado
   
7. FastAPI envia JSON
   {
     "total": 2,
     "products": [...]
   }
```

---

## 📝 Padrões de Código

### Naming Conventions

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Classe | PascalCase | `class UserRepository` |
| Função | snake_case | `def get_user_by_id()` |
| Constante | UPPER_SNAKE_CASE | `MAX_RETRIES = 3` |
| Private | `_leading_underscore` | `def _validate_email()` |
| Async | `async def` | `async def fetch_data()` |

### Type Hints (Obrigatório)

```python
# ✅ Correto
def process_items(items: list[str]) -> dict[str, int]:
    return {"count": len(items)}

async def fetch_data(url: str, timeout: float = 10.0) -> str | None:
    try:
        response = await client.get(url, timeout=timeout)
        return response.text
    except Exception:
        return None

# ❌ Evitar
def process_items(items):
    return {"count": len(items)}
```

### Imports Organizados

```python
# 1. Standard Library
import asyncio
import json
from dataclasses import dataclass
from typing import Optional

# 2. Third-party
import httpx
from sqlalchemy import Column, Integer
from pydantic import BaseModel

# 3. Local
from fastapi_zero.core.settings import settings
from fastapi_zero.db.session import get_session
```

### Docstrings

```python
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calcula o preço final após desconto.
    
    Args:
        price: Preço original em BRL
        discount_percent: Percentual de desconto (0-100)
    
    Returns:
        Preço final após aplicar desconto
    
    Raises:
        ValueError: Se percentual estiver fora do range
    
    Example:
        >>> calculate_discount(100.0, 10)
        90.0
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("Desconto deve estar entre 0 e 100")
    return price * (1 - discount_percent / 100)
```

---

## 🧪 Testando

### Estrutura de Testes

```
tests/
├── conftest.py              # Fixtures compartilhadas
├── test_app.py              # Testes dos endpoints
├── test_db.py               # Testes do banco
└── test_scraper.py          # Testes do scraper
```

### Exemplo de Teste

```python
# tests/test_scraper.py
import pytest
from fastapi_zero.services.scraper import Scraper

@pytest.mark.asyncio
async def test_scrape_valid_url(mock_httpx_client):
    """Testa se o scraper extrai título e preço corretamente."""
    scraper = Scraper()
    
    # Mock da resposta HTTP
    mock_httpx_client.get.return_value.text = """
        <html>
            <h1>GPU RTX 4070</h1>
            <meta property="product:price:amount" content="2999.99">
        </html>
    """
    
    result = await scraper.scrape_urls(["https://example.com/product"])
    
    assert result[0].title == "GPU RTX 4070"
    assert result[0].price == 2999.99
```

### Executando Testes

```bash
# Todos os testes
poetry run pytest

# Com cobertura
poetry run pytest --cov=fastapi_zero --cov-report=html

# Teste específico
poetry run pytest tests/test_scraper.py::test_scrape_valid_url -v

# Modo watch
poetry run pytest-watch --now

# Com output detalhado
poetry run pytest -vv --tb=long
```

---

## 🔍 Linting

### Regras Ativas

O projeto usa **Ruff** com as seguintes regras:
- **I** - isort (imports)
- **F** - Pyflakes (undefined names, duplicate imports)
- **E** - pycodestyle (whitespace, blank lines)
- **W** - pycodestyle warnings
- **PL** - Pylint (complexity, naming conventions)
- **PT** - pytest (test assertions)

### Violações Corrigidas (v1.0)

| Código | Descrição | Solução |
|--------|-----------|---------|
| PLR0913 | Too many function arguments | Usar dataclass com parâmetros |
| PLR0917 | Too many positional arguments | Idem |
| PLR0911 | Too many return statements | Consolidar retornos |
| PLW2901 | Loop variable overwritten | Usar nomes diferentes |
| PLR2004 | Magic number | Extrair para constante |

---

## 📦 Dependências

### Produção

```toml
[tool.poetry.dependencies]
python = "^3.13"
fastapi = "^0.109"
sqlalchemy = "^2.0"
alembic = "^1.13"
pydantic = "^2.5"
pydantic-settings = "^2.1"
httpx = "^0.25"
selectolax = "^0.3"
uvicorn = {version = "^0.27", extras = ["standard"]}
```

### Desenvolvimento

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
pytest-cov = "^4.1"
pytest-watch = "^4.2"
ruff = "^0.1"
```

---

## 🚀 CI/CD

### GitHub Actions (Exemplo)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run ruff check
      - run: poetry run pytest --cov
```

---

## 🐛 Debugging

### Modo Verbose do pytest

```bash
poetry run pytest -vv --tb=long --capture=no
```

### Breakpoint no Código

```python
def expensive_function(x):
    result = x * 2
    breakpoint()  # Abre debugger aqui
    return result
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Variável:", {"url": url, "price": price})
logger.info("Scraping iniciado")
logger.warning("Timeout aguardando resposta")
logger.error("Falha ao fazer parsing")
```

---

## 📚 Recursos Úteis

- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/concepts/)

---

**Last Updated**: January 29, 2026
