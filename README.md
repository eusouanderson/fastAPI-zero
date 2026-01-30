# 🚀 FastAPI Zero - Web Scraper de Preços

Um agregador de preços de produtos com web scraping assíncrono, organização em camadas e interface web responsiva.

> ⚡ FastAPI + SQLAlchemy + Alembic + Poetry + Ruff (linting zero violations)

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Recursos](#-recursos)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Iniciando o Servidor](#-iniciando-o-servidor)
- [API Endpoints](#-api-endpoints)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Desenvolvimento](#-desenvolvimento)
- [Testes](#-testes)
- [Linting e Formatação](#-linting-e-formatação)
- [Migrations](#-migrations)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Visão Geral

FastAPI Zero é um web scraper de preços que:
- **Extrai preços** de múltiplos sites em paralelo
- **Descobre URLs** automaticamente via sitemap e crawling
- **Categoriza produtos** por loja
- **Seleciona o preço mais baixo** entre diferentes fornecedores
- **Oferece interface web** intuitiva para buscar e comparar preços

---

## ✨ Recursos

- ✅ **Web Scraping Assíncrono** — Múltiplas requisições paralelas com `httpx`
- ✅ **Extração Inteligente** — JSON-LD, Next.js `__NEXT_DATA__` e HTML parsing
- ✅ **Discovery de URLs** — Sitemap parsing e link crawling automático
- ✅ **API RESTful** — Endpoints bem estruturados
- ✅ **Interface Web** — Dashboard com filtros e ordenação
- ✅ **Banco de Dados** — SQLAlchemy + Alembic migrations
- ✅ **Código Limpo** — Ruff linting (zero violations)
- ✅ **Testes** — Pytest com fixtures e mocking
- ✅ **Organização em Camadas** — core, db, services, schemas, api

---

## 📋 Pré-requisitos

- **Python 3.13+**
- **Poetry 1.6+**
- **SQLite3** (incluído no Python)

Verifique as versões instaladas:

```bash
python --version
poetry --version
```

---

## 📦 Instalação

### 1. Clonar o Repositório

```bash
git clone https://github.com/eusouanderson/fastAPI-zero.git
cd fastAPI-zero
```

### 2. Instalar Dependências

```bash
poetry install
```

Isso vai:
- Criar um ambiente virtual
- Instalar todas as dependências do `pyproject.toml`
- Gerar `poetry.lock`

### 3. Ativar o Ambiente Virtual (Opcional)

```bash
poetry shell
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# Banco de dados
DATABASE_URL=sqlite:///./database.db

# FastAPI
DEBUG=true
API_HOST=127.0.0.1
API_PORT=8000

# Scraper
MAX_CONCURRENCY=20
TIMEOUT=10.0
```

A aplicação carrega essas variáveis em `fastapi_zero/core/settings.py`

---

## 🚀 Iniciando o Servidor

### Modo Desenvolvimento (com hot-reload)

```bash
poetry run uvicorn fastapi_zero.app:app --reload --host 127.0.0.1 --port 8000
```

### Modo Produção

```bash
poetry run uvicorn fastapi_zero.app:app --host 0.0.0.0 --port 8000
```

Acesse:
- **API**: http://localhost:8000
- **Docs Interativa**: http://localhost:8000/docs
- **Interface Web**: http://localhost:8000/ui

---

## 📡 API Endpoints

### 1. **GET** `/`
Retorna informações da API.

**Response:**
```json
{
  "message": "FastAPI Zero - Web Scraper de Preços",
  "version": "1.0.0"
}
```

---

### 2. **POST** `/scrape/urls`
Faz scraping de uma lista de URLs.

**Request Body:**
```json
{
  "urls": [
    "https://www.kabum.com.br/produto/123",
    "https://www.pichau.com.br/produto/456"
  ],
  "max_concurrency": 20
}
```

**Response:**
```json
{
  "total": 2,
  "products": [
    {
      "url": "https://www.kabum.com.br/produto/123",
      "title": "GPU RTX 4070",
      "price": 2999.99,
      "currency": "BRL",
      "raw_price": "R$ 2.999,99"
    }
  ]
}
```

---

### 3. **POST** `/crawl/urls`
Descobre URLs automaticamente via sitemap e crawling.

**Request Body:**
```json
{
  "base_url": "https://www.kabum.com.br",
  "max_urls": 500,
  "use_sitemap": true,
  "follow_links": false,
  "include_patterns": ["/produto/"],
  "exclude_patterns": ["/admin/", "/api/"],
  "max_depth": 1
}
```

**Response:**
```json
{
  "total_urls": 245,
  "urls": [
    "https://www.kabum.com.br/produto/123",
    "https://www.kabum.com.br/produto/456"
  ]
}
```

---

### 4. **POST** `/crawl/search`
Crawl resultados de busca e extrai URLs de produtos.

**Request Body:**
```json
{
  "search_url": "https://www.kabum.com.br/busca/rx-7600",
  "max_pages": 5,
  "max_urls": 500
}
```

**Response:**
```json
{
  "total_urls": 48,
  "urls": [
    "https://www.kabum.com.br/produto/123",
    "https://www.kabum.com.br/produto/456"
  ]
}
```

---

### 5. **POST** `/users`
Cria um novo usuário.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "senha_segura"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com"
}
```

---

### 6. **GET** `/users/{user_id}`
Retorna informações de um usuário.

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com"
}
```

---

## 📁 Estrutura do Projeto

```
fastAPI-zero/
├── alembic.ini                           # Config do Alembic
├── pyproject.toml                        # Dependências e config do Poetry
├── poetry.lock                           # Lock file (auto-gerado)
├── README.md                             # Este arquivo
│
├── fastapi_zero/
│   ├── __init__.py
│   ├── app.py                           # Instância FastAPI e rotas principais
│   │
│   ├── core/                            # Camada de configurações
│   │   ├── __init__.py
│   │   └── settings.py                  # Variáveis de ambiente e config
│   │
│   ├── db/                              # Camada de banco de dados
│   │   ├── __init__.py
│   │   ├── models.py                    # Modelos SQLAlchemy (User, Product, PriceRecord)
│   │   └── session.py                   # Engine, SessionLocal, get_session()
│   │
│   ├── services/                        # Lógica de negócio
│   │   ├── __init__.py
│   │   └── scraper.py                   # Classe Scraper (web scraping)
│   │
│   ├── schemas/                         # Schemas Pydantic
│   │   └── __init__.py                  # Todos os DTOs (ScrapeUrlsRequest, etc)
│   │
│   ├── api/                             # Camada de API
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── scrape.py                # Endpoints de scraping
│   │       └── users.py                 # Endpoints de usuários
│   │
│   ├── templates/                       # Templates HTML
│   │   └── index.html                   # Interface web
│   │
│   ├── static/                          # Arquivos estáticos
│   │   ├── app.js                       # JavaScript do frontend
│   │   └── styles.css                   # CSS responsivo
│   │
│   ├── database.py                      # Shim backward-compat (import de db/)
│   ├── models.py                        # Shim backward-compat (import de db/)
│   ├── settings.py                      # Shim backward-compat (import de core/)
│   └── scraper.py                       # Shim backward-compat (import de services/)
│
├── migrations/
│   ├── env.py                           # Config do Alembic
│   ├── script.py.mako                   # Template para novas migrations
│   └── versions/
│       └── e7e412616ab7_create_users_table.py
│       └── 5634b0a78199_add_products_and_price_records.py
│
└── tests/
    ├── conftest.py                      # Fixtures pytest
    ├── test_app.py                      # Testes dos endpoints
    └── test_db.py                       # Testes do banco de dados
```

---

## 🛠️ Desenvolvimento

### Estrutura em Camadas

O projeto segue um padrão de **arquitetura em camadas**:

1. **Core** (`fastapi_zero/core/`)
   - Configurações e variáveis de ambiente
   - Isolado de dependências externas

2. **DB** (`fastapi_zero/db/`)
   - Modelos SQLAlchemy
   - Sessão do banco de dados
   - Funções de acesso a dados

3. **Services** (`fastapi_zero/services/`)
   - Lógica de negócio
   - Scraper, cálculos, processamento
   - Testável e reutilizável

4. **Schemas** (`fastapi_zero/schemas/`)
   - Pydantic models (DTOs)
   - Validação de entrada/saída
   - Documentação automática

5. **API** (`fastapi_zero/api/routes/`)
   - Endpoints FastAPI
   - Injeção de dependências
   - Respostas HTTP

### Fluxo de Requisição

```
HTTP Request
    ↓
[API Route] - valida com Pydantic
    ↓
[Service] - executa lógica de negócio
    ↓
[DB] - acessa dados com SQLAlchemy
    ↓
SQLite Database
    ↓
[Response Schema] - serializa resultado
    ↓
HTTP Response (JSON)
```

---

## 🧪 Testes

### Rodar Todos os Testes

```bash
poetry run pytest
```

### Rodar com Cobertura

```bash
poetry run pytest --cov=fastapi_zero --cov-report=html
```

Abre o relatório em `htmlcov/index.html`

### Rodar Teste Específico

```bash
poetry run pytest tests/test_app.py::test_read_root -v
```

### Modo Watch (re-roda ao salvar)

```bash
poetry run pytest-watch
```

---

## 🔍 Linting e Formatação

### Verificar Código

```bash
poetry run ruff check fastapi_zero/
```

### Corrigir Automaticamente

```bash
poetry run ruff check --fix fastapi_zero/
```

### Formatar Código

```bash
poetry run ruff format fastapi_zero/
```

### Verificação Completa (check + format)

```bash
poetry run ruff check --fix && poetry run ruff format
```

**Status**: ✅ 0 violations (todas as 14 violações foram corrigidas)

---

## 🗄️ Migrations

### Criar Nova Migration

```bash
poetry run alembic revision --autogenerate -m "descrição da mudança"
```

### Aplicar Migrations

```bash
poetry run alembic upgrade head
```

### Ver Histórico

```bash
poetry run alembic history
```

### Reverter para Versão Anterior

```bash
poetry run alembic downgrade -1
```

---

## 🌐 Interface Web

Acesse http://localhost:8000/ui para a interface web com:

- ✅ Campos para inserir URLs
- ✅ Busca por termo
- ✅ Controle de temperatura (agressividade do scraping)
- ✅ Filtros por preço
- ✅ Ordenação por preço/loja
- ✅ Tabela com resultados em tempo real

---

## 📊 Modelos de Dados

### User
```python
class User(Base):
    id: int (PK)
    username: str (unique)
    email: str (unique)
    password: str (hashed)
    created_at: datetime
```

### Product
```python
class Product(Base):
    id: int (PK)
    url: str (unique)
    title: str
    store: str
    created_at: datetime
```

### PriceRecord
```python
class PriceRecord(Base):
    id: int (PK)
    product_id: int (FK → Product)
    price: float
    currency: str
    raw_price: str
    recorded_at: datetime
```

---

## 🔧 Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'fastapi_zero'`

**Solução:**
```bash
poetry install
poetry shell
```

### Erro: `DATABASE_URL not set`

**Solução:**
```bash
export DATABASE_URL=sqlite:///./database.db
```

### Erro: `alembic.exc.CommandError: Can't locate revision identified by`

**Solução:**
```bash
poetry run alembic upgrade head
```

### Erro: `Connection refused` ao conectar ao banco

**Solução:**
```bash
rm database.db
poetry run alembic upgrade head
```

### Scraper muito lento

**Solução:**
```python
# Aumentar concorrência em scrape.py
scraper = Scraper(max_concurrency=50)  # default é 20
```

---

## 📚 Documentação Adicional

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Pydantic Validation](https://docs.pydantic.dev/)
- [Poetry Docs](https://python-poetry.org/)

---

## 📄 Licença

MIT License

---

## 👤 Autor

Desenvolvido por [Anderson](https://github.com/eusouanderson)

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📞 Suporte

Para reportar problemas ou sugerir melhorias, abra uma [issue](https://github.com/eusouanderson/fastAPI-zero/issues)

---

**Last Updated**: January 29, 2026 | **Status**: ✅ Production Ready
