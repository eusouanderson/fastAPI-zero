# 🚀 Quick Start Guide

Comece a usar FastAPI Zero em 5 minutos!

---

## 1️⃣ Instalação Rápida

```bash
# Clone
git clone https://github.com/eusouanderson/fastAPI-zero.git
cd fastAPI-zero

# Instale dependências
poetry install

# Ative o ambiente
poetry shell
```

---

## 2️⃣ Inicie o Servidor

```bash
poetry run uvicorn fastapi_zero.app:app --reload --port 8000
```

Aguarde a mensagem:
```
Uvicorn running on http://127.0.0.1:8000
```

---

## 3️⃣ Abra no Navegador

### Interface Web
```
http://localhost:8000/ui
```

### Documentação Interativa
```
http://localhost:8000/docs
```

---

## 4️⃣ Primeiros Testes

### Via Interface Web

1. Acesse http://localhost:8000/ui
2. Digite uma URL (ex: `https://www.kabum.com.br/produto/123`)
3. Clique em "Scrape"
4. Veja o resultado em tempo real!

### Via cURL

#### Scraper de URLs

```bash
curl -X POST "http://localhost:8000/scrape/urls" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://www.kabum.com.br/produto/123"],
    "max_concurrency": 20
  }'
```

#### Descobrir URLs

```bash
curl -X POST "http://localhost:8000/crawl/urls" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://www.kabum.com.br",
    "max_urls": 100,
    "use_sitemap": true,
    "include_patterns": ["/produto/"]
  }'
```

#### Busca em Página

```bash
curl -X POST "http://localhost:8000/crawl/search" \
  -H "Content-Type: application/json" \
  -d '{
    "search_url": "https://www.kabum.com.br/busca/gpu",
    "max_pages": 3,
    "max_urls": 100
  }'
```

### Via Python

```python
import httpx
import asyncio

async def scrape():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/scrape/urls",
            json={
                "urls": ["https://www.kabum.com.br/produto/123"],
                "max_concurrency": 20
            }
        )
        data = response.json()
        print(f"Total: {data['total']}")
        for product in data['products']:
            print(f"  - {product['title']}: R$ {product['price']}")

asyncio.run(scrape())
```

### Via JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/scrape/urls', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    urls: ['https://www.kabum.com.br/produto/123'],
    max_concurrency: 20
  })
});

const data = await response.json();
console.log(`Total: ${data.total}`);
data.products.forEach(p => {
  console.log(`  - ${p.title}: R$ ${p.price}`);
});
```

---

## 5️⃣ Próximos Passos

### ✅ Rodar Testes

```bash
poetry run pytest
```

### ✅ Verificar Código

```bash
poetry run ruff check fastapi_zero/
```

### ✅ Consultar Documentação

- [README.md](../README.md) - Visão geral
- [docs/API.md](API.md) - Referência de endpoints
- [docs/DEVELOPMENT.md](DEVELOPMENT.md) - Guia de desenvolvimento

### ✅ Explorar o Código

```
fastapi_zero/
├── app.py              ← Instância FastAPI
├── core/settings.py    ← Configurações
├── db/models.py        ← Modelos do banco
├── services/scraper.py ← Lógica de scraping
├── schemas/            ← Validação Pydantic
└── api/routes/         ← Endpoints
```

---

## 🔧 Troubleshooting Rápido

### Port já está em uso?

```bash
poetry run uvicorn fastapi_zero.app:app --reload --port 8001
```

### Erro de banco de dados?

```bash
rm database.db
poetry run alembic upgrade head
```

### Dependências desatualizadas?

```bash
poetry update
```

### Linting problemas?

```bash
poetry run ruff check --fix fastapi_zero/
poetry run ruff format fastapi_zero/
```

---

## 📚 Comandos Úteis

```bash
# Desenvolvimento
poetry run uvicorn fastapi_zero.app:app --reload

# Testes
poetry run pytest -v

# Cobertura
poetry run pytest --cov=fastapi_zero --cov-report=html

# Linting
poetry run ruff check --fix && poetry run ruff format

# Banco de dados
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "descrição"

# Shell interativo
poetry run python
```

---

## 🎯 Próxima Tarefa Recomendada

1. **Entender a arquitetura** - Leia [docs/DEVELOPMENT.md](DEVELOPMENT.md)
2. **Explorar endpoints** - Use http://localhost:8000/docs
3. **Modificar código** - Tente adicionar um novo modelo ou endpoint
4. **Rodar testes** - `poetry run pytest`

---

**Status**: ✅ Pronto para começar!

**Need help?** Abra uma [issue no GitHub](https://github.com/eusouanderson/fastAPI-zero/issues)
