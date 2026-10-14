# Refatoração Arquitetural Automatizada com a Skill `refactor-arch`

Neste desafio criei uma skill para o Claude Code, a `/refactor-arch`. Ela analisa um projeto backend, audita anti-patterns de arquitetura, segurança e qualidade, gera um relatório com severidade, arquivo e linha e, depois da minha confirmação, refatora o projeto para o padrão MVC, validando que a API continua funcionando.

Executei a mesma skill, sem nenhuma alteração por projeto, nas três aplicações do repositório:

| Projeto | Stack | Situação inicial |
|---|---|---|
| `code-smells-project/` | Python + Flask | Monolito com 4 arquivos |
| `ecommerce-api-legacy/` | Node.js + Express | God Class `AppManager` com callbacks aninhados |
| `task-manager-api/` | Python + Flask + SQLAlchemy | Camadas parciais (`models/`, `routes/`, `services/`, `utils/`) |

Entregáveis:

- Skill: `<projeto>/.claude/skills/refactor-arch/` (cópia idêntica nos 3 projetos)
- Relatórios da Fase 2: [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md), [`reports/audit-project-3.md`](reports/audit-project-3.md)
- Logs completos das execuções: [`reports/execution-logs/`](reports/execution-logs/)
- Código refatorado: commits `refactor(...)` de cada projeto

---

## Análise Manual

Antes de escrever a skill li o código dos três projetos inteiros e anotei os problemas que mais pesam na arquitetura e na segurança. Foi essa lista que virou a base do catálogo de anti-patterns.

### Projeto 1 — code-smells-project (Python/Flask, API de e-commerce)

