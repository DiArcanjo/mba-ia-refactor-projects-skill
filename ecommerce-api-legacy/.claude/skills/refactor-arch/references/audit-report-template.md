# Template do Relatório de Auditoria (Fase 2)

O relatório é impresso no terminal em Markdown puro (sem bloco de código em volta), exatamente nesta estrutura. Ele deve poder ser copiado como está para `reports/audit-project-N.md`. O bloco abaixo só delimita o template neste arquivo.

## Regras

1. Findings ordenados por severidade: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade, ordene pelo ID do catálogo.
2. Numere os findings em sequência (`#1`, `#2`...).
3. `File:` sempre com caminho relativo à raiz do projeto e linhas exatas: `arquivo:linha`, `arquivo:inicio-fim` ou lista `arquivo:12, 48-50, 92`. Quando o anti-pattern aparece em vários arquivos, separe-os com `;` no mesmo finding.
4. `Evidence:` mostra um trecho curto e real do código (1 a 3 linhas), sem reescrever.
5. Cada finding referencia o ID do catálogo (`AP-xx`).
6. O `Summary` precisa bater com a quantidade de findings listados.
7. A seção `Deprecated APIs` é obrigatória. Se não houver nenhuma, escreva `None detected` e cite as versões verificadas.
8. Descrição, impacto e recomendação em português, objetivos (1 a 2 frases cada).

## Template

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem> + <framework versão>
Files:   <N> analyzed | ~<L> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n> | Total: <n>

## Findings

### #1 [CRITICAL] <Nome do anti-pattern> (AP-xx)
File: <arquivo>:<linhas>
Evidence: `<trecho do código>`
Description: <o que está errado neste projeto>
Impact: <consequência concreta>
Recommendation: <transformação recomendada, citando PB-xx>

### #2 [CRITICAL] ...

### #N [LOW] ...

## Deprecated APIs
| API | File | Modern replacement |
|---|---|---|
| <api> | <arquivo:linha> | <substituto> |

## Architecture Notes
<2 a 4 linhas sobre a arquitetura atual e o que a Fase 3 vai mudar estruturalmente>

================================
Total: <n> findings
================================
````

## Exemplo de finding bem escrito

```markdown
### #2 [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 47-50, 57-61, 92, 110
Evidence: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`
Description: Queries montadas por concatenação com valores vindos do request em produtos, usuários e pedidos, inclusive no login.
Impact: `' OR '1'='1` no login autentica sem senha; o termo de busca permite ler qualquer tabela.
Recommendation: Usar queries parametrizadas com placeholders (`?`) em todas as consultas (PB-02).
```

## Exemplo de finding mal escrito (não fazer)

```markdown
### [HIGH] Código ruim
File: models.py
Description: O código tem vários problemas.
```

Problemas: sem ID, sem linha, sem evidência, descrição genérica, severidade sem critério.
