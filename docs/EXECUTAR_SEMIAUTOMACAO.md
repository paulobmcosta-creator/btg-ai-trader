# Executar o coordenador Codex + Antigravity

**Atualização 0.3.0:** o modo recomendado agora executa lotes por sprint com
Antigravity como motor, Codex opcional nas etapas críticas e estado publicável
no GitHub. Siga [o guia autossuficiente](INICIAR_CHATGPT_WORKFLOW.md) e abra um
novo chat com [o prompt de coordenação](CHATGPT_PROJECT_PROMPT.md). As instruções
abaixo preservam a operação histórica de tarefas avulsas; `review` agora usa
Antigravity por padrão. Para Codex avulso, informe `--provider codex`.

O coordenador está em `scripts/agent_workflow.py`, usa somente a biblioteca
padrão do Python e executa cada tarefa em um checkout Git isolado. Estado,
pacote de tarefa, hashes e logs ficam em `artifacts/agent-workflow/<id>/`.
Nenhum comando de push, merge, deploy ou operação financeira é executado pelo
coordenador. Permissões reais dos agentes continuam sendo configuradas nos CLIs;
verificação de escopo após execução não substitui isolamento do sistema operacional.

## Primeiro piloto no Windows

O usuário informou Antigravity CLI em:

```text
C:\Users\Extensão - Ifes Bsf\AppData\Local\agy\bin\agy.exe
```

O lançador PowerShell usa esse caminho como padrão. Caso o repositório esteja em
outro local, informe `-RepoPath`. O pacote pode ser extraído fora do repositório:
o lançador usa seus próprios scripts/config e opera no repositório indicado.

No PowerShell, a partir da pasta extraída:

```powershell
.\scripts\start_agent_workflow.ps1 -Action Doctor
```

O diagnóstico confere os CLIs, o login do Codex e lista os IDs de modelos do
Antigravity. Se precisar autenticar, abra `agy` interativamente no seu computador
e use o fluxo oficial da conta. Não copie credenciais para este projeto ou chat.
O acesso e a cobrança do CLI devem corresponder à conta escolhida; o coordenador
não adiciona chaves de API nem compra créditos.

Em seguida:

```powershell
.\scripts\start_agent_workflow.ps1 -Action Prepare
.\scripts\start_agent_workflow.ps1 -Action Check
.\scripts\start_agent_workflow.ps1 -Action Review
.\scripts\start_agent_workflow.ps1 -Action Status
```

`Prepare` usa o commit completo fixado em `config/agent-workflow-s8-inventory.json`
e busca a branch existente se o commit ainda não estiver disponível. Não troca
a branch da sua árvore de trabalho principal. Se a tarefa já existir, retome
com `Check`, `Review` ou `Status`; não a prepare novamente.

Para uma análise adicional no Antigravity CLI:

```powershell
.\scripts\start_agent_workflow.ps1 -Action AnalyzeAG -Model gemini-3.8-flash-medium
```

Confirme o ID exato na saída de `Doctor`. Esta análise não é necessária para
duplicar uma revisão já satisfatória; serve para validar o acesso ao segundo CLI.
Os dois comandos de análise são somente leitura por contrato, e os hashes são
conferidos antes/depois. No Codex, também é solicitado sandbox `read-only`.

O inventário está fixado em `3c485edc99649d6eafece1357d26ffc4437c7f21` e não permite
edições. Ele executa três checks locais: whitespace do diff histórico, integridade
da Fundação e boundary da estratégia. O resultado não equivale a CI completa,
auditoria integral nem fechamento de S8-B01.

## Usar o aplicativo Antigravity

```powershell
.\scripts\start_agent_workflow.ps1 -Action Handoff
```

Abra o checkout indicado em `handoff.md` no aplicativo, selecione o modelo e
envie o conteúdo do pacote. Após uma tarefa de edição autorizada, rode `Check`
e `Review` sobre esse mesmo checkout. O primeiro inventário permanece sem edição.

## Tarefas de implementação

Uma tarefa nova exige seu próprio JSON, ID, SHA completo, objetivo concreto,
referência da autorização e lista restrita de arquivos permitidos. Use o perfil
`s8-b01` para implementação nessa remediação, que exige regressão, cobertura de
100% da estratégia, lint, tipagem, dependências e boundaries anteriores.

Os checks usam o mesmo Python que iniciou o coordenador. Ative o ambiente de
desenvolvimento adequado ou informe `-PythonPath` antes de executar o perfil
completo. Dependências ausentes produzem falha; nunca são tratadas como PASS.
O coordenador não instala dependências automaticamente.

Depois de preparar a nova tarefa com o comando Python, é possível usar:

```powershell
.\scripts\start_agent_workflow.ps1 -Action Implement -TaskId ID-DA-TAREFA -Model ID-EXATO-DO-SONNET
.\scripts\start_agent_workflow.ps1 -Action Check -TaskId ID-DA-TAREFA
.\scripts\start_agent_workflow.ps1 -Action Review -TaskId ID-DA-TAREFA
```