4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`), ~780 linhas, sem camadas de verdade: `models.py` faz SQL, validação e formatação de produtos, usuários e pedidos ao mesmo tempo.

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection | `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140-166, 174-192, 279-281, 289-297` | Quase toda query é montada concatenando valores do request. No login, `' OR '1'='1` entra sem senha. |
| 2 | CRITICAL | Endpoint que executa SQL arbitrário sem autenticação | `app.py:59-78` | `POST /admin/query` executa qualquer SQL vindo do body. `POST /admin/reset-db` (`app.py:47-57`) apaga o banco sem autenticação. |
| 3 | CRITICAL | Credenciais hardcoded e expostas | `app.py:7`, `controllers.py:285-289` | `SECRET_KEY` está no código e ainda é devolvida pelo `/health`, junto com o caminho do banco e a flag de debug. |
| 4 | CRITICAL | Senhas em texto puro e devolvidas pela API | `database.py:75-83`, `models.py:83, 99, 109-111` | Senha salva como recebida, comparada direto no SQL e retornada em `GET /usuarios`. |
| 5 | CRITICAL | God File | `models.py:1-314` | Um arquivo com acesso a dados e regras de 4 domínios; impossível testar ou mexer em um sem afetar os outros. |
| 6 | HIGH | Estado global mutável na conexão | `database.py:4-11` | `global db_connection` com `check_same_thread=False` compartilha uma conexão entre todas as threads. |
| 7 | HIGH | Regra de negócio e efeitos colaterais no controller | `controllers.py:208-210, 247-250`, `models.py:256-262` | Notificações simuladas com `print` e faixas de desconto do relatório presas no fluxo HTTP. |
| 8 | HIGH | Pedido sem transação | `models.py:133-169` | Pedido, itens e baixa de estoque em várias escritas sem rollback; uma falha no meio deixa o banco inconsistente. |
| 9 | HIGH | Debug ligado e bind aberto fixos | `app.py:8, 88` | `debug=True` com `host="0.0.0.0"` expõe o debugger do Werkzeug (execução remota de código). |
| 10 | MEDIUM | Queries N+1 | `models.py:171-233` | Para cada pedido, uma query de itens; para cada item, uma query de produto (`cursor2`, `cursor3`). |
| 11 | MEDIUM | Validação duplicada e tratamento de erro genérico | `controllers.py:24-96`, todos os `except Exception as e: return str(e)` | Mesmo bloco de validação em criar/atualizar e mensagens internas do banco devolvidas ao cliente. |
| 12 | MEDIUM | Serialização duplicada | `models.py:12-21, 31-40, 304-313` | O mesmo dicionário de produto copiado em várias funções. |
| 13 | LOW | Magic numbers | `models.py:257-262`, `controllers.py:52, 242` | Faixas de desconto (`10000`, `0.1`...), categorias e status como literais soltos. |
| 14 | LOW | `print` como log | `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 219` | Sem nível de log nem destino configurável. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

3 arquivos em `src/`, ~180 linhas. A classe `AppManager` cria o banco, faz o seed, define todas as rotas e processa pagamento.

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais hardcoded | `src/utils.js:1-7` | Senha do banco, chave `pk_live_` do gateway e usuário SMTP no código-fonte. |
| 2 | CRITICAL | God Class | `src/AppManager.js:4-139` | Banco, schema, seed, rotas, pagamento e relatório na mesma classe. |
| 3 | CRITICAL | Dados de cartão e chave em log | `src/AppManager.js:45` | `console.log` com o número completo do cartão e a chave do gateway (viola PCI-DSS). |
| 4 | CRITICAL | "Criptografia" de senha caseira | `src/utils.js:17-23`, `src/AppManager.js:68` | `badCrypto` só repete base64 da senha; ainda usa `"123456"` como senha default. |
| 5 | CRITICAL | Rotas administrativas sem autenticação | `src/AppManager.js:80, 131` | Relatório financeiro e exclusão de usuários abertos para qualquer um. |
| 6 | HIGH | Estado global mutável | `src/utils.js:9-10, 12-15` | `globalCache` e `totalRevenue` exportados e mutados por qualquer módulo. |
| 7 | HIGH | Checkout sem transação | `src/AppManager.js:50-62` | Matrícula, pagamento e log em escritas separadas; se o pagamento falhar, a matrícula fica. |
| 8 | MEDIUM | Callback hell | `src/AppManager.js:37-77, 83-128` | Até 6 níveis de callbacks e contadores manuais (`coursesPending--`) para saber quando responder. |
| 9 | MEDIUM | N+1 no relatório financeiro | `src/AppManager.js:89-125` | Uma query de matrículas por curso e duas (usuário + pagamento) por matrícula. |
| 10 | MEDIUM | Exclusão deixa registros órfãos | `src/AppManager.js:131-136` | Apaga o usuário e deixa matrículas e pagamentos; a própria resposta admite isso. |
| 11 | MEDIUM | Erros ignorados | `src/AppManager.js:57, 92, 104, 106, 133` | Callbacks que recebem `err` e não tratam; `enrollments.length` quebra se a query falhar. |
| 12 | LOW | Nomes ruins | `src/AppManager.js:29-33`, `src/utils.js:12, 17` | `u`, `e`, `p`, `cid`, `cc`, `badCrypto`, `AppManager`. |
| 13 | LOW | Magic strings | `src/AppManager.js:46` | Regra de aprovação `cc.startsWith("4")` e status `"PAID"`/`"DENIED"` soltos. |

### Projeto 3 — task-manager-api (Python/Flask, Task Manager)

Já tem `models/`, `routes/`, `services/` e `utils/`, mas as rotas fazem tudo (validação, regra, serialização) e há vários problemas de segurança.

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais hardcoded | `app.py:13`, `services/notification_service.py:7-10` | `SECRET_KEY` e usuário/senha do SMTP no código. |
| 2 | CRITICAL | Hash de senha com MD5 | `models/user.py:27-32` | MD5 sem salt é quebrado em segundos com rainbow tables. |
| 3 | CRITICAL | Hash da senha devolvido pela API | `models/user.py:21`, `routes/user_routes.py:85, 129, 209` | `to_dict()` inclui `password`; create, update e login devolvem o hash. |
| 4 | HIGH | Token de autenticação falso | `routes/user_routes.py:210` | `'fake-jwt-token-' + id` pode ser forjado por qualquer um. |
| 5 | HIGH | Regra de negócio e serialização nas rotas | `routes/task_routes.py:11-63, 85-154`, `routes/report_routes.py:12-101` | Rotas com 50 a 90 linhas fazendo validação, cálculo e montagem de JSON. |
| 6 | MEDIUM | Queries N+1 | `routes/task_routes.py:41-57`, `routes/report_routes.py:53-68, 159-164`, `routes/user_routes.py:22` | Busca de usuário/categoria por task e de tasks por usuário dentro de loops. |
| 7 | MEDIUM | APIs deprecated | `Task.query.get` (SQLAlchemy 2.x) em todas as rotas; `datetime.utcnow` (Python 3.12+) nos models e rotas | Geram `LegacyAPIWarning`/`DeprecationWarning` e vão sumir nas próximas versões. |
| 8 | MEDIUM | Lógica de "atrasada" duplicada | `routes/task_routes.py:30-39, 71-80, 283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:34-43, 132-135` | A mesma regra reescrita 6 vezes, mesmo existindo `Task.is_overdue()`. |
| 9 | MEDIUM | `except:` genérico | `routes/task_routes.py:62, 137, 204, 236`, `routes/user_routes.py:130, 149`, `routes/report_routes.py:186, 207, 221` | Engole qualquer erro, inclusive bugs de programação. |
| 10 | MEDIUM | Validação duplicada e inconsistente | `routes/task_routes.py:92-114, 166-184`, `utils/helpers.py:57-108` | Create e update validam de formas diferentes; `process_task_data` existe mas não é usado. |
| 11 | LOW | Imports não usados | `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `utils/helpers.py:3-7` | `os, sys, json, time, hashlib, math` sem uso. |
| 12 | LOW | Magic numbers / constantes não usadas | `routes/task_routes.py:110-114`, `utils/helpers.py:110-116` | As constantes existem em `helpers.py`, mas as rotas usam os literais. |
| 13 | LOW | Condicionais verbosas | `models/task.py:38-60`, `models/user.py:34-38` | `if ...: return True else: return False` em vários métodos. |

