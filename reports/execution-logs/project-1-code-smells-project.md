# Execução da skill — code-smells-project

Saída do `claude "/refactor-arch"` executado dentro de `code-smells-project/`.

## Fases 1 e 2

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (versão não declarada no projeto)
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Database:      SQLite (loja.db), driver cru `sqlite3` com conexão global
Domain:        E-commerce (loja): produtos, usuários, pedidos, itens de pedido, relatório de vendas
Architecture:  Camadas parciais (app.py = rotas, controllers.py, models.py, database.py), com
               responsabilidades misturadas: SQL, serialização e regra de negócio em models.py;
               validação, notificações e acesso direto ao banco em controllers.py; handlers
               administrativos com SQL dentro de app.py; sem camada de config
Source files:  4 files analyzed | ~780 lines of code
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 (GET / | GET,POST /produtos | GET /produtos/busca | GET,PUT,DELETE /produtos/<id> |
               GET,POST /usuarios | GET /usuarios/<id> | POST /login | GET,POST /pedidos |
               GET /pedidos/usuario/<id> | PUT /pedidos/<id>/status | GET /relatorios/vendas |
               GET /health | POST /admin/reset-db | POST /admin/query)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-14

## Summary
CRITICAL: 8 | HIGH: 7 | MEDIUM: 5 | LOW: 4 | Total: 24

## Findings

### #1 [CRITICAL] Credenciais e segredos hardcoded (AP-01)
File: app.py:7
Evidence: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`
Description: A SECRET_KEY do Flask está literal no código-fonte, sem leitura de variável de ambiente.
Impact: Qualquer pessoa com acesso ao repositório conhece a chave, e trocá-la exige novo deploy.
Recommendation: Mover para um módulo de config lido de variável de ambiente, com `.env.example` e default seguro para desenvolvimento (PB-01).

### #2 [CRITICAL] Credenciais e segredos hardcoded (AP-01)
File: controllers.py:289
Evidence: `"secret_key": "minha-chave-super-secreta-123"`
Description: O mesmo segredo é repetido como literal no handler de health e devolvido ao cliente.
Impact: Duplica o segredo no código e o publica numa rota sem autenticação.
Recommendation: Remover o segredo da resposta e usar apenas a configuração central (PB-01).

### #3 [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 291-297
Evidence: `cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")`
Description: Todas as queries de produtos, usuários, pedidos e busca são montadas por concatenação com valores vindos do request, inclusive o login e o `LIKE '%" + termo + "%'`.
Impact: `' OR '1'='1` no login autentica sem senha; o termo de busca permite ler qualquer tabela; o status do pedido permite alterar dados.
Recommendation: Usar queries parametrizadas com `?` em todas as consultas (PB-02).

### #4 [CRITICAL] God File (AP-03)
File: models.py:1-314
Evidence: `def get_todos_produtos(): ... def login_usuario(...): ... def criar_pedido(...): ... def relatorio_vendas():`
Description: Um único arquivo com 314 linhas mistura SQL, serialização e regra de negócio (estoque, total do pedido, faixas de desconto) de quatro domínios. O schema e o seed também ficam no mesmo módulo de conexão (`database.py:14-84`).
Impact: Impossível testar em isolamento; qualquer mudança afeta todos os domínios (viola SRP).
Recommendation: Separar em models por entidade, repositórios/serviços para regras e camada de config/banco dedicada (PB-03).

### #5 [CRITICAL] Endpoint administrativo/destrutivo sem autenticação e execução arbitrária de SQL (AP-04)
File: app.py:47-57, 59-78
Evidence: `cursor.execute(query)` com `query = dados.get("sql", "")`; `cursor.execute("DELETE FROM usuarios")`
Description: `/admin/query` executa qualquer SQL enviado no corpo, e `/admin/reset-db` apaga todas as tabelas, ambos sem autenticação. Os handlers também chamam `get_db()` e fazem SQL direto em app.py (`app.py:4, 49, 66`).
Impact: Qualquer cliente pode apagar ou ler o banco inteiro, inclusive senhas.
Recommendation: Remover `/admin/query`; proteger `/admin/reset-db` com autenticação/autorização de admin (ou removê-lo) e mover a lógica para um controller (PB-04).