Os IDs em maiúsculas são marcadores que devem ser substituídos. O CLI do
Antigravity usa as permissões locais existentes e sandbox; permissões negadas
podem exigir ajuste local específico. O programa não desabilita os controles.
São permitidas até duas tentativas de implementação por tarefa; após isso,
o coordenador para para diagnóstico, preservando as alterações.

## Estado e limites desta primeira versão

- Preparação, execução de cada etapa, checks, exportação e revisão estão implementados.
- A escolha de iniciar/corrigir/continuar cada etapa é explícita pelo operador.
- Os modelos não podem fazer commit neste piloto; o HEAD deve permanecer no SHA base.
- Qualquer arquivo alterado depois dos checks invalida a evidência para revisão.
- Arquivos rastreados e novos não ignorados entram no hash; arquivos ignorados
  pelo Git não são evidência de código. Dados/configs ignorados exigiriam uma
  política adicional de proveniência antes de serem usados em tarefas quantitativas.
- `READY_FOR_HUMAN` significa entrega local pronta para avaliação; não abre gates.
- Timeout, falta de CLI, resposta inválida ou checks falhos bloqueiam a tarefa.
- Um lock impede concorrência no mesmo pacote. Após queda abrupta, confira se
  o processo terminou antes de remover manualmente um diretório `.lock` abandonado.
- O script PowerShell foi preparado para Windows; a validação neste ambiente é Linux.
- A execução real do Antigravity depende do login, modelo, cota e permissões no Windows.

## Testar o coordenador

Sem instalar dependências:

```powershell
python -m unittest discover -s tests -p test_agent_workflow.py -v
```

Os testes usam repositórios temporários e executores simulados, sem consumir
cotas dos modelos. Cobrem isolamento, escopo, evidência desatualizada, relatório
inválido, saída zero sem relatório, falhas, timeout e concorrência.

## Atualização após o primeiro piloto Windows

O piloto do usuário confirmou checks locais e uma resposta real do Sol 6.1.
O relatório traz `REVIEWED` com pendências em `findings`: a versão corrigida
classifica isso conservadoramente como `CHANGES_REQUIRED`, preservando o texto
original e registrando a classificação em `review-NN.assessment.json`.

Uma resposta otimista posterior de outro modelo não apaga pendências registradas
para o mesmo snapshot. Resolver as pendências ou sua adjudicação continua sendo
uma tarefa explícita. A ausência de evidência segue impedindo aprovação.

O Antigravity retornou `SUCCESS`, resposta vazia e `denied_actions` para
`RunCommand`. Esse resultado permanece bloqueado. A versão atual do inventário
envia trechos delimitados e numerados dos arquivos no próprio pedido e proíbe
uso de ferramentas nessa análise. Não é necessário liberar comandos globalmente.
O retorno ainda precisa ser validado por execução real no Windows.

Após substituir os scripts pela versão atualizada, reaproveite a resposta do
Codex sem nova chamada ao modelo:

```powershell
python .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" replay s8-b01-inventory --attempt 1 --provider codex --model gpt-6.1-sol
```

O replay é restrito ao inventário sem edição, exige checks atuais, snapshot
inalterado e evidência `turn.completed` no log Codex. Depois, tente novamente
somente o Antigravity:

```powershell
python .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" review s8-b01-inventory --provider antigravity --model gemini-3.8-flash-medium
python .\scripts\agent_workflow.py --repo "C:\Projetos\btg-ai-trader" status s8-b01-inventory
```

Não execute `prepare` novamente nem apague a pasta da tarefa. Para consultar
relatórios no Windows PowerShell 5, use `Get-Content -Encoding UTF8` e execute
cada comando separadamente para preservar os acentos e evitar junção de parâmetros.

## Versão 0.2.0 — limite da linha de comando do Windows

O piloto seguinte confirmou o replay do Codex e identificou `WinError 206` ao
iniciar o Antigravity. O pacote de trechos era maior que o limite de argumentos
do Windows; nessa tentativa, o executável nem chegou a iniciar. Não era um
problema de caminho longo da instalação nem de login do Antigravity.

O coordenador agora envia os pedidos dos dois CLIs pela entrada padrão. No
Antigravity, usa o protocolo oficial de eventos JSONL e exige um único evento
final completo. O pedido não aparece mais nos argumentos do processo. Recusas
de permissão e respostas incompletas continuam bloqueando a tarefa.
Referência: [entrada padrão do Antigravity CLI](https://www.antigravity.google/docs/cli/headless/).

Confira a versão, sem chamar modelos:

```powershell
python .\scripts\agent_workflow.py --version
```

O resultado deve ser `0.2.0`. Depois de instalar esta atualização, basta repetir
a revisão Antigravity e consultar o estado. Não precisa refazer preparação,
checks já atuais ou o replay Codex concluído. Os logs existentes são preservados.

Esta versão foi verificada com 28 testes, incluindo processo real recebendo
entrada UTF-8 grande, limite do tamanho dos argumentos e rejeição de eventos
incompletos ou com ações negadas. O CLI Antigravity real continua dependendo
da validação na máquina Windows do usuário.