---

## Construção da Skill

A skill fica em `.claude/skills/refactor-arch/`, com uma cópia idêntica dentro de cada projeto:

```
.claude/skills/refactor-arch/
├── SKILL.md
└── references/
    ├── project-analysis.md        # Fase 1: heurísticas de stack, domínio e arquitetura
    ├── anti-patterns-catalog.md   # Fase 2: 24 anti-patterns com sinais de detecção e severidade
    ├── audit-report-template.md   # Fase 2: formato obrigatório do relatório
    ├── mvc-guidelines.md          # Fase 3: camadas, responsabilidades e estrutura alvo
    └── refactoring-playbook.md    # Fase 3: 18 transformações com código antes/depois
```

### Decisões de design

- **O SKILL.md é o "roteiro" e as referências são o "conhecimento".** O `SKILL.md` só descreve o que fazer em cada fase, em que ordem e com qual formato de saída. Tudo que é conhecimento de domínio (como detectar um framework, o que é um God Class, como corrigir N+1) ficou nos arquivos de referência. Cada fase manda ler apenas a referência de que precisa naquele momento, o que deixa o contexto mais enxuto.
- **Uma referência por área de conhecimento.** Uma para cada uma das 5 áreas pedidas no desafio, com nomes que dizem o que contêm.
- **IDs cruzados.** Cada anti-pattern tem um ID (`AP-01`...) e aponta para uma transformação do playbook (`PB-01`...). O relatório cita os dois, então na Fase 3 a skill sabe exatamente qual correção aplicar para cada finding.
- **Pausa obrigatória.** A Fase 2 termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e uma instrução explícita para não ler, criar, editar ou executar nada até a resposta.
- **Validação baseada em linha de base.** Antes de mexer em qualquer arquivo, a Fase 3 sobe a aplicação original e chama todos os endpoints, guardando status e formato. Depois da refatoração ela repete as mesmas chamadas e compara. Assim "os endpoints continuam funcionando" deixa de ser uma impressão e vira uma tabela antes/depois.
- **Contrato preservado.** A refatoração mantém rotas, métodos, status e formato do JSON. As únicas mudanças permitidas são correções de segurança, e todas precisam aparecer na seção `API Contract Changes` do resumo.
- **Estilo do código gerado.** A skill pede para seguir o idioma e a convenção de nomes do projeto, não adicionar comentários explicativos e não instalar dependências novas quando a biblioteca padrão resolve (`werkzeug.security`, `itsdangerous`, `crypto` do Node).