### #6 [CRITICAL] Armazenamento inseguro de senha (AP-05)
File: models.py:105-120, 122-131; controllers.py:160; database.py:76-78
Evidence: `"INSERT INTO usuarios (nome, email, senha, tipo) VALUES ('" + nome + "', '" + email + "', '" + senha + "', '" + tipo + "')"`
Description: A senha é gravada em texto puro, comparada diretamente em SQL no login, e as senhas do seed (`admin123`, `123456`) também estão em texto puro.
Impact: Um vazamento do banco expõe todas as senhas imediatamente.
Recommendation: Hash com `werkzeug.security` (`generate_password_hash`/`check_password_hash`), busca por e-mail e verificação em código; seed com hash (PB-05).

### #7 [CRITICAL] Exposição de dados sensíveis (AP-06)
File: models.py:83, 99
Evidence: `"senha": row["senha"],`
Description: `GET /usuarios` e `GET /usuarios/<id>` devolvem a senha de cada usuário na resposta.
Impact: Qualquer cliente lê as senhas de todos os usuários (LGPD).
Recommendation: Serializar usuário sem o campo `senha` (PB-06).

### #8 [CRITICAL] Exposição de dados sensíveis (AP-06)
File: controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 287-289, 292
Evidence: `"db_path": "loja.db", "debug": True, "secret_key": "minha-chave-super-secreta-123"`; `return jsonify({"erro": str(e)}), 500`
Description: O health devolve `secret_key`, `db_path` e flag de debug, e os handlers devolvem `str(e)` de exceções internas ao cliente (também em `app.py:78`).
Impact: Vaza segredo, caminho do banco e detalhes internos que facilitam ataques.
Recommendation: Health apenas com status e contagens; erros genéricos ao cliente e detalhe só em log (PB-06, PB-14).

### #9 [HIGH] Regra de negócio no controller (AP-07)
File: controllers.py:24-62, 64-96, 188-220, 237-255, 264-292
Evidence: `if novo_status == "cancelado": print("NOTIFICAÇÃO: ... Devolver estoque.")`
Description: Handlers extensos concentram validação, lista de categorias/status, notificações simuladas e acesso direto ao banco (health). Em `models.py:256-262` o cálculo de desconto do relatório também vive na camada de dados.
Impact: Regras não reutilizáveis e testáveis só via HTTP.
Recommendation: Extrair regras para serviços/models e deixar controllers só orquestrando (PB-07).

### #10 [HIGH] Estado global mutável (AP-08)
File: database.py:4-5, 8-10
Evidence: `global db_connection`
Description: A conexão SQLite é uma variável de módulo reatribuída por `global`, compartilhada entre requisições (`check_same_thread=False`).
Impact: Compartilhamento de conexão entre threads, impossível isolar em testes.
Recommendation: Conexão por requisição (`g`/teardown) ou provider injetável (PB-08).

### #11 [HIGH] Acoplamento forte sem injeção de dependência (AP-09)
File: models.py:1, 5, 25, 44, 56, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286
Evidence: `from database import get_db` / `db = get_db()`
Description: Todas as funções do model obtêm a conexão chamando o `get_db()` global.
Impact: Não é possível substituir o banco por fake/mock; trocar de banco exige mexer em tudo.
Recommendation: Receber a conexão/repositório por parâmetro ou factory (PB-08).

### #12 [HIGH] Acoplamento forte sem injeção de dependência (AP-09)
File: controllers.py:3, 266
Evidence: `from database import get_db` / `db = get_db()` em `health_check`
Description: O controller acessa o banco diretamente, pulando a camada de model.
Impact: Controller acoplado ao driver; regra de acesso a dados fora do model.
Recommendation: Mover as contagens para o model/serviço (PB-08).

### #13 [HIGH] Escritas em múltiplas etapas sem transação (AP-10)
File: models.py:148-168
Evidence: `cursor.execute("INSERT INTO pedidos ...")` … `cursor.execute("UPDATE produtos SET estoque = estoque - ...")` … `db.commit()`
Description: Pedido, itens e baixa de estoque são escritos em sequência com um único commit no fim e sem `rollback` em caso de erro. A validação de estoque (140-146) também é feita separada da baixa.
Impact: Uma falha no meio deixa pedido sem itens ou estoque inconsistente, e a conexão compartilhada mantém a transação suja.
Recommendation: Envolver a criação do pedido em transação com `commit`/`rollback` (PB-09).

