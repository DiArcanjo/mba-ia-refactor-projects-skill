================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   13 analyzed | ~1060 lines of code
Date:    2026-10-14

## Summary
CRITICAL: 3 | HIGH: 5 | MEDIUM: 7 | LOW: 5 | Total: 20

## Findings

### #1 [CRITICAL] Credenciais e segredos hardcoded (AP-01)
File: app.py:13; services/notification_service.py:9-10
Evidence: `app.config['SECRET_KEY'] = 'super-secret-key-123'` / `self.email_password = 'senha123'`
Description: A `SECRET_KEY` da aplicação e as credenciais SMTP (usuário e senha) estão escritas no código. A URI do banco também está fixa em `app.py:11`.
Impact: Quem tem acesso ao repositório tem as credenciais, e trocá-las exige novo deploy. Não há como ter valores por ambiente.
Recommendation: Mover para um módulo de config lido de variáveis de ambiente, com `.env.example` (PB-01).

### #2 [CRITICAL] Armazenamento inseguro de senha (AP-05)
File: models/user.py:3, 27-32
Evidence: `self.password = hashlib.md5(pwd.encode()).hexdigest()`
Description: As senhas são salvas e verificadas com MD5 sem salt.
Impact: Um vazamento do banco permite reverter as senhas em segundos com rainbow tables.
Recommendation: Usar `werkzeug.security.generate_password_hash` e `check_password_hash` (PB-05). Os hashes MD5 já existentes deixam de validar, então é preciso rodar o seed de novo.

### #3 [CRITICAL] Exposição de dados sensíveis em respostas (AP-06)
File: models/user.py:21 (usado em routes/user_routes.py:33, 85, 129, 209)
Evidence: `'password': self.password,`
Description: `User.to_dict()` devolve o hash da senha. Ele sai em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
Impact: Vaza o hash MD5, que é trivial de reverter. Viola a LGPD.
Recommendation: Remover o campo `password` da serialização (PB-06).

### #4 [HIGH] Regra de negócio na rota (Fat Controller) (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299; routes/user_routes.py:42-90, 92-132, 153-183; routes/report_routes.py:12-101, 103-155
Evidence: `if t.due_date < datetime.utcnow(): if t.status != 'done' and t.status != 'cancelled':`
Description: Os handlers fazem validação, cálculo de atraso e de estatísticas, resolução de relacionamentos e montagem da resposta. Alguns passam de 60 linhas, como `summary_report` e `update_task`. Os blueprints de `/categories` ficam em `report_routes.py`.
Impact: A regra não é reaproveitável nem testável sem HTTP. Rotas de domínios diferentes ficam misturadas.
Recommendation: Criar `controllers/` e `services/` por domínio, deixando as rotas finas (PB-07).

### #5 [HIGH] Estado global mutável (AP-08)
File: services/notification_service.py:6, 31-36
Evidence: `self.notifications = []`
Description: O serviço guarda as notificações em uma lista em memória na instância. Ela se perde a cada restart e vaza entre requisições se for usada como singleton. Hoje o serviço nem é importado.
Impact: Estado perdido ou compartilhado sem controle quando for usado.
Recommendation: Persistir as notificações ou removê-las, e instanciar o serviço por injeção (PB-08).

