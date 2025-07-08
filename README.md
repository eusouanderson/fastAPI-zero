# 🚀 FastAPI Zero

Um projeto base minimalista usando **FastAPI**, **SQLAlchemy**, **Alembic** e **Poetry**, com foco em organização, cobertura de testes e boas práticas.

> ⚡ Desenvolvido com Python `3.13.5` e gerenciado com `Poetry`.

---

## 📁 Estrutura do Projeto

```bash

fastAPI_zero/
├── alembic.ini # Configuração do Alembic para migrations
├── database.db # Banco de dados SQLite local (ignorar em produção)
├── fastapi_zero/ # Código principal da aplicação
│ ├── app.py # Instância da aplicação FastAPI e rotas
│ ├── database.py # Sessão e engine do SQLAlchemy
│ ├── models.py # Modelos ORM
│ ├── schemas.py # Schemas Pydantic
│ └── settings.py # Configurações da aplicação
├── htmlcov/ # Relatórios de cobertura de testes (gerado pelo coverage)
├── migrations/ # Diretório de migrations do Alembic
│ └── versions/ # Versões das migrations
├── poetry.lock # Lockfile do Poetry
├── pyproject.toml # Configuração do projeto e dependências
├── README.md # Este arquivo
└── tests/ # Testes automatizados com Pytest
├── conftest.py # Fixtures globais
├── test_app.py # Testes dos endpoints
└── test_db.py # Testes da integração com o banco

```


---

## 📦 Tecnologias Utilizadas

- **[FastAPI](https://fastapi.tiangolo.com/)** — Web Framework assíncrono e moderno.
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — ORM para o banco de dados.
- **[Alembic](https://alembic.sqlalchemy.org/)** — Controle de versionamento do banco.
- **[Pydantic](https://docs.pydantic.dev/)** — Validação de dados com Python type hints.
- **[Poetry](https://python-poetry.org/)** — Gerenciador de pacotes e ambientes virtuais.
- **[Pytest](https://docs.pytest.org/)** — Framework de testes.
- **[Coverage.py](https://coverage.readthedocs.io/)** — Geração de relatórios de cobertura.

---

## 🚀 Como Rodar o Projeto

### 1. Clone o repositório

```bash

git clone https://github.com/eusouanderson/fastAPI_zero.git

```
```bash


cd fastAPI_zero
```
```bash

poetry install
```
```bash

poetry shell
```
```bash

task run	#Inicia o servidor com fastapi dev fastapi_zero/app.py

```
```bash
task lint #Verifica problemas com o ruff

```
```bash
task pre_format	#Corrige automaticamente problemas simples com ruff --fix
```
```bash

task format	#Formata o código com ruff format

```
```bash
task test #Executa os testes com Pytest + Coverage

```
```bash
task post_test	#Gera o relatório de cobertura em HTML (htmlcov/index.html)