### #14 [HIGH] Autenticação falsa (AP-11)
File: controllers.py:167-186
Evidence: `return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200`
Description: O login só devolve o usuário; nenhum token é emitido e nenhuma rota valida credencial depois, nem as administrativas.
Impact: Falsa sensação de segurança; todas as rotas são acessíveis anonimamente.
Recommendation: Emitir token assinado com expiração e exigir autenticação nas rotas administrativas (PB-10).

### #15 [HIGH] Debug e bind aberto fixos no código (AP-12)
File: app.py:8, 88
Evidence: `app.run(host="0.0.0.0", port=5000, debug=True)`
Description: Debug, host e porta estão fixos no código, além de `app.config["DEBUG"] = True`.
Impact: O debugger do Werkzeug permite execução remota de código e expõe a aplicação em todas as interfaces.
Recommendation: Ler DEBUG/HOST/PORT de variáveis de ambiente com default seguro (PB-01).

### #16 [MEDIUM] Queries N+1 (AP-13)
File: models.py:139-146, 154-166, 187-193, 219-225
Evidence: `cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))`
Description: Listagens de pedidos fazem uma query de itens por pedido e uma de produto por item; `criar_pedido` consulta o produto em loop duas vezes.
Impact: 1 + N + N×M idas ao banco, degradando com o volume.
Recommendation: Usar JOIN (itens + produtos) e buscar produtos em lote (PB-11).

### #17 [MEDIUM] Validação ausente, inconsistente ou duplicada (AP-15)
File: controllers.py:30-50, 74-90, 169-171, 195-201, 239-242
Evidence: `if preco < 0:` / `dados = request.get_json()` / `dados.get("email", "")`
Description: A validação de produto está duplicada entre create e update, e o update não valida tamanho do nome nem categoria. Não há checagem de tipo (`preco < 0` com string vira 500), `get_json()` é usado sem checar `None` no login e no status, e itens do pedido e existência do usuário não são validados. (Em `app.py:61-62` o mesmo vale para `/admin/query`.)
Impact: Dados inválidos chegam ao banco ou geram 500 em vez de 400; regras divergem entre create e update.
Recommendation: Centralizar validação em funções reutilizáveis com checagem de tipo (PB-13).

### #18 [MEDIUM] Tratamento de erro genérico e não centralizado (AP-16)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
Evidence: `except Exception as e: return jsonify({"erro": str(e)}), 500`
Description: Todo handler repete o mesmo try/except genérico, e não existe `@app.errorhandler` (também em `app.py:77-78`).
Impact: Código repetido, erros internos expostos e status inadequados (ex.: JSON inválido vira 500).
Recommendation: Error handlers globais e exceções de domínio mapeadas para status HTTP (PB-14).

### #19 [MEDIUM] Código duplicado (AP-17)
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 178-199, 211-231
Evidence: `result.append({"id": row["id"], "nome": row["nome"], ...})`
Description: O dicionário de produto é repetido em 3 funções, o de usuário em 2, e `get_pedidos_usuario` e `get_todos_pedidos` são quase idênticas.
Impact: Mudanças de campo precisam ser replicadas em vários lugares.
Recommendation: Funções únicas de serialização e uma query parametrizada para pedidos (PB-15).

### #20 [MEDIUM] Exclusão sem integridade referencial (AP-19)
File: models.py:65-70
Evidence: `cursor.execute("DELETE FROM produtos WHERE id = " + str(id))`
Description: Produtos são apagados sem tratar `itens_pedido` que os referenciam, e o schema (`database.py:36-53`) não declara FOREIGN KEY. Cancelar pedido também não devolve estoque, apesar da mensagem em `controllers.py:250`.
Impact: Itens órfãos e pedidos que mostram produto "Desconhecido".
Recommendation: Declarar FKs/regra de exclusão e tratar dependências na mesma transação (PB-09).

