# Catálogo de Anti-patterns

Use este catálogo na Fase 2. Cada item tem ID, severidade padrão, sinais de detecção concretos (por stack) e a transformação correspondente no playbook (`PB-xx`).

## Escala de severidade

| Severidade | Critério |
|---|---|
| **CRITICAL** | Falha grave de segurança ou arquitetura: expõe dados sensíveis, permite injeção/execução arbitrária, ou viola completamente a separação de responsabilidades (God Class com banco + regra + rota no mesmo lugar). |
| **HIGH** | Forte violação de MVC/SOLID que dificulta muito manutenção e testes: regra de negócio pesada em controller/rota, acoplamento sem injeção de dependência, estado global mutável, operações sem transação. |
| **MEDIUM** | Padronização, duplicação, performance moderada: N+1, validação ausente ou duplicada, tratamento de erro inadequado, APIs deprecated. |
| **LOW** | Legibilidade: nomes ruins, magic numbers, imports não usados, `print` como log, condicionais verbosas. |

Ajuste a severidade padrão apenas com justificativa explícita no finding (ex.: API deprecated que já quebra na versão instalada sobe para HIGH).

## Resumo

| ID | Anti-pattern | Severidade | Playbook |
|---|---|---|---|
| AP-01 | Credenciais e segredos hardcoded | CRITICAL | PB-01 |
| AP-02 | SQL Injection por concatenação/interpolação | CRITICAL | PB-02 |
| AP-03 | God Class / God File | CRITICAL | PB-03 |
| AP-04 | Endpoint administrativo ou destrutivo sem autenticação / execução arbitrária | CRITICAL | PB-04 |
| AP-05 | Armazenamento inseguro de senha | CRITICAL | PB-05 |
| AP-06 | Exposição de dados sensíveis em respostas ou logs | CRITICAL | PB-06 |
| AP-07 | Regra de negócio na rota/controller (Fat Controller) | HIGH | PB-07 |
| AP-08 | Estado global mutável | HIGH | PB-08 |
| AP-09 | Acoplamento forte sem injeção de dependência | HIGH | PB-08 |
| AP-10 | Escritas em múltiplas etapas sem transação | HIGH | PB-09 |
| AP-11 | Autenticação falsa / token simulado | HIGH | PB-10 |
| AP-12 | Modo debug e bind aberto fixos no código | HIGH | PB-01 |
| AP-13 | Queries N+1 | MEDIUM | PB-11 |
| AP-14 | Callback hell / pirâmide de callbacks | MEDIUM | PB-12 |
| AP-15 | Validação ausente, inconsistente ou duplicada | MEDIUM | PB-13 |
| AP-16 | Tratamento de erro genérico e não centralizado | MEDIUM | PB-14 |
| AP-17 | Código duplicado (lógica de domínio/serialização repetida) | MEDIUM | PB-15 |
| AP-18 | Uso de APIs deprecated | MEDIUM | PB-16 |
| AP-19 | Exclusão sem integridade referencial (registros órfãos) | MEDIUM | PB-09 |
| AP-20 | Magic numbers e strings soltas | LOW | PB-17 |
| AP-21 | Nomenclatura ruim | LOW | PB-17 |
| AP-22 | Imports não usados e código morto | LOW | PB-18 |
| AP-23 | `print`/`console.log` no lugar de logger; efeitos colaterais simulados com print | LOW | PB-18 |
| AP-24 | Condicionais verbosas (`if x: return True else: return False`) | LOW | PB-18 |

---

## CRITICAL

