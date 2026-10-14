# Análise de Projeto — Heurísticas

Guia para a Fase 1. O objetivo é descrever o projeto com fatos verificáveis: stack, domínio, arquitetura e superfície da API.

## 1. Detecção de linguagem

| Sinal | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, arquivos `*.py` | Python |
| `package.json`, arquivos `*.js` / `*.mjs` / `*.cjs` | JavaScript (Node.js) |
| `tsconfig.json`, arquivos `*.ts` | TypeScript |
| `pom.xml`, `build.gradle`, arquivos `*.java` | Java |
| `go.mod` | Go |
| `composer.json`, arquivos `*.php` | PHP |
| `Gemfile`, arquivos `*.rb` | Ruby |
| `*.csproj` | C# |

Se houver mais de uma, a linguagem principal é a que tem o entry point e a maior parte das linhas.

Versão: procure em `pyproject.toml` (`requires-python`), `.python-version`, `package.json` (`engines`), `.nvmrc`, Dockerfile. Se não houver, informe apenas a linguagem.

## 2. Detecção de framework

| Sinal no código ou manifesto | Framework |
|---|---|
| `flask` no manifesto, `Flask(__name__)`, `Blueprint`, `@app.route` | Flask |
| `fastapi`, `FastAPI()`, `APIRouter` | FastAPI |
| `django`, `settings.py`, `urls.py`, `manage.py` | Django |
| `express` no `package.json`, `express()`, `app.get/post`, `express.Router()` | Express |
| `@nestjs/core`, decorators `@Controller` | NestJS |
| `fastify`, `koa`, `hapi` | Fastify / Koa / Hapi |
| `spring-boot`, `@RestController` | Spring Boot |
| `laravel/framework`, `routes/web.php` | Laravel |

A versão vem do manifesto (`flask==3.1.1`, `"express": "^4.18.2"`). Informe exatamente como está declarada.

## 3. Banco de dados e acesso a dados

| Sinal | Banco / forma de acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect`, `require('sqlite3')`, `:memory:`, `*.db` | SQLite com driver cru |
| `flask_sqlalchemy`, `SQLAlchemy()`, `db.Model`, `sqlite:///` / `postgresql://` | ORM SQLAlchemy |
| `psycopg2`, `pg`, `mysql`, `mysql2`, `pymongo`, `mongoose` | Postgres / MySQL / MongoDB |
| `prisma`, `sequelize`, `typeorm`, `knex` | ORM / query builder Node |

Tabelas/entidades: extraia de `CREATE TABLE`, classes de model (`__tablename__`, `db.Model`), schemas do ORM ou migrations.

## 4. Domínio da aplicação

Deduza pelo nome das tabelas, rotas e mensagens. Exemplos:

- `produtos`, `pedidos`, `carrinho`, `checkout` → e-commerce
- `courses`, `enrollments`, `students` → LMS / plataforma de cursos
- `tasks`, `projects`, `categories`, `due_date` → gestão de tarefas

Descreva em uma frase e liste as entidades principais.

## 5. Mapeamento de endpoints

| Framework | Onde procurar |
|---|---|
| Flask | `@app.route`, `@bp.route`, `app.add_url_rule`, `register_blueprint` |
| FastAPI | `@app.get/post/...`, `@router.get/...`, `include_router` |
| Express | `app.get/post/put/delete`, `router.METHOD`, `app.use('/prefixo', router)` |
| Django | `urls.py` (`path`, `re_path`) |

Registre método + rota de cada endpoint. Inclua rotas administrativas e de health.

## 6. Arquitetura atual

Classifique a organização encontrada:

| Classificação | Sinais |
|---|---|
| **Monolítica / sem camadas** | Poucos arquivos concentrando rotas, SQL, regra de negócio e configuração; classe "Manager" ou "App" que faz tudo; SQL dentro de handlers |
| **Camadas parciais** | Já existem pastas como `models/`, `routes/`, `services/`, `utils/`, mas as responsabilidades vazam (regra de negócio e serialização nas rotas, queries espalhadas, config hardcoded) |
| **MVC / camadas definidas** | Models só com dados e regras de domínio, controllers orquestrando, rotas finas, config isolada, error handling centralizado |

Descreva em uma frase o que está misturado com o quê (ex.: "Monolítica — rotas, SQL e regras de negócio em 4 arquivos, sem camada de config").

## 7. Contagem

- **Source files:** arquivos de código da aplicação (exclua `.claude/`, dependências, ambientes virtuais, lockfiles, bancos e arquivos gerados).
- **Lines of code:** soma aproximada das linhas desses arquivos (`wc -l`).

## 8. Como a aplicação roda

Anote para usar na Fase 3:

- Comando de start (README, `scripts.start`, `if __name__ == "__main__"`).
- Porta padrão e se ela é configurável.
- Seeds ou passos prévios (ex.: `python seed.py`, banco em memória com seed no boot).
- Arquivos de exemplo de requisições (`*.http`, coleções Postman) que servem de payload para testes.
