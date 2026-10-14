================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-14

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 5 | LOW: 4 | Total: 19

## Findings

### #1 [CRITICAL] Credenciais e segredos hardcoded (AP-01)
File: src/utils.js:2-5
Evidence: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`
Description: O objeto `config` guarda usuário/senha de banco, chave live do gateway de pagamento e usuário SMTP em texto literal no código.
Impact: Quem tem acesso ao repositório tem as credenciais; não há valores por ambiente e a troca exige deploy.
Recommendation: Mover para um módulo de config lido de variáveis de ambiente, com `.env.example` e defaults seguros de desenvolvimento (PB-01).

### #2 [CRITICAL] God Class / God File (AP-03)
File: src/AppManager.js:4-139
Evidence: `class AppManager { constructor() { this.db = new sqlite3.Database(':memory:'); } initDb() {...} setupRoutes(app) {...} }`
Description: Uma única classe genérica cria a conexão, define o schema e os seeds, registra as três rotas, executa SQL e implementa checkout, relatório e exclusão.
Impact: Impossível testar em isolamento; qualquer mudança afeta todos os domínios (viola SRP).
Recommendation: Separar em config, database, models, services, controllers e routes (PB-03).

### #3 [CRITICAL] Endpoint administrativo/destrutivo sem autenticação (AP-04)
File: src/AppManager.js:80, 131
Evidence: `app.get('/api/admin/financial-report', ...)`, `app.delete('/api/users/:id', ...)`
Description: O relatório financeiro e a exclusão de usuários são públicos, sem nenhuma verificação de identidade ou permissão.
Impact: Qualquer cliente lê a receita e os alunos por curso, ou apaga qualquer usuário.
Recommendation: Exigir autenticação/autorização nas duas rotas, por exemplo um middleware com chave administrativa vinda de variável de ambiente (PB-04).

### #4 [CRITICAL] Armazenamento inseguro de senha (AP-05)
File: src/utils.js:17-23; src/AppManager.js:18, 68
Evidence: `hash += Buffer.from(pwd).toString('base64').substring(0, 2);` / `badCrypto(p || "123456")`
Description: A "criptografia" é um loop de base64 truncado em 10 caracteres, que é reversível e colide com facilidade. Quando a senha não vem, é aplicada a senha default "123456". O seed grava a senha em texto puro ('123').
Impact: O vazamento do banco expõe senhas, e usuários criados sem senha ficam com credencial previsível.
Recommendation: Usar `crypto.scrypt` com salt aleatório (biblioteca padrão) e não aplicar senha default (PB-05).

### #5 [CRITICAL] Exposição de dados sensíveis em logs (AP-06)
File: src/AppManager.js:45
Evidence: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`
Description: O número completo do cartão e a chave live do gateway são escritos no log a cada checkout.
Impact: Dado financeiro e segredo ficam em logs (PCI-DSS, LGPD).
Recommendation: Remover o dado sensível do log, no máximo registrar os 4 últimos dígitos mascarados (PB-06).

### #6 [HIGH] Regra de negócio na rota (AP-07)
File: src/AppManager.js:28-78
Evidence: `let status = cc.startsWith("4") ? "PAID" : "DENIED";`
Description: O handler de checkout valida a entrada, decide pagamento, cria usuário, matricula, registra pagamento e auditoria, tudo dentro da definição da rota (~50 linhas). O relatório financeiro (linhas 80-129) também calcula receita no handler.
Impact: A regra de negócio não é reutilizável e só pode ser testada via HTTP.
Recommendation: Extrair para services (checkout, relatório) e deixar controllers finos (PB-07).

### #7 [HIGH] Estado global mutável (AP-08)
File: src/utils.js:9-10, 25
Evidence: `let globalCache = {}; let totalRevenue = 0;`
Description: Cache e receita total são variáveis de módulo exportadas e mutadas (`globalCache[key] = data`). `totalRevenue` é exportada por valor e nunca é atualizada de fato.
Impact: Estado compartilhado entre requisições, sem expiração e com crescimento ilimitado; os testes passam a depender de ordem.
Recommendation: Remover o estado global; o cache só se justifica se for injetado e limitado (PB-08).

### #8 [HIGH] Acoplamento forte sem injeção de dependência (AP-09)
File: src/AppManager.js:7; src/app.js:8-10
Evidence: `this.db = new sqlite3.Database(':memory:');`
Description: A classe cria a própria conexão no construtor e depende diretamente do módulo `utils` global. O `app.js` instancia o manager e chama `initDb`/`setupRoutes` manualmente.
Impact: Não dá para trocar o banco ou substituir por mock nos testes.
Recommendation: Criar a conexão em um módulo de database e injetá-la nos models/services (PB-08).

### #9 [HIGH] Escritas em múltiplas etapas sem transação (AP-10)
File: src/AppManager.js:50-57, 69
Evidence: `INSERT INTO enrollments ...` seguido de `INSERT INTO payments ...` e `INSERT INTO audit_logs ...`
Description: Usuário, matrícula, pagamento e auditoria são gravados em inserts independentes, sem `BEGIN/COMMIT/ROLLBACK`. O erro do insert de auditoria (linha 57) é ignorado.
Impact: Uma falha no meio deixa matrícula sem pagamento ou usuário sem matrícula.
Recommendation: Envolver o fluxo em uma transação com rollback no erro (PB-09).

### #10 [HIGH] Porta fixa no código (AP-12)
File: src/utils.js:6; src/app.js:12
Evidence: `port: 3000`
Description: A porta é um literal e não é lida do ambiente.
Impact: Não dá para configurar a porta por ambiente nem rodar duas instâncias.
Recommendation: Ler `PORT` de variável de ambiente no módulo de config, com default 3000 (PB-01).

