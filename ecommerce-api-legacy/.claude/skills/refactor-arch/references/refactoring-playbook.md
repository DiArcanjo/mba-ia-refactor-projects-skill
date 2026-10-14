# Playbook de Refatoração

Transformações concretas para a Fase 3. Cada padrão (`PB-xx`) corrige um ou mais anti-patterns do catálogo (`AP-xx`) e traz um exemplo antes/depois. Os exemplos mostram a ideia; adapte nomes, idioma e estilo ao projeto.

| ID | Transformação | Corrige |
|---|---|---|
| PB-01 | Extrair configuração para módulo de config com variáveis de ambiente | AP-01, AP-12 |
| PB-02 | Queries parametrizadas | AP-02 |
| PB-03 | Quebrar God Class em camadas MVC por domínio | AP-03 |
| PB-04 | Proteger ou remover endpoints administrativos perigosos | AP-04 |
| PB-05 | Hash de senha com algoritmo adequado | AP-05 |
| PB-06 | Serialização segura e logs sem dados sensíveis | AP-06 |
| PB-07 | Mover regra de negócio do controller/rota para model/service | AP-07 |
| PB-08 | Substituir estado global por dependências injetadas | AP-08, AP-09 |
| PB-09 | Transações e integridade referencial | AP-10, AP-19 |
| PB-10 | Token assinado no lugar de token falso | AP-11 |
| PB-11 | Eliminar N+1 com JOIN / eager loading / agregação | AP-13 |
| PB-12 | Callbacks para async/await | AP-14 |
| PB-13 | Validação centralizada | AP-15 |
| PB-14 | Error handler centralizado com exceções de domínio | AP-16 |
| PB-15 | Extrair lógica duplicada para o model | AP-17 |
| PB-16 | Substituir APIs deprecated | AP-18 |
| PB-17 | Constantes nomeadas e nomes claros | AP-20, AP-21 |
| PB-18 | Limpeza: imports, prints e condicionais | AP-22, AP-23, AP-24 |

---

## PB-01 — Extrair configuração

**Antes (Python)**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Depois**
```python
# config/settings.py
import os
import secrets


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
```
```python
# app.py
app.config.from_object(Config)
app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
```

**Antes (Node)**
```js
const config = { dbPass: "senha_prod_123", paymentGatewayKey: "pk_live_abc", port: 3000 };
```

**Depois**
```js
// src/config/index.js
module.exports = {
  port: Number(process.env.PORT) || 3000,
  databasePath: process.env.DATABASE_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  adminToken: process.env.ADMIN_TOKEN || '',
};
```
Crie `.env.example` listando as chaves, sem valores reais.

---

## PB-02 — Queries parametrizadas

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```

**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)
```
Os fragmentos fixos podem ser montados dinamicamente; **valores** sempre vão em `params`.

**Node**
```js
// antes
db.run(`DELETE FROM users WHERE id = ${id}`);
// depois
await db.run('DELETE FROM users WHERE id = ?', [id]);
```

---

## PB-03 — Quebrar God Class em camadas

**Antes**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE + seed */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* SQL + pagamento + resposta */ });
  }
}
```

**Depois**
```js
// src/app.js (composition root)
const db = await createDatabase(config.databasePath);
const courseModel = new CourseModel(db);
const checkoutController = new CheckoutController({ db, courseModel, userModel, paymentService });
app.use('/api', checkoutRoutes(checkoutController));
app.use(errorHandler);
```
```js
// src/routes/checkoutRoutes.js
module.exports = (controller) => {
  const router = express.Router();
  router.post('/checkout', (req, res, next) =>
    controller.checkout(req.body).then((result) => res.status(200).json(result)).catch(next));
  return router;
};
```
Regra: um arquivo por responsabilidade e por domínio. Delete o arquivo original depois de migrar tudo.

---

## PB-04 — Endpoints administrativos perigosos

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])
```

**Depois**
- Endpoint que executa SQL/código arbitrário: **remover** e registrar em "API Contract Changes". Não existe versão segura de "execute qualquer SQL".
- Endpoint administrativo legítimo (reset, relatório financeiro, exclusão): manter a rota e exigir autorização via middleware.

