# 🔗 API Reference

Referência completa dos endpoints da API.

---

## Base URL

```
http://localhost:8000
```

## Authentication

Atualmente, a API **não requer autenticação**. Futuras versões implementarão JWT.

---

## Response Format

Todos os responses são em JSON com o seguinte padrão:

### Sucesso (200-201)
```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2026-01-29T10:30:00Z"
}
```

### Erro (400-500)
```json
{
  "status": "error",
  "error": "Descrição do erro",
  "details": { ... },
  "timestamp": "2026-01-29T10:30:00Z"
}
```

---

## Endpoints

### 1. Health Check

#### GET `/`

Verifica se a API está online.

**Response:**
```json
{
  "message": "FastAPI Zero - Web Scraper de Preços",
  "version": "1.0.0",
  "status": "operational"
}
```

**Status Code:** `200 OK`

---

### 2. Scraping

#### POST `/scrape/urls`

Faz web scraping de uma lista de URLs.

**Request:**
```json
{
  "urls": [
    "https://www.kabum.com.br/produto/123",
    "https://www.pichau.com.br/produto/456"
  ],
  "max_concurrency": 20
}
```

**Parameters:**
| Campo | Tipo | Obrigatório | Default | Descrição |
|-------|------|-------------|---------|-----------|
| urls | array[string] | ✅ | - | URLs para fazer scraping |
| max_concurrency | integer | ❌ | 20 | Número de requisições simultâneas (1-50) |

**Response:**
```json
{
  "total": 2,
  "products": [
    {
      "url": "https://www.kabum.com.br/produto/123",
      "title": "GPU NVIDIA RTX 4070",
      "price": 2999.99,
      "currency": "BRL",
      "raw_price": "R$ 2.999,99"
    },
    {
      "url": "https://www.pichau.com.br/produto/456",
      "title": "GPU NVIDIA RTX 4070 OC",
      "price": 3150.00,
      "currency": "BRL",
      "raw_price": "R$ 3.150,00"
    }
  ]
}
```

**Status Codes:**
- `200` - Sucesso
- `400` - URLs inválidas ou formato incorreto
- `422` - Validação falhou
- `500` - Erro ao fazer scraping

**Example com cURL:**
```bash
curl -X POST "http://localhost:8000/scrape/urls" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/product"],
    "max_concurrency": 20
  }'
```

**Example com Python:**
```python
import httpx
import asyncio

async def scrape():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/scrape/urls",
            json={
                "urls": ["https://example.com/product"],
                "max_concurrency": 20
            }
        )
        return response.json()

asyncio.run(scrape())
```

---

### 3. URL Discovery

#### POST `/crawl/urls`

Descobre URLs automaticamente via sitemap ou crawling.

**Request:**
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

**Parameters:**
| Campo | Tipo | Obrigatório | Default | Descrição |
|-------|------|-------------|---------|-----------|
| base_url | string | ✅ | - | URL raiz do site |
| max_urls | integer | ❌ | 1000 | Limite de URLs (1-10000) |
| use_sitemap | boolean | ❌ | true | Buscar via sitemap.xml |
| follow_links | boolean | ❌ | false | Seguir links da página |
| include_patterns | array[string] | ❌ | [] | Regex para incluir URLs |
| exclude_patterns | array[string] | ❌ | [] | Regex para excluir URLs |
| max_depth | integer | ❌ | 1 | Profundidade de crawling (1-5) |

**Response:**
```json
{
  "total_urls": 245,
  "urls": [
    "https://www.kabum.com.br/produto/123",
    "https://www.kabum.com.br/produto/456",
    "https://www.kabum.com.br/produto/789"
  ]
}
```

**Status Codes:**
- `200` - Sucesso
- `400` - URL ou patterns inválidos
- `408` - Timeout ao fazer request
- `500` - Erro ao fazer discovery

---

#### POST `/crawl/search`

Crawl uma página de busca e extrai URLs de produtos.

**Request:**
```json
{
  "search_url": "https://www.kabum.com.br/busca/rx-7600",
  "max_pages": 5,
  "max_urls": 500
}
```

**Parameters:**
| Campo | Tipo | Obrigatório | Default | Descrição |
|-------|------|-------------|---------|-----------|
| search_url | string | ✅ | - | URL de busca |
| max_pages | integer | ❌ | 5 | Número máximo de páginas |
| max_urls | integer | ❌ | 500 | Limite total de URLs |

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

### 4. Users

#### POST `/users`

Cria um novo usuário.

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "senha_forte_123"
}
```

**Parameters:**
| Campo | Tipo | Regra | Descrição |
|-------|------|-------|-----------|
| username | string | 3-50 chars, alphanumeric | Nome único do usuário |
| email | string | válido RFC 5322 | Email único |
| password | string | 8+ chars | Senha em plaintext (será hasheada) |

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2026-01-29T10:30:00Z"
}
```

**Status Codes:**
- `201` - Usuário criado
- `400` - Username ou email já existe
- `422` - Validação falhou (email inválido, etc)

---

#### GET `/users/{user_id}`

Retorna informações de um usuário.

**Parameters:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| user_id | integer | ID do usuário |

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2026-01-29T10:30:00Z"
}
```

**Status Codes:**
- `200` - Sucesso
- `404` - Usuário não encontrado

**Example com cURL:**
```bash
curl "http://localhost:8000/users/1"
```

---

#### PUT `/users/{user_id}`

Atualiza informações de um usuário.

**Request:**
```json
{
  "email": "newemail@example.com",
  "password": "nova_senha_123"
}
```

**Parameters:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| email | string | ❌ | Novo email |
| password | string | ❌ | Nova senha |

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "newemail@example.com",
  "updated_at": "2026-01-29T10:35:00Z"
}
```

---

#### DELETE `/users/{user_id}`

Deleta um usuário.

**Response:**
```json
{
  "message": "Usuário deletado com sucesso",
  "id": 1
}
```

**Status Codes:**
- `200` - Deletado
- `404` - Usuário não encontrado

---

## Error Handling

### Exemplos de Erro

#### 400 Bad Request
```json
{
  "detail": [
    {
      "loc": ["body", "urls"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 404 Not Found
```json
{
  "detail": "Usuário com ID 999 não encontrado"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email.invalid"
    }
  ]
}
```

#### 429 Too Many Requests
```json
{
  "detail": "Taxa de requisições excedida. Tente novamente em 60 segundos."
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Erro interno do servidor. Tente novamente mais tarde."
}
```

---

## Rate Limiting

Atualmente, não há rate limiting implementado. Futuras versões utilizarão:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 98
X-RateLimit-Reset: 1643433600
```

---

## Paginação (Futuro)

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Filtros (Futuro)

```bash
GET /users?username=john&email=john@example.com&sort=-created_at&limit=10&offset=0
```

---

## CORS

A API não está configurada com CORS. Para habilitar em produção:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Timeouts

- **Scraping**: 10 segundos por URL (configurável)
- **URL Discovery**: 30 segundos
- **Search Crawling**: 60 segundos

---

**Last Updated**: January 29, 2026