### Anti-patterns do catálogo

| Severidade | Anti-patterns | Por que entraram |
|---|---|---|
| CRITICAL | AP-01 credenciais hardcoded, AP-02 SQL Injection, AP-03 God Class/File, AP-04 endpoint admin sem autenticação ou execução arbitrária, AP-05 senha insegura, AP-06 exposição de dados sensíveis | Todos apareceram na análise manual e são os que causam dano real: vazamento de dados, invasão ou um código impossível de manter. |
| HIGH | AP-07 Fat Controller, AP-08 estado global, AP-09 acoplamento sem DI, AP-10 escrita sem transação, AP-11 token falso, AP-12 debug fixo | São as violações de MVC/SOLID que mais travam teste e manutenção, além de duas falhas de segurança de configuração. |
| MEDIUM | AP-13 N+1, AP-14 callback hell, AP-15 validação, AP-16 erro genérico, AP-17 duplicação, AP-18 **APIs deprecated**, AP-19 registros órfãos | Performance e padronização. O AP-18 traz uma tabela de APIs obsoletas por stack (`datetime.utcnow`, `Query.get`, `new Buffer`, `req.param`...) com o substituto moderno. |
| LOW | AP-20 magic numbers, AP-21 nomes ruins, AP-22 código morto, AP-23 `print` como log, AP-24 condicionais verbosas | Legibilidade. São fáceis de corrigir junto com o resto. |

Para cada item escrevi **sinais de detecção concretos** em vez de descrições genéricas. Por exemplo, para N+1: "`execute`/`query`/`db.get`/`Model.query.get` dentro de `for`/`forEach`" e "cursores aninhados (`cursor2`, `cursor3`)". Isso fez diferença: a skill encontrou todos os problemas da análise manual com arquivo e linha.

### Como garanti que a skill é agnóstica de tecnologia

- As heurísticas da Fase 1 são tabelas de "sinal → conclusão" para várias linguagens e frameworks (Python, Node, Java, Go, PHP, Ruby; Flask, FastAPI, Django, Express, NestJS, Spring...).
- Os sinais de detecção do catálogo trazem exemplos de Python e de JavaScript lado a lado.
- O `mvc-guidelines.md` define as camadas pela **responsabilidade**, não pelo nome da pasta, e traz uma estrutura alvo para Flask e outra para Express.
- Há uma tabela de **adaptação por nível de organização**: monolito (cria as camadas do zero) e projeto parcialmente organizado (mantém o que está certo, por exemplo `routes/` como camada View, e move só o que está no lugar errado).
- O playbook mostra cada transformação em Python e/ou Node.
- A prova foi rodar a **mesma skill**, sem nenhuma alteração por projeto, em Flask monolítico, Express e Flask parcialmente organizado.

### Desafios encontrados e como resolvi