### #21 [LOW] Magic numbers e strings soltas (AP-20)
File: models.py:150, 247-262; controllers.py:47-52, 242
Evidence: `if faturamento > 10000: desconto = faturamento * 0.1`
Description: Faixas de desconto, limites de nome, categorias e status válidos estão como literais soltos.
Impact: Regras de negócio difíceis de encontrar e alterar.
Recommendation: Extrair para constantes nomeadas no módulo de domínio/config (PB-17).

### #22 [LOW] Nomenclatura ruim (AP-21)
File: models.py:24, 54, 65, 89, 187-191, 219-223; controllers.py:14, 24, 56, 160
Evidence: `cursor2 = db.cursor()` / `cursor3 = db.cursor()` / `def get_produto_por_id(id)`
Description: `id` sombreia o builtin e há cursores numerados em vez de nomes descritivos.
Impact: Leitura mais difícil e risco de bugs por sombreamento.
Recommendation: Renomear para `produto_id`/`item_cursor` etc., mantendo o contrato HTTP (PB-17).

### #23 [LOW] Imports não usados (AP-22)
File: models.py:2; database.py:2
Evidence: `import sqlite3` / `import os`
Description: Imports sem nenhum uso nos módulos.
Impact: Ruído e confusão sobre dependências reais.
Recommendation: Remover imports não usados (PB-18).

### #24 [LOW] print no lugar de logger e efeitos simulados (AP-23)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248-250; app.py:56, 83-86
Evidence: `print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado ...")`
Description: Logs e envio simulado de email/SMS/push são feitos com `print`.
Impact: Sem níveis de log, e o "envio" não existe de verdade.
Recommendation: Usar `logging` e isolar notificações num serviço (PB-18).

## Deprecated APIs
None detected (verificado contra flask==3.1.1 e flask-cors==5.0.1; nenhum uso de `before_first_request`, `json_encoder`, `datetime.utcnow` etc.).

## Architecture Notes
Camadas parciais: rotas em app.py, controllers e models existem, mas models.py acumula SQL, serialização e regra de negócio, e controllers.py acessa o banco e faz validação extensa. Não há config isolada nem error handling central.
A Fase 3 vai criar config (env), conexão por requisição, models/repositórios por entidade, services para regras (pedido, relatório), controllers finos, rotas em blueprints, validação e error handlers centralizados.

================================
Total: 24 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

## Confirmação

```
> y
```

## Fase 3

All remaining matches are false positives. They are fixed SQL fragments or constant table names, and every user value goes through `?` parameters.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
code-smells-project/
├── app.py                      # create_app() + run via config
├── config/settings.py          # Config (env vars) + constantes de negócio
├── database/
│   ├── connection.py           # conexão por request (flask.g)
│   ├── schema.py               # DDL + init_db
│   └── seed.py                 # dados iniciais (senhas com hash)
├── models/                     # produto_, usuario_, pedido_model (SQL parametrizado)
├── controllers/                # produto, usuario, pedido, relatorio, sistema + validators.py
├── views/                      # Blueprints por domínio
├── services/notificacao_service.py
├── middlewares/                # error_handler.py, auth.py
├── .env.example
├── README.md
└── requirements.txt
(removidos: models.py, controllers.py, database.py)

## Findings Addressed
- [CRITICAL] #1/#2 Segredo hardcoded → Config via env (SECRET_KEY aleatória sem env), removido do /health (PB-01)
- [CRITICAL] #3 SQL Injection → queries parametrizadas (PB-02)
- [CRITICAL] #4 God file → models/controllers/views/services por domínio (PB-03)
- [CRITICAL] #5 Admin sem auth / SQL arbitrário → /admin/query removido; /admin/reset-db exige token de admin (PB-04)
- [CRITICAL] #6 Senha em texto puro → werkzeug hash + check_password_hash (PB-05)
- [CRITICAL] #7/#8 Dados sensíveis expostos → sem `senha`, sem secret/db_path/debug no /health, sem `str(e)` ao cliente (PB-06)
- [HIGH] #9 Regra no controller → regras em models/service, controllers finos (PB-07)
- [HIGH] #10/#11/#12 Estado global e get_db acoplado → conexão por request, `db` injetado nos models (PB-08)
- [HIGH] #13 Pedido sem transação → commit/rollback em `pedido_model.criar` (PB-09)
- [HIGH] #14 Auth falsa → token assinado (itsdangerous) com expiração (PB-10)
- [HIGH] #15 Debug/bind fixos → HOST/PORT/FLASK_DEBUG por env, default 127.0.0.1 e debug off (PB-01)
- [MEDIUM] #16 N+1 → JOIN único nas listagens; busca de produtos por IN (PB-11)
- [MEDIUM] #17 Validação → validators.py compartilhado, com checagem de tipo (PB-13)
- [MEDIUM] #18 Erro genérico → error handler central com exceções de domínio (PB-14)
- [MEDIUM] #19 Duplicação → listagem de pedidos e serialização unificadas (PB-15)
- [MEDIUM] #20 Integridade referencial → FKs em itens_pedido + PRAGMA foreign_keys=ON (PB-09)
- [LOW] #21/#22 Magic numbers e nomes → constantes em config, nomes claros (PB-17)
- [LOW] #23/#24 Imports/prints → imports limpos, `logging` e notification service (PB-18)