### #11 [MEDIUM] Queries N+1 (AP-13)
File: src/AppManager.js:89-124
Evidence: `courses.forEach(c => { this.db.all("SELECT * FROM enrollments WHERE course_id = ?" ...` com `this.db.get(...)` de users e payments dentro de `enrollments.forEach`
Description: O relatório executa uma query de matrículas por curso e duas queries (usuário e pagamento) por matrícula.
Impact: 1 + N + 2M idas ao banco, que degradam com o volume.
Recommendation: Substituir por uma única query com JOIN agrupada em memória (PB-11).

### #12 [MEDIUM] Callback hell (AP-14)
File: src/AppManager.js:26, 37-77, 83-128
Evidence: `enrPending--; if (enrPending === 0) {` / `const self = this;`
Description: Checkout com 6 níveis de callbacks e relatório com 5 níveis, com contadores manuais de pendências e `self = this`.
Impact: Fluxo difícil de ler, e a resposta pode ser enviada duas vezes ou nunca quando um erro é ignorado.
Recommendation: Promisificar o acesso ao banco e usar async/await (PB-12).

### #13 [MEDIUM] Validação ausente ou inconsistente (AP-15)
File: src/AppManager.js:35, 132
Evidence: `if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");`
Description: Só há checagem de presença. Não há validação de formato de e-mail, tipo do `c_id` nem do cartão, e `req.params.id` do DELETE não é validado.
Impact: Entradas malformadas chegam ao banco e geram erros ou dados inconsistentes.
Recommendation: Centralizar a validação dos payloads em uma função/middleware (PB-13).

### #14 [MEDIUM] Tratamento de erro genérico e não centralizado (AP-16)
File: src/AppManager.js:57, 84, 93, 104, 106, 133
Evidence: `this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => { let enrPending = enrollments.length;`
Description: Vários callbacks ignoram `err` (a linha 93 quebra com `TypeError` se a query falhar). As respostas de erro são strings soltas e não há middleware global de erro.
Impact: Falhas derrubam a requisição ou passam silenciosas, com mensagens inconsistentes.
Recommendation: Propagar os erros com async/await e adicionar um middleware de erro `(err, req, res, next)` (PB-14).

### #15 [MEDIUM] Exclusão sem integridade referencial (AP-19)
File: src/AppManager.js:131-136; src/AppManager.js:12-15
Evidence: `res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");`
Description: O DELETE remove o usuário, mas não trata matrículas e pagamentos, e o schema não define chaves estrangeiras. O erro do `run` é ignorado.
Impact: Matrículas e pagamentos órfãos corrompem o relatório financeiro.
Recommendation: Remover os filhos (pagamentos, matrículas) na mesma transação e declarar FOREIGN KEYs (PB-09).

### #16 [LOW] Magic numbers e strings (AP-20)
File: src/AppManager.js:46, 48, 68, 108; src/utils.js:19, 22
Evidence: `cc.startsWith("4") ? "PAID" : "DENIED"` / `for(let i = 0; i < 10000; i++)`
Description: Regra de cartão, status de pagamento, senha default e parâmetros do hash são literais espalhados.
Impact: Difícil entender e alterar as regras de negócio.
Recommendation: Extrair constantes nomeadas (PB-17).

### #17 [LOW] Nomenclatura ruim (AP-21)
File: src/AppManager.js:29-33; src/utils.js:12, 17
Evidence: `let u = req.body.usr; let cc = req.body.card; let cid = req.body.c_id;`
Description: Variáveis de uma letra e abreviadas (`u`, `e`, `p`, `cc`, `cid`) e funções que não descrevem o comportamento (`badCrypto`, `logAndCache`, `AppManager`).
Impact: Leitura prejudicada.
Recommendation: Manter `usr`/`eml`/`pwd`/`c_id` na borda HTTP (contrato) e usar nomes claros internamente (PB-17).

### #18 [LOW] Imports não usados e código morto (AP-22)
File: src/AppManager.js:2; src/utils.js:3-5
Evidence: `const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');`
Description: `totalRevenue` é importado e nunca usado, e `dbUser`, `dbPass` e `smtpUser` do config não são lidos em lugar nenhum.
Impact: Ruído e falsa impressão de funcionalidade.
Recommendation: Remover os imports e as configurações sem uso (PB-18).

### #19 [LOW] console.log no lugar de logger (AP-23)
File: src/AppManager.js:45; src/utils.js:13; src/app.js:13
Evidence: `console.log(\`[LOG] Salvando no cache: ${key}\`);`
Description: Logs ad hoc via `console.log` espalhados, sem nível nem formato.
Impact: Sem controle de verbosidade, e há risco de vazamento (ver #5).
Recommendation: Centralizar o log em um módulo mínimo e remover os logs de depuração (PB-18).

## Deprecated APIs
None detected. Versões verificadas: express ^4.18.2, sqlite3 ^5.1.6. O código usa `express.json()`, `Buffer.from` e `res.status().send()/json()`, sem `new Buffer`, `req.param()` ou `body-parser`.

## Architecture Notes
Arquitetura monolítica: `AppManager.js` concentra banco, rotas, SQL e regra de negócio, e `utils.js` mistura config com segredos, estado global e hash caseiro. A Fase 3 vai separar em config/, database/, models/, services/, controllers/, routes/ e middlewares/. Os fluxos serão migrados para async/await com transação, e o contrato da API será preservado, exceto pelas correções de segurança.

================================
Total: 19 findings
================================
