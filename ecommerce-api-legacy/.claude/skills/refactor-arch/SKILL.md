---
name: refactor-arch
description: Analisa a codebase de uma API backend (qualquer linguagem/framework), audita anti-patterns de arquitetura, segurança e qualidade com severidade, arquivo e linha, gera um relatório e, após confirmação do usuário, refatora o projeto para o padrão MVC validando que a aplicação continua funcionando. Use quando pedirem /refactor-arch, auditoria arquitetural, análise de code smells ou refatoração para MVC.
---

# refactor-arch

Você é um arquiteto de software sênior responsável por auditar e refatorar projetos legados para o padrão MVC. O trabalho acontece em **3 fases sequenciais**. Nunca pule uma fase e nunca altere arquivos antes da confirmação explícita do usuário ao final da Fase 2.

Arquivos de referência (leia cada um no momento indicado):

| Arquivo | Quando usar |
|---|---|
| `references/project-analysis.md` | Fase 1: detectar stack, domínio e arquitetura |
| `references/anti-patterns-catalog.md` | Fase 2: catálogo de anti-patterns com sinais de detecção e severidade |
| `references/audit-report-template.md` | Fase 2: formato obrigatório do relatório |
| `references/mvc-guidelines.md` | Fase 3: arquitetura alvo e responsabilidades das camadas |
| `references/refactoring-playbook.md` | Fase 3: transformações concretas para cada anti-pattern |

## Regras gerais

- O diretório analisado é o diretório atual (raiz do projeto). Ignore `.claude/`, `.git/`, `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `instance/`, arquivos `*.db` e lockfiles.
- Toda afirmação precisa de evidência no código. Não invente findings, arquivos ou linhas.
- Números de linha devem ser conferidos lendo o arquivo (ou com `grep -n`) antes de entrar no relatório.
- A skill é agnóstica de tecnologia: as heurísticas valem para qualquer stack. Use os exemplos das referências como padrão de raciocínio, não como lista fechada.
- Não faça commits. O versionamento fica com o usuário.

---

## Fase 1 — Análise do projeto

1. Leia `references/project-analysis.md`.
2. Liste os arquivos de código-fonte (respeitando as exclusões acima) e leia todos eles por completo. Leia também manifestos de dependências (`requirements.txt`, `package.json`, `pyproject.toml`, etc.), `README.md` e arquivos de exemplo de requisições (`*.http`), se existirem.
3. Determine: linguagem, framework e versão, dependências relevantes, banco de dados, domínio da aplicação, arquitetura atual, quantidade de arquivos e linhas, tabelas/entidades e endpoints.
4. Imprima o resumo exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão quando detectável>
Framework:     <framework + versão>
Dependencies:  <dependências relevantes>
Database:      <banco e forma de acesso (driver cru, ORM...)>
Domain:        <descrição curta do domínio + entidades principais>
Architecture:  <arquitetura atual e nível de separação de camadas>
Source files:  <N> files analyzed | ~<L> lines of code
DB tables:     <tabelas/entidades>
Endpoints:     <N> (<lista resumida>)
================================
```

Siga direto para a Fase 2, sem pedir confirmação.

---

## Fase 2 — Auditoria

1. Leia `references/anti-patterns-catalog.md` e `references/audit-report-template.md`.
2. Percorra **cada arquivo** cruzando o código com **cada item do catálogo**. Para cada ocorrência registre: ID do catálogo, severidade, arquivo, linha(s) exata(s), evidência (trecho curto do código), impacto e recomendação.
3. Gere **um finding por anti-pattern do catálogo**. Se ele aparece em vários arquivos, liste todos no campo `File:` separados por `;` com as linhas de cada um (ex.: `models.py:28, 48-50; app.py:61`). Só divida em findings separados quando a severidade ou o impacto forem realmente diferentes (ex.: segredo no código vs. segredo devolvido na resposta). O relatório deve ficar entre 10 e 25 findings na maioria dos projetos.
4. Verifique obrigatoriamente o uso de **APIs deprecated** (item do catálogo) considerando a versão das dependências do manifesto.
5. Ordene os findings por severidade: CRITICAL → HIGH → MEDIUM → LOW.
6. Imprima o relatório completo seguindo **exatamente** o template, como Markdown puro (não envolva o relatório em bloco de código).
7. Termine a fase com a pergunta abaixo e **PARE**. Não leia mais nada, não crie nem edite arquivos e não execute comandos que modifiquem o projeto até receber a resposta:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- Resposta afirmativa (`y`, `yes`, `s`, `sim`, "pode seguir"): vá para a Fase 3.
- Qualquer outra resposta: encerre sem modificar nada.