```python
# middlewares/auth.py
from functools import wraps
from flask import current_app, request
from middlewares.error_handler import UnauthorizedError


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = current_app.config.get("ADMIN_TOKEN")
        if not token or request.headers.get("X-Admin-Token") != token:
            raise UnauthorizedError("Acesso restrito a administradores")
        return view(*args, **kwargs)
    return wrapper
```
```js
// src/middlewares/adminAuth.js
module.exports = (adminToken) => (req, res, next) => {
  if (!adminToken || req.get('X-Admin-Token') !== adminToken) {
    return res.status(401).json({ error: 'Acesso restrito a administradores' });
  }
  next();
};
```

---

## PB-05 — Hash de senha

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```js
function badCrypto(pwd) { return Buffer.from(pwd).toString('base64').substring(0, 10); }
```

**Depois (Flask — sem dependência nova)**
```python
from werkzeug.security import check_password_hash, generate_password_hash

def set_password(self, password):
    self.password = generate_password_hash(password)

def check_password(self, password):
    return check_password_hash(self.password, password)
```

**Depois (Node — módulo nativo)**
```js
const crypto = require('crypto');

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, hash] = stored.split(':');
  const candidate = crypto.scryptSync(password, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```
Login passa a buscar o usuário pelo e-mail e comparar com `check_password`/`verifyPassword`, nunca com senha no `WHERE`. Atualize seeds para gravar senhas com hash.

---

## PB-06 — Serialização segura e logs limpos

**Antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

**Depois**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "role": self.role}
```
```js
logger.info(`Processando pagamento com cartão final ${card.slice(-4)}`);
```
Health check devolve só status e contagens, nunca `secret_key`, caminho do banco ou flags de debug.

---

## PB-07 — Regra de negócio fora do controller/rota

**Antes**
```python
def relatorio_vendas():
    faturamento = ...
    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
```

**Depois**
```python
# models/pedido_model.py
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0
```
```python
# controllers/relatorio_controller.py
def relatorio_vendas():
    resumo = pedido_model.resumo_vendas()
    desconto = pedido_model.calcular_desconto(resumo["faturamento"])
    return {**resumo, "desconto_aplicavel": round(desconto, 2)}
```
Efeitos colaterais (e-mail, SMS, push) vão para um service chamado pelo controller.

---

## PB-08 — Estado global → dependências injetadas

**Antes**
```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```

**Depois (conexão por request no contexto do Flask)**
```python
# database/connection.py
import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
```

**Antes (Node)**
```js
let globalCache = {};
module.exports = { globalCache };
```

**Depois**
```js
class CheckoutController {
  constructor({ db, cache, paymentService }) {
    this.db = db;
    this.cache = cache;
    this.paymentService = paymentService;
  }
}
```

---

## PB-09 — Transações e integridade referencial

**Antes**
```python
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()
```

**Depois**
```python
try:
    pedido_id = pedido_model.inserir(db, usuario_id, total)
    for item in itens:
        item_model.inserir(db, pedido_id, item)
        produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"])
    db.commit()
except Exception:
    db.rollback()
    raise
```
```js
await db.run('BEGIN');
try {
  const enrollmentId = await enrollmentModel.create(userId, courseId);
  await paymentModel.create(enrollmentId, amount, status);
  await db.run('COMMIT');
} catch (err) {
  await db.run('ROLLBACK');
  throw err;
}
```
Exclusão de entidade pai: remova os filhos na mesma transação ou use `FOREIGN KEY ... ON DELETE CASCADE` (com `PRAGMA foreign_keys = ON` no SQLite).

---

## PB-10 — Token assinado

**Antes**
```python
return {"token": "fake-jwt-token-" + str(user.id)}
```

**Depois (sem dependência nova)**
```python
from itsdangerous import URLSafeTimedSerializer

