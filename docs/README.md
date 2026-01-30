# 📚 Documentação FastAPI Zero

Bem-vindo à documentação completa do FastAPI Zero!

---

## 📖 Documentos Disponíveis

### 🚀 [Quick Start](QUICKSTART.md)
**Para: Iniciantes que querem começar rápido**
- Instalação em 5 minutos
- Primeiros testes com cURL/Python
- Troubleshooting básico

### 📋 [README.md](../README.md)
**Para: Visão geral do projeto**
- Visão geral e recursos
- Instalação completa
- Configuração e variáveis de ambiente
- Estrutura do projeto
- Guia de testes

### 🔗 [API Reference](API.md)
**Para: Documentação técnica de endpoints**
- Todos os endpoints com exemplos
- Request/Response schemas
- Status codes e erros
- Exemplos em cURL, Python, JavaScript

### 🛠️ [Guia de Desenvolvimento](DEVELOPMENT.md)
**Para: Contribuintes e arquitetos**
- Arquitetura em camadas
- Padrões de código
- Estrutura do projeto
- Como escrever testes
- Linting e formatação

---

## 🗺️ Mapa Rápido

```
Você é novo?
    ↓
Leia: QUICKSTART.md
    ↓
Abra: http://localhost:8000/ui
    ↓

Quer entender a API?
    ↓
Leia: API.md
    ↓
Teste em: http://localhost:8000/docs
    ↓

Quer contribuir?
    ↓
Leia: DEVELOPMENT.md
    ↓
Execute: poetry run pytest
    ↓

Quer informações gerais?
    ↓
Leia: README.md
    ↓
```

---

## 🎯 Guias por Tarefa

### Quero fazer scraping de URLs
→ Veja [API.md - POST /scrape/urls](API.md#-scraping)

### Quero descobrir URLs automaticamente
→ Veja [API.md - POST /crawl/urls](API.md#-url-discovery)

### Quero adicionar um novo endpoint
→ Veja [DEVELOPMENT.md - Arquitetura](#-arquitetura)

### Quero executar testes
→ Veja [README.md - Testes](../README.md#-testes)

### Quero melhorar o código
→ Veja [DEVELOPMENT.md - Linting](DEVELOPMENT.md#-linting-e-formatação)

### Quero entender a estrutura
→ Veja [README.md - Estrutura](../README.md#-estrutura-do-projeto)

### Quero fazer uma migration
→ Veja [README.md - Migrations](../README.md#️-migrations)

### Tenho um problema
→ Veja [README.md - Troubleshooting](../README.md#-troubleshooting)

---

## 📊 Estrutura da Documentação

```
docs/
├── README.md           ← Este arquivo (índice)
├── QUICKSTART.md       ← Comece aqui!
├── API.md              ← Referência de endpoints
└── DEVELOPMENT.md      ← Guia técnico

../README.md            ← Overview do projeto (recomendado ler)
```

---

## 🔍 Usando a Documentação

### Search no VS Code
```
Ctrl+P (ou Cmd+P no Mac)
> docs/
```

### Navegação nos Docs
- Clique nos links em azul para navegar
- Use `Ctrl+Click` (Cmd+Click) para abrir em nova aba
- Use `Ctrl+Home` para voltar ao topo

### Links Internos

#### No README.md
- [Instalação](../README.md#-instalação)
- [API Endpoints](../README.md#-api-endpoints)
- [Estrutura](../README.md#-estrutura-do-projeto)

#### No API.md
- [POST /scrape/urls](API.md#-scraping)
- [POST /crawl/urls](API.md#-url-discovery)
- [Error Handling](API.md#error-handling)

#### No DEVELOPMENT.md
- [Padrões de Código](DEVELOPMENT.md#-padrões-de-código)
- [Testes](DEVELOPMENT.md#-testando)
- [Linting](DEVELOPMENT.md#-linting)

---

## 💡 Dicas

### Leitura Recomendada (Ordem)

**Para Usuários:**
1. QUICKSTART.md (5 min)
2. README.md (10 min)
3. API.md (15 min)

**Para Desenvolvedores:**
1. QUICKSTART.md (5 min)
2. README.md (10 min)
3. DEVELOPMENT.md (15 min)
4. API.md (10 min)

### Keep Docs Updated

Quando fazer mudanças importantes:
```bash
# Atualize a documentação
vim docs/API.md
vim docs/DEVELOPMENT.md

# Faça commit
git add docs/
git commit -m "docs: atualizar documentação"
git push
```

---

## 🔗 Links Úteis

### Documentação Externa
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### Ferramentas
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pytest Docs](https://docs.pytest.org/)
- [Poetry Docs](https://python-poetry.org/docs/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)

### Repositório
- [GitHub Repo](https://github.com/eusouanderson/fastAPI-zero)
- [Issues](https://github.com/eusouanderson/fastAPI-zero/issues)
- [Discussions](https://github.com/eusouanderson/fastAPI-zero/discussions)

---

## 📞 Suporte

### Problemas?

1. **Verifique o Troubleshooting**
   - [README.md - Troubleshooting](../README.md#-troubleshooting)

2. **Procure na documentação**
   - Use `Ctrl+F` para buscar
   - Veja DEVELOPMENT.md para tópicos técnicos

3. **Abra uma Issue**
   - [GitHub Issues](https://github.com/eusouanderson/fastAPI-zero/issues)
   - Descreva o problema com detalhes
   - Inclua erro/log se houver

4. **Leia o código**
   - `fastapi_zero/api/routes/` - Endpoints
   - `fastapi_zero/services/` - Lógica
   - `fastapi_zero/db/models.py` - Modelos

---

## ✨ Melhorias Futuras

- [ ] Adicionar screenshots/demos
- [ ] Criar guia de deployment
- [ ] Adicionar troubleshooting avançado
- [ ] Criar guia de contribuição
- [ ] Adicionar exemplos de curl em arquivo `.rest`
- [ ] Criar documentação de segurança

---

## 📄 Versão

- **Última atualização**: January 29, 2026
- **Versão do Projeto**: 1.0.0
- **Status**: ✅ Completa e Produção Pronta

---

**Comece agora:** [QUICKSTART.md](QUICKSTART.md) → 5 minutos para rodar! 🚀