1. **Relatório fragmentado (iteração 1 → 2).** Na primeira versão eu pedia "um finding por arquivo". No `task-manager-api`, que tem vários arquivos de rotas, isso gerou **54 findings**: só o `datetime.utcnow` virou 7 itens. Mudei a regra para "um finding por anti-pattern, listando todos os arquivos no mesmo item". O mesmo projeto passou a ter **20 findings**, todos mais fáceis de ler.
2. **Autenticação quebrando o contrato.** Na primeira auditoria do `task-manager-api`, a skill planejava exigir token em todas as rotas de CRUD, o que faria todos os endpoints responderem 401. Restringi: autenticação só é exigida em rotas administrativas ou de manutenção (`/admin`, reset, relatório financeiro). Nas demais, a falta de autenticação fica como recomendação no relatório.
3. **Relatório dentro de bloco de código.** Como o template estava dentro de um bloco ```` ``` ```` no arquivo de referência, a skill repetia o bloco na saída. Deixei explícito que o relatório sai em Markdown puro.
4. **Porta 5000 ocupada no macOS.** O AirPlay Receiver usa a porta 5000, e os dois projetos Flask tinham a porta fixa no código. Coloquei na Fase 3 a instrução de usar outra porta via variável de ambiente quando a padrão estiver ocupada. A própria refatoração passou a ler `PORT` da config.
5. **Senhas antigas inválidas depois da troca de hash.** Ao trocar MD5 e texto puro por `werkzeug.security`, os bancos antigos deixam de validar login. A skill passou a recriar o seed antes de validar, e o README de cada projeto indica isso.

---

## Resultados

### Resumo das auditorias

| Projeto | Stack detectada | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1 | 8 | 7 | 5 | 4 | 24 | [audit-project-1.md](reports/audit-project-1.md) |
| ecommerce-api-legacy | Node.js + Express ^4.18.2 | 5 | 5 | 5 | 4 | 19 | [audit-project-2.md](reports/audit-project-2.md) |
| task-manager-api | Python + Flask 3.0.0 | 3 | 5 | 7 | 5 | 20 | [audit-project-3.md](reports/audit-project-3.md) |

A saída completa de cada execução (Fase 1, relatório, confirmação e resumo da Fase 3) está em [`reports/execution-logs/`](reports/execution-logs/).

Os relatórios dos projetos 1 e 2 foram gerados pela primeira versão da skill e o do projeto 3 pela versão final (depois do ajuste de agrupamento). As três cópias da skill no repositório estão na versão final.

### Antes e depois da estrutura

**Projeto 1 — code-smells-project**

```
ANTES                         DEPOIS
app.py                        app.py                      (create_app + run lendo config)
controllers.py                config/settings.py          (env vars + constantes de negócio)
models.py                     database/connection.py      (conexão por request via flask.g)
database.py                   database/schema.py
requirements.txt              database/seed.py            (senhas com hash)
                              models/produto_model.py
                              models/usuario_model.py
                              models/pedido_model.py
                              controllers/produto_controller.py
                              controllers/usuario_controller.py
                              controllers/pedido_controller.py
                              controllers/relatorio_controller.py
                              controllers/sistema_controller.py
                              controllers/validators.py
                              views/produto_routes.py     (blueprints por domínio)
                              views/usuario_routes.py
                              views/pedido_routes.py
                              views/sistema_routes.py
                              services/notificacao_service.py
                              middlewares/error_handler.py
                              middlewares/auth.py
                              .env.example
```

**Projeto 2 — ecommerce-api-legacy**

```
ANTES                         DEPOIS
src/app.js                    src/app.js                  (composition root com injeção de dependência)
src/AppManager.js             src/config/index.js, constants.js
src/utils.js                  src/database/connection.js  (Promise + transaction())
                              src/database/schema.js      (FKs com ON DELETE CASCADE + seed)
                              src/models/userModel.js, courseModel.js, enrollmentModel.js,
                                         paymentModel.js, auditLogModel.js, financialReport.js
                              src/controllers/checkoutController.js, reportController.js,
                                              userController.js, validators.js
                              src/routes/checkoutRoutes.js, reportRoutes.js, userRoutes.js
                              src/services/passwordService.js (scrypt), paymentService.js
                              src/middlewares/adminAuth.js, errorHandler.js
                              .env.example
```

**Projeto 3 — task-manager-api** (já tinha camadas, então a skill manteve `models/`, `routes/` e `services/`)

```
ANTES                         DEPOIS
app.py                        app.py                      (create_app + config)
database.py                   config/settings.py
seed.py                       database/connection.py, database/seed.py
models/ (3 arquivos)          models/ (mesmos 3, com regras de domínio e sem utcnow)
routes/task_routes.py (299)   routes/task_routes.py (56)  (rotas finas)
routes/user_routes.py (211)   routes/user_routes.py (57)
routes/report_routes.py (223) routes/report_routes.py (15)
                              routes/category_routes.py   (categorias saíram de report_routes)
                              routes/serializers.py       (sem password)