## API Contract Changes
- GET /usuarios, GET /usuarios/<id>: não retornam mais `senha` (segurança)
- GET /health: removidos `secret_key`, `db_path`, `debug`; `ambiente` agora vem da config ("desenvolvimento" por padrão, antes "producao" fixo)
- POST /admin/query: removido (executava SQL arbitrário; agora 404)
- POST /admin/reset-db: exige `Authorization: Bearer <token>` de admin (401 sem ele)
- POST /login: resposta ganha o campo aditivo `token` (usado no reset-db)
- Erros 500 retornam mensagem genérica ("Erro interno do servidor") em vez de `str(e)`
- Entradas inválidas que antes davam 500 agora dão 400: JSON ausente no login/status, preço/estoque não numérico, `preco_min`/`preco_max` inválidos, item de pedido malformado ou com quantidade <= 0
- Itens de pedido cujo produto foi deletado passam a ter `produto_id` nulo (FK `ON DELETE SET NULL`); `produto_nome` continua "Desconhecido"

## Validation
  ✓ Application boots without errors (`PORT=5056 python app.py`, sem warnings de import)
  ✓ 33/33 chamadas respondem como antes; as 3 divergências de status/corpo são as mudanças de segurança acima
  ✓ Zero anti-patterns remaining from the audit (grep: sem concatenação SQL com valores, `print`, `global`, `debug=True`, `utcnow`, `str(e)` ou segredos literais)
  Login com `' OR '1'='1` → 401; busca com `' OR 1=1--` → 0 resultados; reset-db com token admin → 200, com token de cliente → 401

  método | rota                              | antes | depois
  GET    | /                                 | 200   | 200
  GET    | /health                           | 200   | 200
  GET    | /produtos                         | 200   | 200
  GET    | /produtos/busca (q; filtros)      | 200   | 200
  GET    | /produtos/1 · /produtos/999       | 200·404 | 200·404
  POST   | /produtos (ok·inválido·categoria) | 201·400·400 | 201·400·400
  PUT    | /produtos/11 · /produtos/999      | 200·404 | 200·404
  DELETE | /produtos/11 · /produtos/999      | 200·404 | 200·404
  GET    | /usuarios · /usuarios/1 · /999    | 200·200·404 | 200·200·404
  POST   | /usuarios (ok·inválido)           | 201·400 | 201·400
  POST   | /login (ok·senha errada·sem senha)| 200·401·400 | 200·401·400
  POST   | /pedidos (ok·404·estoque·vazio)   | 201·400·400·400 | 201·400·400·400
  GET    | /pedidos · /pedidos/usuario/2     | 200·200 | 200·200
  PUT    | /pedidos/1/status (ok·inválido)   | 200·400 | 200·400
  GET    | /relatorios/vendas                | 200   | 200
  POST   | /admin/reset-db                   | 200   | 401 (sem token; mudança de segurança)
  POST   | /admin/query                      | 200   | 404 (removido; mudança de segurança)
================================
```

A porta 5000 estava ocupada (AirPlay), então testei em 5055 (original) e 5056/5057 (refatorada). Removi `loja.db` e os arquivos temporários. Não fiz commit.

`git status` mostra mudanças em `../ecommerce-api-legacy/` que não vieram desta refatoração.