### AP-01 — Credenciais e segredos hardcoded
**Sinais de detecção**
- Atribuição literal a nomes como `SECRET_KEY`, `password`, `pass`, `pwd`, `token`, `api_key`, `apiKey`, `*_KEY`, `*_SECRET`, `dbPass`, `smtp*`.
- Prefixos de chaves reais: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xox`.
- Objetos de configuração com segredos (`const config = { dbPass: "..." }`, `app.config["SECRET_KEY"] = "..."`).
- Segredo repetido em outro lugar (ex.: devolvido no `/health`).

**Por que importa:** qualquer pessoa com acesso ao repositório tem as credenciais; trocar o valor exige deploy; impossível ter valores diferentes por ambiente.

### AP-02 — SQL Injection
**Sinais de detecção**
- Python: `cursor.execute("... " + var)`, `execute(f"... {var}")`, `execute("..." % var)`, `.format(` em string SQL.
- Node: `db.run("... " + var)`, template string com `${}` dentro de SQL.
- `LIKE '%" + termo + "%'`.
- Query montada incrementalmente com `+=` usando entrada do usuário.

**Por que importa:** permite ler, alterar ou apagar qualquer dado (`' OR '1'='1`).

### AP-03 — God Class / God File
**Sinais de detecção**
- Um arquivo/classe que contém ao mesmo tempo: conexão/schema de banco, queries, regra de negócio e definição de rotas.
- Classes com nomes genéricos (`AppManager`, `Utils`, `Helper`, `Manager`) com métodos de domínios diferentes.
- Arquivo "models" que faz SQL + validação + formatação de 3+ domínios.
- Arquivo com mais de ~250 linhas misturando entidades diferentes.

**Por que importa:** impossível testar em isolamento; qualquer mudança afeta tudo; viola SRP.

### AP-04 — Endpoint administrativo/destrutivo sem autenticação ou execução arbitrária
**Sinais de detecção**
- Rotas `/admin/*`, `reset`, `drop`, `query`, `exec`, `DELETE` em massa sem verificação de autenticação/autorização.
- Endpoint que recebe SQL, comando ou código no corpo e executa (`cursor.execute(dados["sql"])`, `eval`, `exec`, `child_process.exec`).
- Rotas de relatório financeiro ou exclusão de usuários acessíveis sem autenticação.

**Por que importa:** qualquer cliente pode apagar o banco ou executar SQL arbitrário.

### AP-05 — Armazenamento inseguro de senha
**Sinais de detecção**
- Senha salva como recebida (`INSERT ... senha` com o valor do request) ou comparada em SQL (`WHERE senha = '...'`).
- Hash rápido/quebrado: `hashlib.md5`, `hashlib.sha1`, `sha256` sem salt, `crypto.createHash('md5')`.
- "Criptografia" caseira: base64, loops de concatenação, `Buffer.from(pwd).toString('base64')`.
- Senha default aplicada quando o usuário não envia (`p || "123456"`).

**Por que importa:** vazamento do banco expõe todas as senhas; MD5/base64 são revertidos em segundos.

### AP-06 — Exposição de dados sensíveis
**Sinais de detecção**
- Serialização de usuário incluindo `senha`/`password`/hash (`to_dict()` com password, `SELECT *` devolvido direto).
- Health/debug endpoint devolvendo `secret_key`, `db_path`, flags de debug.
- Logs com dados de cartão, senha, token ou chave (`console.log(\`Processando cartão ${cc}...\`)`).
- `str(e)` de exceções do banco devolvido ao cliente.

**Por que importa:** vaza segredo, dado pessoal e dado financeiro (PCI-DSS, LGPD).

---

## HIGH

### AP-07 — Regra de negócio na rota/controller (Fat Controller)
**Sinais de detecção**
- Handler HTTP com cálculos de domínio (descontos, totais, estoque, status), validações extensas e montagem de resposta no mesmo bloco.
- Handlers com mais de ~40 linhas.
- Regras de transição de status, notificações e efeitos colaterais dentro do handler.
- Lógica de pagamento/checkout dentro da definição da rota.

**Por que importa:** regra de negócio não reutilizável e testável só via HTTP.

### AP-08 — Estado global mutável
**Sinais de detecção**
- `global` em Python; variáveis de módulo reatribuídas (`db_connection = None` + `global db_connection`).
- `let globalCache = {}`, `let totalRevenue = 0` exportados e mutados.
- Listas/dicts de módulo usados como armazenamento (`self.notifications = []` em serviço instanciado por request ou singleton).

**Por que importa:** condições de corrida, vazamento entre requisições, testes que dependem de ordem.

### AP-09 — Acoplamento forte sem injeção de dependência
**Sinais de detecção**
- Handlers/models que chamam `get_db()` global ou instanciam conexão/serviço dentro do método.
- Classe que cria a própria conexão no construtor (`this.db = new sqlite3.Database(...)`).
- Import direto de módulos concretos para efeitos colaterais (SMTP, gateway) dentro de regra de negócio.

**Por que importa:** impossível substituir por mock/fake em testes; troca de banco exige mexer em todo lugar.

### AP-10 — Escritas em múltiplas etapas sem transação
**Sinais de detecção**
- Sequência de `INSERT`/`UPDATE` relacionados (pedido + itens + baixa de estoque; matrícula + pagamento) sem `BEGIN/COMMIT/ROLLBACK` ou `with transaction`.
- `return` de erro no meio de um loop que já executou escritas.
- `commit()` só no final, sem `rollback()` no caminho de erro.

**Por que importa:** falha no meio deixa o banco inconsistente (pedido sem itens, cobrança sem matrícula).

### AP-11 — Autenticação falsa / token simulado
**Sinais de detecção**
- Token construído com string fixa (`'fake-jwt-token-' + id`), sem assinatura nem expiração.
- Login que retorna o usuário mas nenhuma rota valida credencial depois.

**Por que importa:** dá falsa sensação de segurança; qualquer um forja o token.

### AP-12 — Debug e bind aberto fixos no código
**Sinais de detecção**
- `app.run(debug=True)`, `app.config["DEBUG"] = True`, `host="0.0.0.0"` fixos.
- Porta fixa sem leitura de variável de ambiente.

**Por que importa:** o debugger do Werkzeug permite execução remota de código; configuração de produção vira a de desenvolvimento.

---

## MEDIUM

### AP-13 — Queries N+1
**Sinais de detecção**
- `execute`/`query`/`db.get`/`Model.query.get` dentro de `for`/`forEach`.
- Cursores aninhados (`cursor2`, `cursor3`) em loop.
- `len(user.tasks)` ou acesso a relacionamento lazy dentro de loop de listagem.
- Uma `count()` por status/prioridade em vez de `GROUP BY`.

**Por que importa:** 1 + N (ou 1 + N × M) idas ao banco; degrada com o volume.

### AP-14 — Callback hell
**Sinais de detecção**
- 3+ níveis de callbacks aninhados (`db.get(..., (err, x) => { db.run(..., () => { ... }) })`).
- Contadores manuais para saber quando callbacks terminaram (`pending--; if (pending === 0)`).
- `self = this` para escapar de `function` dentro de callback.

**Por que importa:** fluxo difícil de ler, erros engolidos, respostas enviadas duas vezes ou nunca.

### AP-15 — Validação ausente, inconsistente ou duplicada
**Sinais de detecção**
- Mesmo bloco de validação repetido em create e update.
- Campos numéricos sem checagem de tipo (`priority < 1` quebra se vier string).
- Endpoint de update sem validação nenhuma ou com regras diferentes do create.
- Listas de valores válidos repetidas em vários arquivos.
- `request.get_json()` usado sem checar `None`.

### AP-16 — Tratamento de erro genérico e não centralizado
**Sinais de detecção**
- `except:` sem tipo, `except Exception as e: return str(e)`.
- `try/except` idêntico em todos os handlers.
- Callbacks que ignoram `err`.
- Ausência de error handler global (`@app.errorhandler`, middleware de erro `(err, req, res, next)`).

### AP-17 — Código duplicado
**Sinais de detecção**
- Mesmo dicionário de serialização copiado em várias funções.
- Mesma regra de domínio (ex.: "está atrasado?") reimplementada em vários handlers.
- Funções quase idênticas que diferem por um filtro (`get_todos_pedidos` vs `get_pedidos_usuario`).

### AP-18 — Uso de APIs deprecated
Compare com a versão declarada no manifesto. Informe a alternativa moderna no finding.

| Stack | API deprecated | Substituto moderno |
|---|---|---|
| Python 3.12+ | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` |
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)` (Query.get legado) | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `Model.query.filter_by(...).all()` em código novo | `db.session.execute(db.select(Model).filter_by(...)).scalars()` |
| Flask 2.3+ | `@app.before_first_request`, `flask.json.JSONEncoder`, `app.json_encoder` | lógica no app factory, `app.json` provider |
| Python | `pkg_resources`, `distutils`, `imp` | `importlib.metadata`, `setuptools`, `importlib` |
| Node.js | `new Buffer(x)` | `Buffer.from(x)` |
| Node.js | `url.parse()` | `new URL()` |
| Node.js | `crypto.createCipher()` | `crypto.createCipheriv()` |
| Node.js | `fs.exists()` | `fs.existsSync()` / `fs.promises.access()` |
| Express 4 → 5 | `body-parser` separado, `req.param()`, `res.send(status)`, `res.json(status, body)` | `express.json()`, `req.params`/`req.query`, `res.status(x).send()` |
| Segurança | MD5/SHA1 para senha | `werkzeug.security`, `bcrypt`, `crypto.scrypt` (ver AP-05) |

### AP-19 — Exclusão sem integridade referencial
**Sinais de detecção**
- `DELETE` de entidade pai sem tratar filhos (matrículas, pagamentos, tasks) e sem `ON DELETE CASCADE`/`FOREIGN KEY`.
- Mensagens admitindo dados sujos.
- Loop deletando filhos manualmente sem transação.

---

## LOW

### AP-20 — Magic numbers e strings
- Literais com significado de negócio: faixas de desconto (`10000`, `0.1`), limites (`len(nome) > 200`), status (`'pendente'`, `'PAID'`), prioridades (`1..5`), regra de cartão (`startsWith("4")`).

### AP-21 — Nomenclatura ruim
- Variáveis de uma letra fora de loops curtos (`u`, `e`, `p`, `cc`, `cid`).
- Campos de API abreviados (`usr`, `eml`, `pwd`) — quando fazem parte do contrato público, mantenha na borda HTTP e use nomes claros internamente.
- Nomes que não descrevem o comportamento (`badCrypto`, `logAndCache`, `AppManager`, `process_task_data`).

### AP-22 — Imports não usados e código morto
- `import os, sys, json` sem uso; constantes declaradas e nunca usadas; funções utilitárias nunca chamadas.

### AP-23 — `print`/`console.log` como log e efeitos simulados
- `print("ENVIANDO EMAIL...")` no lugar de um serviço de notificação; `print` de erros em vez de `logging`.

### AP-24 — Condicionais verbosas
- `if cond: return True else: return False`; `if` aninhados que podem virar uma expressão booleana.
