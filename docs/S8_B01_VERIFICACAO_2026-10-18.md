# S8-B01: evidências verificadas e próxima tarefa

Verificação em 18/10/2026, sem alteração do candidato. Commit examinado:
`3c485edc99649d6eafece1357d26ffc4437c7f21`; referência histórica:
`7fce78b02d03cc8140bc021217a0230776cc53ff`.

## Conclusão do piloto Windows

O relatório `review-05.json` enviado pelo usuário confirma o funcionamento do
Antigravity/Gemini 3.8 Flash Medium no inventário. `CHANGES_REQUIRED` é uma
conclusão de análise aceita pelo coordenador, não uma falha de configuração.
Os hashes de entrada e saída são iguais. O inventário informou corretamente que
não consultou CI nem realizou auditoria completa; suas lacunas não significam
que essas atividades nunca ocorreram no GitHub.

## Evidências observadas no GitHub

Todos os runs abaixo apontam para o commit examinado e terminaram em `success`:

| Workflow | Run | Resultado |
|---|---|---|
| Strategy Remediation CI, pull request | [38962176895](https://github.com/paulobmcosta-creator/btg-ai-trader/actions/runs/38962176895) | 16 jobs aprovados |
| Strategy Remediation CI, push | [38962170574](https://github.com/paulobmcosta-creator/btg-ai-trader/actions/runs/38962170574) | success |
| Sprint 8 Entry Gate CI | [38962170644](https://github.com/paulobmcosta-creator/btg-ai-trader/actions/runs/38962170644) | success |
| Pinned upstream engineering verification | [38962170717](https://github.com/paulobmcosta-creator/btg-ai-trader/actions/runs/38962170717) | 2 jobs aprovados |

O [PR #96](https://github.com/paulobmcosta-creator/btg-ai-trader/pull/96) permanece
aberto, sem merge. Existe revisão independente do Codex de 16/10/2026 sobre
esse commit, com dois achados P2 ainda não resolvidos:

1. [Builtins com argumentos não confiáveis](https://github.com/paulobmcosta-creator/btg-ai-trader/pull/96#discussion_r4299052092):
   `len(client)`, `str(client)` e `sorted(client)` são aceitos pelo scanner,
   embora possam chamar métodos do objeto recebido.
2. [Dispatch implícito de operadores](https://github.com/paulobmcosta-creator/btg-ai-trader/pull/96#discussion_r4299052107):
   `client + 1`, `if client` e `f"{client}"` podem chamar métodos como
   `__add__`, `__bool__` e `__format__` e são aceitos pelo scanner.

Esses achados dizem respeito à garantia estática do scanner. Não demonstram
que o runtime Strategy atual esteja executando operações financeiras. CI verde
não elimina esses achados e não fecha o gate.

## Verificação local independente da CI

Ambiente virtual dedicado em Linux, Python 3.12.14, criado com as dependências
do próprio candidato (`pip install -e '<checkout>[dev,ml]'`). Checkout isolado
permaneceu sem alterações rastreadas ou novos arquivos não ignorados.

| Comando, executado na raiz do candidato | Resultado |
|---|---|
| `python -m pytest --cov=btg_ai_trader --cov-branch` | 1.391 testes aprovados; cobertura total arredondada de 97% |
| `python -m pytest tests/strategy --cov=btg_ai_trader.strategy --cov-branch --cov-fail-under=100` | 256 testes aprovados; 394 statements e 122 branches cobertos, 100% |
| `python -m ruff check .` | PASS |
| `python -m mypy src tests scripts` | PASS, 174 arquivos |
| `python -m pip check` | Nenhuma dependência inconsistente |

A suíte integral emitiu um `RuntimeWarning` de `runpy` sobre
`scripts.check_s4_boundary` já estar em `sys.modules`; não houve falha de teste.
Os demais jobs de engenharia são evidência da CI consultada, não foram todos
reexecutados nesta verificação local.

A reprodução estática colocou cada um dos seis exemplos acima em um arquivo
temporário e chamou o scanner do candidato. Todos produziram zero findings,
confirmando os dois achados existentes. Não foram executados métodos de objetos
maliciosos. Evidências locais preservadas em `artifacts/s8-baseline-tests.txt`,
`artifacts/s8-strategy-tests.txt`, nos dois JSONs de cobertura e em
`artifacts/s8-existing-findings-reproduction.json`.

## Próxima tarefa delimitada

O arquivo `config/agent-workflow-s8-dispatch-remediation.json` prepara uma tarefa
nova, sem substituir o inventário. Permite alterações somente em:

- `scripts/check_s8_strategy_boundary.py`;
- `tests/strategy/test_boundary_scanner.py`.

Use Sonnet 5.5 Medium para a implementação inicial. Use um revisor Codex separado
para examinar o diff completo, seus casos adversariais e as evidências. Reserve
Astra/Opus para uma dificuldade concreta de desenho; não é necessário repetir
o inventário com modelos adicionais.

Extraia o ZIP desta tarefa na pasta do coordenador já instalado. No PowerShell,
na pasta `Downloads\btg-agent-workflow`, prepare a tarefa:

```powershell
python .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" prepare .\config\agent-workflow-s8-dispatch-remediation.json
```

Para implementação via CLI:

```powershell
python .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" implement s8-b01-dispatch-remediation --model claude-sonnet-5-5-medium
```

Se o CLI negar ferramentas, preserve o erro e abra no aplicativo Antigravity o
checkout indicado no `handoff.md` da nova tarefa. Envie o conteúdo desse arquivo.
Não é necessário desativar controles globais de permissão.

Depois da edição, use um Python com as dependências `[dev,ml]` instaladas para
executar os checks completos e consultar o estado:

```powershell
python .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" check s8-b01-dispatch-remediation
python .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" status s8-b01-dispatch-remediation
```

A revisão/inventário do coordenador não substitui uma auditoria independente
completa do patch. O fechamento exigirá revisão sem findings bloqueantes e CI
do futuro commit contendo a correção. Este pacote ainda não contém a correção,
não publica alterações e não autoriza merge, S8-B02, Paper ou Live.