### #6 [HIGH] Acoplamento forte sem injeção de dependência (AP-09)
File: routes/*.py (uso direto de `Task.query`, `User.query` e `db.session` nos handlers); services/notification_service.py:12-25
Evidence: `server = smtplib.SMTP(self.email_host, self.email_port)`
Description: Os handlers acessam o ORM diretamente. O serviço de e-mail abre a conexão SMTP dentro do método, com host e credenciais fixos.
Impact: Não dá para trocar por fakes nos testes nem mudar a persistência sem editar todas as rotas.
Recommendation: Isolar o acesso a dados em repositórios/services e injetar a config do SMTP (PB-08).

### #7 [HIGH] Autenticação falsa / token simulado (AP-11)
File: routes/user_routes.py:207-211
Evidence: `'token': 'fake-jwt-token-' + str(user.id)`
Description: O login devolve um token fixo derivado do id, sem assinatura nem expiração. Nenhuma rota o valida.
Impact: Qualquer pessoa forja o token de qualquer usuário.
Recommendation: Emitir um token assinado com expiração, mantendo o campo `token` na resposta (PB-10).

### #8 [HIGH] Debug e bind aberto fixos no código (AP-12)
File: app.py:34
Evidence: `app.run(debug=True, host='0.0.0.0', port=5000)`
Description: O modo debug, o host e a porta estão fixos no código.
Impact: O debugger do Werkzeug permite execução remota de código e fica exposto na rede.
Recommendation: Ler `DEBUG`, `HOST` e `PORT` do ambiente, com defaults seguros (PB-01).

### #9 [MEDIUM] Escritas em múltiplas etapas sem transação (AP-10)
File: routes/user_routes.py:140-151
Evidence: `for t in tasks: db.session.delete(t)` seguido de `db.session.delete(user)`
Description: A exclusão do usuário apaga as tasks uma a uma e só então o usuário, com um único commit e rollback no except. O `except:` genérico esconde a causa da falha.
Impact: O rollback cobre só a sessão atual. Os erros ficam sem diagnóstico.
Recommendation: Encapsular a operação em um service com transação explícita e erros tipados (PB-09).

### #10 [MEDIUM] Queries N+1 (AP-13)
File: routes/task_routes.py:41-57; routes/user_routes.py:22; routes/report_routes.py:19-28, 55-56, 163
Evidence: `user = User.query.get(t.user_id)` dentro do `for t in tasks`
Description: `GET /tasks` faz 2 consultas por task. `GET /users` acessa `len(u.tasks)` por usuário, `GET /categories` faz um `count` por categoria e o resumo faz um `count` por status e por prioridade e uma query por usuário.
Impact: O número de consultas cresce linearmente com o volume de dados.
Recommendation: Usar `joinedload`/`GROUP BY` e agregações únicas (PB-11).

### #11 [MEDIUM] Validação ausente, inconsistente ou duplicada (AP-15)
File: routes/task_routes.py:96-114, 166-184, 261, 264; routes/user_routes.py:61-72, 106-125; routes/report_routes.py:169-181, 196-202; utils/helpers.py:57-108
Evidence: `if priority < 1 or priority > 5:` / `tasks.filter(Task.priority == int(priority))`
Description: Create e update repetem as validações com listas de status e roles duplicadas. Prioridade como string gera 500 e `int()` na busca quebra com valor inválido. Categorias e `PUT /categories` não validam o JSON nem a cor (`get_json()` pode ser `None`). `utils/helpers.py` tem validadores que ninguém usa.
Impact: Entradas inválidas geram 500 e as regras divergem entre as rotas.
Recommendation: Centralizar a validação em um módulo único, com checagem de tipo e de `None` (PB-13).

### #12 [MEDIUM] Tratamento de erro genérico e não centralizado (AP-16)
File: routes/task_routes.py:62, 204, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46-49
Evidence: `except:` / `return jsonify({'error': 'Erro interno'}), 500`
Description: Há `except:` sem tipo nas rotas e nenhum `errorhandler` global. Cada handler repete seu próprio try/except.
Impact: Falhas reais ficam mascaradas, sem log, e os formatos de erro variam.
Recommendation: Criar erros de domínio e um handler global (PB-14).

### #13 [MEDIUM] Código duplicado (AP-17)
File: routes/task_routes.py:17-39, 71-80, 283-287; routes/user_routes.py:162-180; routes/report_routes.py:33-43, 119-135; models/task.py:23-36, 50-60
Evidence: `if t.status != 'done' and t.status != 'cancelled':`
Description: A regra "está atrasado?" e a serialização de task estão copiadas em ao menos 6 lugares, mesmo com `Task.is_overdue()` e `Task.to_dict()` já existindo.
Impact: Qualquer mudança de regra precisa ser replicada em vários lugares, e os resultados podem divergir.
Recommendation: Reaproveitar `Task.is_overdue()` e `to_dict()` e criar um serializer único (PB-15).

### #14 [MEDIUM] Uso de APIs deprecated (AP-18)
File: veja a seção Deprecated APIs
Evidence: `Task.query.get(task_id)` / `datetime.utcnow()`
Description: `Query.get` é legado no SQLAlchemy 2.x, e `datetime.utcnow()` é deprecated desde o Python 3.12 (o venv usa 3.13).
Impact: Gera DeprecationWarning hoje e vai quebrar em versões futuras. Também produz datetimes sem fuso.
Recommendation: Usar `db.session.get()` e `datetime.now(timezone.utc)` (PB-16).

### #15 [MEDIUM] Exclusão sem integridade referencial (AP-19)
File: routes/category_routes.py não existe; routes/report_routes.py:211-223; models/task.py:13-14
Evidence: `db.session.delete(cat)`
Description: Apagar uma categoria não trata as tasks vinculadas, pois a FK `category_id` não tem `ondelete`. Ao apagar um usuário, as tasks dele são apagadas à mão, sem cascade no relacionamento.
Impact: Gera tasks órfãs com `category_id` inexistente ou erro de integridade, conforme o banco.
Recommendation: Definir `ondelete`/`cascade` nos models ou anular a FK no service (PB-09).

### #16 [LOW] Magic numbers e strings soltas (AP-20)
File: routes/task_routes.py:96-114, 177, 182; routes/user_routes.py:64, 71, 115, 120; routes/report_routes.py:180; utils/helpers.py:110-116
Evidence: `['pending', 'in_progress', 'done', 'cancelled']`
Description: Status, roles, limites de título, prioridade e senha estão como literais repetidos. As constantes de `helpers.py` existem, mas ninguém as usa.
Impact: A mudança de uma regra exige alterar vários arquivos.
Recommendation: Centralizar em constantes de domínio (PB-17).

### #17 [LOW] Nomenclatura ruim (AP-21)
File: routes/task_routes.py:16-17; routes/user_routes.py:14, 37, 161; routes/report_routes.py:33, 55, 161, 190; utils/helpers.py:57; models/user.py:27
Evidence: `for t in tasks:` / `def process_task_data(data, existing_task=None)` / `def set_password(self, pwd)`
Description: Há variáveis de uma letra (`t`, `u`, `p1`..`p5`, `cat`) e funções que não descrevem o que fazem, como `process_task_data`.
Impact: Leitura mais difícil.
Recommendation: Renomear para nomes descritivos (PB-17).

### #18 [LOW] Imports não usados e código morto (AP-22)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:6, 8; models/task.py:3; utils/helpers.py:1-7, 9-41, 57-116; services/notification_service.py:38-48; models/user.py:34-38; requirements.txt:4-6
Evidence: `import os, sys, json, datetime` / `import hashlib, json, re`
Description: Há imports sem uso, funções nunca chamadas (`validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `process_task_data`), métodos mortos (`validate_status`, `validate_priority`, `is_admin`) e dependências não usadas (marshmallow, requests, python-dotenv).
Impact: Ruído no código e dependências desnecessárias.
Recommendation: Remover o código morto e os imports (PB-18).

### #19 [LOW] `print` como log (AP-23)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41
Evidence: `print(f"Task criada: {task.id} - {task.title}")`
Description: Eventos e erros são registrados com `print`, em vez de `logging`.
Impact: Não há níveis nem formato de log, e não dá para configurar a saída.
Recommendation: Usar `logging` (PB-18).

### #20 [LOW] Condicionais verbosas (AP-24)
File: routes/task_routes.py:30-39, 71-80; routes/user_routes.py:171-180; models/task.py:38-60; models/user.py:34-38
Evidence: `if self.role == 'admin': return True else: return False`
Description: Há `if/else` aninhados que devolvem booleanos e podem virar uma expressão.
Impact: Mais ruído e mais risco de erro.
Recommendation: Simplificar para expressões booleanas (PB-18).

## Deprecated APIs
| API | File | Modern replacement |
|---|---|---|
| `Model.query.get(id)` | routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `db.session.get(Model, id)` |
| `datetime.utcnow()` | routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; models/*.py (defaults de `created_at`/`updated_at`); services/notification_service.py:35; seed.py | `datetime.now(timezone.utc)` |

## Architecture Notes
Camadas parciais. Existem `models/`, `routes/`, `services/` e `utils/`, mas as rotas fazem tudo e os módulos de apoio estão sem uso. Os blueprints de categorias estão dentro de `report_routes.py`. A Fase 3 vai criar `config/`, `controllers/`, `services/` por domínio e `middlewares/` com tratamento de erro e autenticação. Também vai separar as rotas de categorias e limpar `utils/`.

Faltam autenticação nas rotas de CRUD e nos relatórios. Pelas regras da skill elas ficam abertas, mas a recomendação está registrada aqui.

================================
Total: 20 findings
================================
