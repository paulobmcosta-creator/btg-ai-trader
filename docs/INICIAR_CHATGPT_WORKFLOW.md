# Operar o projeto pelo ChatGPT, GitHub e terminal

Este guia é autossuficiente. Não é necessário recuperar a conversa que originou
o workflow. Versão do coordenador: **0.3.0**.

## Responsabilidades

| Componente | Responsabilidade |
|---|---|
| ChatGPT conectado ao GitHub | Ler o estado publicado, conferir pendências e orientar o próximo comando ou pacote autorizado |
| Terminal local + coordenador Python | Executar o sprint, preservar checkout, checks, logs, orçamento e retomada |
| Antigravity / Sonnet 5.5 Medium | Implementação principal |
| Antigravity / Gemini 4 Argon Medium | Revisão do lote, em outra sessão/modelo |
| Antigravity / Opus 5.5 Medium | Segunda tentativa, com feedback de testes ou revisão |
| Codex / Sol 6.1 | Revisão crítica final ou diagnóstico após duas tentativas sem resolver, somente com opção explícita |

O conector GitHub do ChatGPT não executa comandos no computador do usuário.
O usuário executa o comando proposto no terminal; o workflow realiza as etapas
localmente. Não há API de ChatGPT paga, envio automático de mensagens ao chat
ou dependência do aplicativo Codex para coordenar o trabalho diário.

## Estado e escopo inicial

Repositório: `paulobmcosta-creator/btg-ai-trader`.

- Ferramentas e este guia: branch `automation/antigravity-sprints`.
- Manifesto inicial: `config/agent-sprint-s8-b01.json`.
- ID do lote: `s8-b01-sprint-ag`.
- Commit base: `3c485edc99649d6eafece1357d26ffc4437c7f21`.
- Estado publicado do lote: branch `workflow-status/s8-b01-sprint-ag`.
- Trabalho autorizado: remediar os dois findings P2 existentes do PR #96 sob a
  Issue #95, alterando somente o scanner e seus testes.

O Sprint 8 inteiro ainda tem S8-B02 aberto. O manifesto inicial representa o
recorte S8-B01 autorizado; não concede autorização para implementar S8-B02,
Paper, Live, execução financeira ou integração. O arquivo AGENTS.md do checkout
fixado e seus documentos de programa continuam sendo a referência do estágio.

## Instalação única no Windows

Extraia o pacote 0.3.0 na pasta do coordenador já utilizada. Ele também pode
ser obtido pela branch de ferramentas no GitHub. Mantenha os arquivos antigos
de `C:\Projetos\btg-ai-trader\artifacts\agent-workflow`; são evidência de tarefas
anteriores e não devem ser apagados para instalar esta atualização.

No PowerShell, execute cada linha separadamente. Não depende de scripts `.ps1`:

```powershell
Set-Location -LiteralPath "$env:USERPROFILE\Downloads\btg-agent-workflow"
$env:Path = "$env:LOCALAPPDATA\agy\bin;" + [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:Path"
python .\scripts\agent_workflow.py --version
python -m venv .\.workflow-venv
```

A versão deve ser `0.3.0`. Use Python 3.12. Depois prepare o novo lote e instale
as dependências do próprio candidato em ambiente separado:

```powershell
git -C "C:\Projetos\btg-ai-trader" fetch --no-tags origin refs/heads/s8/01-strategy-remediation
.\.workflow-venv\Scripts\python.exe .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" sprint init .\config\agent-sprint-s8-b01.json
.\.workflow-venv\Scripts\python.exe -m pip install -e "C:\Projetos\btg-ai-trader\artifacts\agent-workflow\s8-b01-sprint-ag\worktree[dev,ml]"
```

Não repita `init` para um lote já criado. Uma falha de instalação precisa ser
resolvida antes de interpretar testes como falhas do código.

## Comando diário

```powershell
.\.workflow-venv\Scripts\python.exe .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" sprint run s8-b01-sprint-ag --sync-github
```

O comando executa os itens em ordem em um único checkout isolado, preservando
os patches anteriores. Faz checks locais e revisão pelo Antigravity. Se os
testes ou a revisão apontarem problemas, envia feedback para uma segunda
tentativa de implementação pelo Opus. Cada item permite até duas tentativas.
Erros de CLI, permissões, escopo ou resposta inválida pausam a execução para
diagnóstico, em vez de provocar trocas cegas de modelo.

Por padrão, o comando diário faz **zero chamadas Codex**. O manifesto inicial
limita o lote inteiro a seis chamadas Antigravity e uma chamada Codex. O limite
inclui reservas de tentativas que falharam; retomar o comando não zera o contador.
É um limite local de chamadas, não uma medição dos créditos/tokens da assinatura.

Na revisão crítica, quando decidir utilizar a cota Codex:

```powershell
.\.workflow-venv\Scripts\python.exe .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" sprint run s8-b01-sprint-ag --allow-codex
```