services/notification_...     services/notification_service.py (SMTP via config)
utils/helpers.py (morto)      services/token_service.py   (token assinado)
                              controllers/task, user, category, report + validators.py + transaction.py
                              middlewares/error_handler.py
                              .env.example
```

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1** | | | |
| Linguagem detectada corretamente | ✅ Python | ✅ JavaScript (Node.js) | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express ^4.18.2 | ✅ Flask 3.0.0 |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Número de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 13 |
| **Fase 2** | | | |
| Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 24 | ✅ 19 | ✅ 20 |
| Detecção de APIs deprecated | ✅ nenhuma (versões verificadas) | ✅ nenhuma (versões verificadas) | ✅ `Query.get`, `datetime.utcnow` |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** | | | |
| Estrutura de diretórios segue MVC | ✅ | ✅ | ✅ |
| Configuração em módulo de config (sem hardcoded) | ✅ `config/settings.py` | ✅ `src/config/` | ✅ `config/settings.py` |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `views/` | ✅ `src/routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `create_app()` | ✅ `createApp()` | ✅ `create_app()` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ (inclusive com `-W error::DeprecationWarning`) |
| Endpoints originais respondem corretamente | ✅ 33/33 chamadas | ✅ 7/7 chamadas | ✅ 30/30 chamadas |

### Mudanças de contrato (todas por segurança)

| Projeto | Mudança |
|---|---|
| 1 | `POST /admin/query` removido (executava SQL arbitrário). `POST /admin/reset-db` passou a exigir `Authorization: Bearer <token>` de admin. `/usuarios` não devolve mais `senha`. `/health` não devolve mais `secret_key`, `db_path` e `debug`. O login ganhou o campo `token`. |
| 2 | `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header `X-Admin-Token`. O DELETE agora remove as matrículas e os pagamentos do usuário. |
| 3 | O campo `password` não é mais devolvido. O `token` do login passou a ser assinado. |

Além disso, nos três projetos entradas inválidas que antes geravam erro 500 agora retornam 400.

### Logs das aplicações rodando após a refatoração

Testes feitos à mão depois de cada refatoração, sem usar a saída da skill.

**Projeto 1** (`PORT=5071 python app.py`)
```
/                        200
/health                  200
/produtos                200
/produtos/1              200
/produtos/busca?q=mouse  200
/usuarios                200
/usuarios/1              200
/pedidos                 200
/relatorios/vendas       200

GET /health
{"ambiente":"desenvolvimento","counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}

GET /usuarios/1   (sem senha)
{"dados":{"criado_em":"2026-10-14 12:33:10","email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"},"sucesso":true}

POST /pedidos
{"dados":{"pedido_id":1,"total":89.9},"mensagem":"Pedido criado com sucesso","sucesso":true}

POST /login com email "admin@loja.com' OR '1'='1"   (SQL injection bloqueado)
{"erro":"Email ou senha inválidos","sucesso":false} [401]
```

**Projeto 2** (`PORT=3101 ADMIN_TOKEN=segredo-local node src/app.js`)
```
Frankenstein LMS rodando na porta 3101...

POST /api/checkout (cartão 4111...)        {"msg":"Sucesso","enrollment_id":2} [200]
POST /api/checkout (cartão 5111...)        Pagamento recusado [400]
GET  /api/admin/financial-report           Acesso restrito a administradores [401]
GET  /api/admin/financial-report + token   [{"course":"Clean Architecture","revenue":997,...},{"course":"Docker","revenue":497,...}] [200]
DELETE /api/users/1 + token                Usuário deletado com suas matrículas e pagamentos. [200]
```
O log do servidor não mostra mais o número do cartão nem a chave do gateway.

**Projeto 3** (`python -m database.seed` e `PORT=5072 python -W error::DeprecationWarning app.py`)
```
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
/                      200
/health                200
/tasks                 200
/tasks/1               200
/tasks/search?q=API    200
/tasks/stats           200
/users                 200
/users/1               200
/users/1/tasks         200
/reports/summary       200
/reports/user/1        200
/categories            200

POST /login   (token assinado, sem password)
{"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxfQ.as93gg.J9CRyBBSFhtx8usQwODAX5Wm5i8","user":{"active":true,"created_at":"...","email":"joao@email.com","id":1,"name":"João Silva","role":"admin"}}
```

### Observações sobre o comportamento em stacks diferentes

- **Flask monolítico (projeto 1):** foi o caso com mais trabalho. A skill criou todas as camadas do zero, trocou a conexão global por conexão por request (`flask.g`) e resolveu o N+1 com um único JOIN. Também removeu o endpoint de SQL arbitrário, a única correção que mudou o contrato de forma mais forte.
- **Express (projeto 2):** a parte mais interessante foi o callback hell. A skill criou um wrapper com Promises para o `sqlite3`, reescreveu tudo com `async/await` e adicionou um `transaction()` com fila, para que checkouts simultâneos não misturem transações no mesmo banco em memória (ela testou com 6 checkouts em paralelo). As variáveis do contrato (`usr`, `eml`, `c_id`) continuaram aceitas na borda HTTP.
- **Flask parcialmente organizado (projeto 3):** a skill reconheceu que `models/` e `routes/` já existiam e **não recriou** essas pastas. Ela criou `controllers/` e deixou as rotas finas (de 299 para 56 linhas em `task_routes.py`). Também separou as rotas de categoria que estavam dentro de `report_routes.py`, reaproveitou o `Task.is_overdue()` que já existia e removeu o `utils/` inteiro, que só tinha código morto.
- **Em todas:** a auditoria encontrou todos os problemas que eu tinha listado na análise manual, além de outros que eu não tinha anotado (por exemplo, dependências não usadas no `requirements.txt` do projeto 3 e o `NotificationService`, que nunca era chamado).

---

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude auth login`)
- Python 3.10+ (testei com 3.13) para os projetos Flask
- Node.js 18+ (testei com 22) para o projeto Express

