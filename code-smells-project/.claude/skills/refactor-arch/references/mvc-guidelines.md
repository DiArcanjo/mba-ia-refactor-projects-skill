# Guidelines de Arquitetura — MVC alvo

Arquitetura de referência para a Fase 3. Vale para qualquer stack. Em APIs REST, a **View** é a camada de apresentação HTTP: definição das rotas e serialização das respostas JSON.

## Camadas e responsabilidades

| Camada | Responsabilidade | Pode depender de | Não pode |
|---|---|---|---|
| **Config** | Ler variáveis de ambiente, defaults de desenvolvimento, constantes de negócio | nada | ter segredos reais no código |
| **Database** | Criar conexão/sessão, schema, seed | Config | conter regra de negócio |
| **Models** | Representar entidades e encapsular acesso a dados (queries parametrizadas, ORM) e regras do próprio domínio (ex.: `is_overdue`, cálculo de total) | Database | conhecer HTTP (`request`, `req`, `res`, status code) |
| **Controllers** | Orquestrar o caso de uso: validar entrada, chamar models/services, decidir o resultado, lançar erros de domínio | Models, Services, Validators | montar SQL, formatar JSON de resposta à mão, acessar `request` global fora do handler |
| **Views / Routes** | Mapear método + URL para o controller, extrair dados do request, serializar a resposta e escolher o status HTTP | Controllers | conter regra de negócio ou acesso a banco |
| **Services** (opcional) | Integrações e efeitos colaterais externos: e-mail, gateway de pagamento, notificações | Config | conhecer HTTP |
| **Middlewares** | Tratamento de erro centralizado, autenticação/autorização, logging | Config | conter regra de negócio |
| **Entry point** | Composition root: criar o app, carregar config, registrar rotas e middlewares, injetar dependências | todas | conter lógica além da montagem |

Direção das dependências: `Views → Controllers → Models/Services → Database → Config`. Nunca no sentido contrário.

## Estrutura alvo — Python / Flask

```
<projeto>/
├── app.py                     # entry point: create_app() + app.run lendo config
├── config/
│   └── settings.py            # classe Config lendo os.environ
├── database/
│   ├── connection.py          # get_connection / db = SQLAlchemy()
│   └── seed.py                # dados iniciais (se houver)
├── models/
│   └── <entidade>_model.py    # uma entidade por arquivo
├── controllers/
│   └── <dominio>_controller.py
├── views/
│   ├── <dominio>_routes.py    # Blueprint por domínio
│   └── serializers.py         # to_dict / presenters (opcional)
├── services/                  # opcional
├── middlewares/
│   ├── error_handler.py       # @app.errorhandler centralizado
│   └── auth.py                # decorators de autorização (se necessário)
├── .env.example
└── requirements.txt
```

## Estrutura alvo — Node.js / Express

```
<projeto>/
├── src/
│   ├── app.js                 # entry point: cria o app, injeta dependências, listen
│   ├── config/index.js        # lê process.env
│   ├── database/
│   │   ├── connection.js      # abre o banco e expõe helpers com Promise
│   │   └── schema.js          # CREATE TABLE + seed
│   ├── models/<entidade>Model.js
│   ├── controllers/<dominio>Controller.js
│   ├── routes/                # views: express.Router por domínio
│   ├── services/              # opcional
│   └── middlewares/
│       ├── errorHandler.js    # (err, req, res, next)
│       └── adminAuth.js
├── .env.example
└── package.json
```

## Regras

1. **Um domínio, um conjunto de arquivos.** Produtos, usuários e pedidos não dividem o mesmo model/controller.
2. **Controllers finos, models ricos.** Cálculos de domínio (total do pedido, desconto, atraso) ficam no model ou em um service de domínio; o controller só coordena.
3. **Views sem regra.** A rota extrai parâmetros, chama o controller e devolve o resultado serializado com o status correto.
4. **Erros como exceções de domínio.** Controllers lançam `NotFoundError`, `ValidationError`, `ConflictError`... O middleware de erro converte em status HTTP e JSON padronizado. Nada de `try/except` repetido em cada handler.
5. **Configuração única.** Toda porta, URI de banco, chave, flag de debug e credencial externa vem do módulo de config, que lê variáveis de ambiente. Segredos sem default real: gere um valor aleatório em desenvolvimento ou deixe vazio.
6. **Injeção de dependência simples.** A conexão/sessão do banco e os services são criados no entry point (ou em uma factory) e passados para quem usa. Em Flask, `create_app()` + extensões (`db.init_app`) ou `g`/`current_app` cumprem esse papel. Em Express, passe as dependências no construtor/factory das rotas.
7. **Transações em casos de uso com várias escritas.** O controller/model abre a transação e faz rollback em erro.
8. **Contrato preservado.** Rotas, métodos, status e formato JSON continuam iguais; só mudam por correção de segurança documentada.
9. **Constantes nomeadas.** Status, limites e faixas de negócio viram constantes em config ou no model correspondente.

## Adaptação por nível de organização

| Situação encontrada | O que fazer |
|---|---|
| Monolito (poucos arquivos fazem tudo) | Criar todas as camadas, extrair por domínio, apagar os arquivos antigos |
| Já existe `routes/` funcionando como view | Manter o nome `routes/` (é a camada View), mover a lógica para `controllers/` e deixar as rotas finas |
| Já existem `models/` com ORM | Manter os models, mover regras duplicadas para métodos do model, corrigir serialização sensível e APIs deprecated |
| Existe `services/` com integração | Manter como service, tirar credenciais para config, injetar via factory |
| `utils/` com funções de domínio misturadas | Mover validações para `validators`/controllers, constantes para config, apagar funções sem uso |

## Checklist de conformidade

- [ ] Estrutura de diretórios segue o padrão acima (adaptada à stack)
- [ ] Configuração em módulo próprio, sem segredos hardcoded, com `.env.example`
- [ ] Models abstraem o acesso a dados (sem SQL fora deles)
- [ ] Views/Routes só roteiam e serializam
- [ ] Controllers concentram o fluxo de cada caso de uso
- [ ] Error handling centralizado
- [ ] Entry point claro (composition root)
- [ ] Aplicação sobe e endpoints respondem como antes