Essa opção permite a chamada crítica ou o diagnóstico se o Antigravity já
esgotou suas tentativas. Ela não aumenta o orçamento do manifesto. Se a única
chamada for usada para diagnóstico, uma revisão final futura precisará de um
novo pacote explicitamente planejado. Não há aprovação automática por falta
de cota. Uma revisão válida já existente no mesmo snapshot é reaproveitada.

## Ponte terminal → GitHub → ChatGPT

`--sync-github` habilita a publicação automática ao fim dessa execução e das
retomadas seguintes do lote. Requer Git autenticado com permissão de push ao
`origin`. Usa somente Git, sem GitHub CLI, chaves adicionais ou chamadas de modelo.

O coordenador publica uma branch exclusiva `workflow-status/<id>` com:

- `STATE.json`: progresso, hashes, checks, último parecer e chamadas reservadas;
- `MANIFEST.json`: objetivo, autorização, arquivos permitidos, itens e política;
- `chatgpt-handoff.md`: pacote pronto para o novo chat;
- `candidate.patch`: diff histórico até o snapshot local, incluindo arquivos novos permitidos;
- `README.md`: interpretação dos artefatos.

Essa publicação não altera a branch do candidato nem a branch principal, não
faz merge e não fecha gates. Usa atualização normal, sem force-push. Uma branch
de estado existente com conteúdo inesperado não é sobrescrita.

Em caso de falha de rede/autenticação, o progresso local fica preservado e
`github_sync_error` registra a falha. O estado remoto pode estar desatualizado.
Depois de resolver o acesso, publique sem chamar modelos:

```powershell
.\.workflow-venv\Scripts\python.exe .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" sprint sync s8-b01-sprint-ag
```

Para consultar o estado ou gerar o pacote local sem gerar chamadas:

```powershell
.\.workflow-venv\Scripts\python.exe .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" sprint status s8-b01-sprint-ag
.\.workflow-venv\Scripts\python.exe .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" sprint packet s8-b01-sprint-ag
```

O pacote local estará em
`C:\Projetos\btg-ai-trader\artifacts\agent-workflow\s8-b01-sprint-ag\chatgpt-handoff.md`.
Se o conector ChatGPT não conseguir ler a branch indicada, cole esse arquivo no
novo chat. Essa alternativa continua independente da conversa original.

## Abrir um novo chat

Copie o conteúdo de `docs/CHATGPT_PROJECT_PROMPT.md` para um novo chat do ChatGPT
com o repositório conectado. Ele fornece URLs explícitas, regras de coordenação
e comandos, sem depender de memória desta conversa.

O ChatGPT deve conferir a branch e o commit lidos. Não deve tratar busca
indexada da branch principal como estado atualizado do lote. Para um candidato
com patch local, o SHA base não é um novo commit de implementação; o snapshot
e `candidate.patch` identificam o código realmente examinado. CI antiga não
aprova alterações novas.

## Estados e retomada

| Estado | Ação |
|---|---|
| `READY` | Executar o comando diário |
| `AWAITING_CRITICAL_REVIEW` | Antigravity concluiu; coordenar revisão crítica e usar Codex se desejado |
| `NEEDS_ATTENTION` | Ler motivo, checks e último parecer; corrigir a causa ou preparar próximo pacote |
| `STALE` | Arquivos mudaram fora do fluxo; conferir escopo e invalidar evidências antigas |
| `READY_FOR_HUMAN` | Candidato local pronto para avaliação; ainda não é fechamento do sprint |

Se permissões do CLI impedirem implementação, use o `handoff.md` do lote no
aplicativo Antigravity, aberto no checkout isolado indicado. Depois de conferir
as edições, execute `sprint run ... --adopt-edits`. A adoção só aceita alterações
dentro do item atual e exige checks/revisão novos. Não desligue proteções globais.
Uma chamada interrompida sem resultado fica marcada para diagnóstico, sem
reenvio automático. Preserve logs e artefatos.

## Sprints seguintes

Depois de uma aceitação formal, o ChatGPT prepara outro manifesto com novo ID,
SHA completo, autorização vigente, itens ordenados e arquivos permitidos por
item. A ordem é linear; o fluxo para antes de avançar sobre item bloqueado.
Não existe avanço automático para outro sprint sem o pacote correspondente.

Os perfis de checks disponíveis nesta versão são `s8-inventory` e `s8-b01`.
Um sprint com outros componentes exige acrescentar e verificar seu perfil de
engenharia; não basta trocar o número no JSON e reutilizar checks de Strategy.
Gate crítico financeiro não pode ser dispensado para economizar cota.

## Verificação do próprio coordenador

```powershell
python -m unittest discover -s tests -p "test_agent_*.py" -v
```

Os testes usam Git e processos locais de verdade com respostas de modelos
simuladas. Não consomem cotas nem provam acesso real aos modelos. A versão foi
verificada em Linux; o piloto Windows anterior validou o transporte Antigravity
por stdin, preservado nesta versão. O novo ciclo por sprint ainda precisa da
primeira execução real na máquina do usuário.