### Preparar os ambientes

```bash
git clone https://github.com/DiArcanjo/mba-ia-refactor-projects-skill.git
cd mba-ia-refactor-projects-skill

cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cd task-manager-api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cd ecommerce-api-legacy && npm install && cd ..
```

### Executar a skill

A skill já está em `.claude/skills/refactor-arch/` dentro de cada projeto. Para rodar em um projeto ainda não refatorado (por exemplo, a partir do commit inicial `6d1ce62`):

```bash
cd code-smells-project
claude "/refactor-arch"
```

```bash
cd ecommerce-api-legacy
claude "/refactor-arch"
```

```bash
cd task-manager-api
claude "/refactor-arch"
```

A skill imprime a Fase 1, o relatório da Fase 2 e para em `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar.

Para rodar sem modo interativo (como eu fiz), use dois comandos: o primeiro executa as Fases 1 e 2, o segundo retoma a mesma sessão com a confirmação.

```bash
claude -p "/refactor-arch" --output-format json --permission-mode acceptEdits --allowedTools "Bash Read Glob Grep Edit Write"
```

```bash
claude -p "y" --resume <session_id> --output-format json --permission-mode acceptEdits --allowedTools "Bash Read Glob Grep Edit Write"
```

### Validar que a refatoração funcionou

**Projeto 1**
```bash
cd code-smells-project
PORT=5001 .venv/bin/python app.py
curl http://127.0.0.1:5001/health
curl http://127.0.0.1:5001/produtos
```

**Projeto 2**
```bash
cd ecommerce-api-legacy
ADMIN_TOKEN=meu-token npm start
curl -X POST http://localhost:3000/api/checkout -H 'Content-Type: application/json' -d '{"usr":"Ana","eml":"ana@x.com","pwd":"senha","c_id":1,"card":"4111222233334444"}'
curl -H 'X-Admin-Token: meu-token' http://localhost:3000/api/admin/financial-report
```
Também dá para usar o arquivo `api.http`.

**Projeto 3**
```bash
cd task-manager-api
.venv/bin/python -m database.seed
PORT=5002 .venv/bin/python app.py
curl http://127.0.0.1:5002/tasks
curl http://127.0.0.1:5002/reports/summary
```

> No macOS a porta 5000 costuma estar ocupada pelo AirPlay Receiver, por isso os exemplos usam `PORT=5001`/`5002`.