def gerar_token(user_id):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps({"user_id": user_id})
```
`itsdangerous` já vem com o Flask. Em Node, use `crypto.createHmac` para assinar um payload com expiração.

---

## PB-11 — Eliminar N+1

**Antes**
```python
for pedido in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(pedido["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**Depois (uma query com JOIN e agrupamento em memória)**
```python
rows = db.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    ORDER BY p.id
""").fetchall()
```

**ORM (SQLAlchemy)**
```python
tasks = db.session.execute(
    db.select(Task).options(joinedload(Task.user), joinedload(Task.category))
).scalars().all()

counts = dict(db.session.execute(
    db.select(Task.status, db.func.count()).group_by(Task.status)
).all())
```

---

## PB-12 — Callbacks para async/await

**Antes**
```js
db.get(sql1, [a], (err, course) => {
  db.get(sql2, [b], (err, user) => {
    db.run(sql3, [c], function (err) { res.json({ id: this.lastID }); });
  });
});
```

**Depois**
```js
// src/database/connection.js
const run = (db, sql, params = []) => new Promise((resolve, reject) => {
  db.run(sql, params, function (err) {
    if (err) return reject(err);
    resolve({ lastID: this.lastID, changes: this.changes });
  });
});
const get = (db, sql, params = []) => new Promise((resolve, reject) =>
  db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
const all = (db, sql, params = []) => new Promise((resolve, reject) =>
  db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));
```
```js
async checkout(input) {
  const course = await this.courseModel.findActiveById(input.courseId);
  const user = await this.userModel.findOrCreate(input);
  const { lastID } = await this.enrollmentModel.create(user.id, course.id);
  return { msg: 'Sucesso', enrollment_id: lastID };
}
```

---

## PB-13 — Validação centralizada

**Antes**
```python
# repetido em create e update
if len(title) < 3: return jsonify({'error': 'Título muito curto'}), 400
if status not in ['pending', 'in_progress', 'done', 'cancelled']: ...
```

**Depois**
```python
# controllers/validators.py
from config.settings import TASK_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH
from middlewares.error_handler import ValidationError


def validate_title(title):
    if not title or not MIN_TITLE_LENGTH <= len(title.strip()) <= MAX_TITLE_LENGTH:
        raise ValidationError(f"Título deve ter entre {MIN_TITLE_LENGTH} e {MAX_TITLE_LENGTH} caracteres")
    return title.strip()


def validate_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError("Status inválido")
    return status
```
Create e update usam as mesmas funções. Mantenha as mesmas mensagens de erro se fizerem parte do contrato.

---

## PB-14 — Error handler centralizado

**Antes**
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Depois**
```python
# middlewares/error_handler.py
class AppError(Exception):
    status_code = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"erro": error.message, "sucesso": False}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        app.logger.exception(error)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
```
```js
// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  const status = err.status || 500;
  if (status === 500) console.error(err);
  res.status(status).send(status === 500 ? 'Erro interno' : err.message);
};
```
Use a mesma chave de erro que o projeto já usa (`erro`, `error`) para não quebrar o contrato.

---

## PB-15 — Lógica duplicada no model

**Antes (copiado em 5 handlers)**
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            overdue = True
```

**Depois**
```python
# models/task.py
def is_overdue(self):
    return (
        self.due_date is not None
        and self.due_date < utcnow()
        and self.status not in CLOSED_STATUSES
    )
```
Serialização repetida vira um único `to_dict()`/`serialize_produto(row)` reaproveitado por todas as rotas.

---

## PB-16 — APIs deprecated

**Antes**
```python
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
user = User.query.get(user_id)
```

**Depois**
```python
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utcnow)
user = db.session.get(User, user_id)
```
`replace(tzinfo=None)` mantém compatibilidade com colunas `DateTime` sem timezone já gravadas no SQLite.

```js
// antes
const buf = new Buffer(text);
// depois
const buf = Buffer.from(text);
```

---

## PB-17 — Constantes nomeadas e nomes claros

**Antes**
```js
let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```

**Depois**
```js
const PAYMENT_STATUS = { PAID: 'PAID', DENIED: 'DENIED' };
const APPROVED_CARD_PREFIX = '4';

const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;
const status = card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
```
Os nomes do contrato HTTP (`usr`, `eml`) continuam aceitos na borda; internamente o código usa nomes claros.

---

## PB-18 — Limpeza

**Antes**
```python
import os, sys, json, datetime

def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False

print("ERRO: " + str(e))
```

**Depois**
```python
import logging

logger = logging.getLogger(__name__)


def is_admin(self):
    return self.role == "admin"

logger.exception("Falha ao criar produto")
```
Remova imports, constantes e funções sem uso. Troque `print` por `logging`/`app.logger` (ou um logger simples no Node).