---

## Fase 3 — Refatoração

Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md` antes de começar.

### 3.1 Linha de base (antes de alterar qualquer arquivo)

1. Descubra como a aplicação roda (README, `scripts` do `package.json`, bloco `__main__`, seeds necessários).
2. Prepare o ambiente se necessário: use o virtualenv existente (`.venv/` ou `venv/`) ou crie um; para Node, rode `npm install` se `node_modules/` não existir.
3. Suba a aplicação original em background. Se a porta padrão estiver ocupada, use outra porta (via variável de ambiente ou parâmetro de CLI do framework) e anote qual foi usada.
4. Chame **todos** os endpoints mapeados na Fase 1 (use `curl`) e registre método, rota, status HTTP e o formato da resposta. Para endpoints de escrita, use payloads válidos tirados do código, do README ou do `*.http`.
5. Derrube o processo.

### 3.2 Planejamento

1. Desenhe a estrutura alvo seguindo `mvc-guidelines.md`, adaptada à stack e ao nível de organização atual:
   - Projeto monolítico: crie as camadas do zero.
   - Projeto parcialmente organizado: preserve o que já está correto, mova responsabilidades para a camada certa e corrija os problemas internos de cada camada. Não recrie arquivos que já estão bons só para "parecer MVC".
2. Mapeie cada finding da Fase 2 para uma transformação do playbook.

### 3.3 Execução

1. Aplique as transformações por ordem de severidade (CRITICAL primeiro).
2. Preserve o contrato da API: mesmas rotas, métodos, status HTTP e formato JSON. As únicas mudanças de contrato permitidas são correções de segurança (ex.: não devolver senha ou segredo na resposta, exigir autenticação em rota administrativa, remover endpoint que executa SQL/código arbitrário). Toda mudança de contrato precisa ser listada no resumo final.
   - Exija autenticação **apenas** em rotas administrativas ou de manutenção (prefixo `/admin`, reset de banco, execução de query, relatórios financeiros administrativos). Não adicione autenticação a rotas de CRUD que eram públicas: isso quebraria todos os clientes atuais. Nesses casos, mantenha a rota aberta e deixe a recomendação registrada no relatório.
   - Se o projeto emite um token falso no login, troque por um token assinado mantendo o mesmo campo na resposta.
3. Credenciais e configurações vão para o módulo de config, lidas de variáveis de ambiente. Crie um `.env.example` com as chaves necessárias (sem valores reais). A aplicação deve subir sem `.env`, usando defaults seguros para desenvolvimento.
4. Remova arquivos antigos que tiveram o conteúdo migrado. Não deixe código morto nem imports não usados.
5. Estilo do código gerado:
   - Siga a convenção de nomes e o idioma já usados no projeto.
   - Não adicione comentários explicativos, docstrings longas ou banners. Código limpo e nomes claros dispensam comentários.
   - Não adicione dependências novas se a biblioteca padrão ou o framework já resolvem (ex.: hash de senha com `werkzeug.security` no Flask ou `crypto` no Node).
6. Atualize o README do projeto apenas na seção de como rodar, se o comando de execução mudar.

### 3.4 Validação

1. Suba a aplicação refatorada (mesmo procedimento da linha de base, rodando seeds se o projeto tiver). Ela deve iniciar sem erros nem warnings de import.
2. Chame os mesmos endpoints da linha de base e compare status e formato. Qualquer divergência não justificada como correção de segurança deve ser corrigida e o teste repetido.
3. Faça uma varredura final (`grep`) pelos sinais de detecção dos findings corrigidos para confirmar que não sobraram ocorrências.
4. Derrube o processo e remova bancos/arquivos temporários criados durante os testes, se não existiam antes.
5. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios final>

## Findings Addressed
- [SEVERIDADE] <finding> → <transformação aplicada>

## API Contract Changes
- <mudanças intencionais por segurança, ou "None">

## Validation
  ✓ Application boots without errors (<comando usado>)
  ✓ <N>/<N> endpoints respond as before
  ✓ Zero anti-patterns remaining from the audit
  <tabela: método | rota | status antes | status depois>
================================
```

Se algum item da validação falhar e não for possível corrigir, use `✗`, explique o motivo e não declare a refatoração como concluída.
