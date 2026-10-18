# Resultado do primeiro piloto de semiautomação

Data: 18/10/2026. Execução local em Linux; pacote Windows preparado separadamente.

## Entregue

- Coordenador Python com checkout isolado, locks, hashes de arquivos e índice,
  estado persistido, checks fixos, exportação manual e relatórios estruturados.
- Adaptadores para revisão/inventário com Codex e Antigravity CLI; implementação
  pelo Antigravity somente em tarefas de edição explicitamente delimitadas.
- Lançador PowerShell que localiza o CLI em `%LOCALAPPDATA%\agy\bin\agy.exe`,
  compatível com o caminho informado pelo usuário.
- Pacote de inventário S8-B01 fixado no commit
  `3c485edc99649d6eafece1357d26ffc4437c7f21`.
- Guia de operação e pacote ZIP para transferência ao Windows.

## Verificações executadas

| Verificação | Resultado |
|---|---|
| Suíte local, incluindo testes do coordenador | 20 testes PASS |
| Ruff dos arquivos Python novos | PASS |
| mypy em src, testes e coordenador, com src no caminho de módulos | PASS — 4 arquivos |
| Compilação dos arquivos Python novos | PASS |
| git diff --check | PASS |
| Integridade documental da Fundação no checkout do piloto | PASS |
| Boundary de Strategy no checkout do piloto | PASS |
| Whitespace do diff histórico do piloto | PASS |
| Revisão real por modelo Codex CLI | BLOCKED — rede |
| Execução real do Antigravity CLI | NOT_EXECUTED — instalado apenas no Windows do usuário |
| Execução do lançador PowerShell em Windows | NOT_EXECUTED — ambiente disponível é Linux |

Os testes do coordenador usam repositórios temporários e executores simulados.
Isso valida o controle do fluxo e seus erros; não é evidência de uma revisão
real por modelo nem de autenticação do Antigravity.

A verificação global de Ruff também foi tentada. Ela encontra um problema
preexistente `UP022` em `scripts/check_public_history_secrets.py:98`, fora desta
alteração. Os arquivos novos passam. Não foi alterado esse scanner histórico.

## Bloqueio do piloto real

O Codex CLI 0.159.2 informou login ChatGPT ativo. A primeira chamada excedeu
300 segundos. Uma segunda chamada, com diagnóstico gravado durante a execução,
identificou recusa da política de rede: `HTTP CONNECT 403` ao endpoint de Codex
em `chatgpt.com`. A tentativa foi interrompida, sem tentar contornar a política.

Não foi produzido relatório de revisão válido por um modelo. Os três checks
locais foram executados novamente com sucesso e a tarefa está pronta para a
etapa de modelo na máquina Windows, sujeita ao acesso local.

Os logs locais estão em `artifacts/agent-workflow/s8-b01-inventory/`. Não são
incluídos no ZIP, que contém apenas código, configuração e documentação.

## Próximo acionamento

Extrair o ZIP e executar `scripts/start_agent_workflow.ps1 -Action Doctor` no
Windows. Depois, preparar a tarefa e executar os checks e a análise local pelo
modelo escolhido, conforme [o guia](EXECUTAR_SEMIAUTOMACAO.md).

Nenhum gate foi fechado; não houve alteração do código da estratégia, commit,
push, merge, deploy, coleta de mercado ou operação financeira.

## Retorno do piloto Windows fornecido pelo usuário

Depois da instalação local, os dois CLIs foram encontrados e o Codex informou
autenticação ativa. O usuário executou preparação, checks e os dois modelos.

O relatório real do Sol 6.1 contém evidências de leitura e hashes, com pendências
de CI/revisão do S8-B01 em `findings`. O status declarado foi `REVIEWED`, combinação
que o primeiro coordenador rejeitou. A correção preserva esse relatório e usa
`CHANGES_REQUIRED` como classificação efetiva, sem promover o gate.

O Antigravity retornou `status=SUCCESS`, `response` vazio e `denied_actions`
contendo `RunCommand`. Houve consumo reportado pelo serviço, mas nenhum relatório
de inventário aproveitável. Isso não é um PASS. O inventário foi ajustado para
enviar trechos como entrada e proibir ferramentas; sua execução real corrigida
permanece pendente no Windows.

A atualização foi verificada com 25 testes locais, Ruff dos arquivos novos,
mypy e compilação. O replay evita regenerar o relatório Codex já disponível.

## Versão 0.2.0

O usuário confirmou a instalação do comando `replay`, que reaproveitou a
resposta Codex corretamente. A nova tentativa Antigravity falhou antes de
iniciar o processo com `WinError 206`: o pedido excedia o limite de argumentos
do Windows. Essa é uma falha do coordenador, corrigida enviando os pedidos por
stdin, com transporte JSONL para Antigravity e texto para Codex.

Foram aprovados 28 testes locais e as verificações de lint/tipagem. Os testes
incluem um processo real recebendo entrada UTF-8 grande e verificação de que
os argumentos não contêm o pedido longo. Uma nova chamada real ao Antigravity
no Windows ainda é necessária; não foi declarada aprovação por esses testes.

## Confirmação do piloto 0.2.0 no Windows

O usuário enviou a execução da versão `0.2.0`. A quinta tentativa, pelo
Antigravity/Gemini 3.8 Flash Medium, concluiu sem erro do coordenador e passou
pela aceitação do relatório. O estado final registrado foi `CHANGES_REQUIRED`.

O estado enviado também informa `checks_current=true` e o mesmo hash inicial,
verificado e corrente: `a33483928bce28dee2cf84bbb7892a6789e138a80b5b44e3c605627a858c82d8`.
Isso confirma o funcionamento do transporte e da validação local do inventário
nesse ambiente, com preservação do snapshot e das pendências anteriores.

O conteúdo do novo relatório Antigravity foi fornecido e aceito: é um inventário
com pendências de verificação, sem erro de transporte. A consulta independente
ao GitHub confirmou CI aprovada no commit examinado e uma revisão Codex já
existente, com dois achados P2 ainda abertos. A regressão local passou com
1.391 testes; os 256 testes de Strategy atingiram 100% de cobertura statement
e branch. Os seis exemplos dos dois achados foram reproduzidos estaticamente.

As evidências e a tarefa de remediação delimitada estão em
[S8_B01_VERIFICACAO_2026-10-18.md](S8_B01_VERIFICACAO_2026-10-18.md).
A conclusão deste piloto de ferramentas não fecha S8-B01 nem autoriza Paper.

## Versão 0.3.0: motor Antigravity e coordenação fora desta conversa

O usuário solicitou economia de cota Codex, lotes por sprint e continuação pelo
ChatGPT conectado ao GitHub. Foram implementados execução ordenada em checkout
único, tentativa de correção por outro modelo Antigravity, revisão crítica
Codex opcional e orçamento persistente por lote. A execução padrão não chama
Codex. Os estados e um patch de evidência podem ser publicados em branch
exclusiva, sem atualizar a branch do candidato.

O guia `INICIAR_CHATGPT_WORKFLOW.md` e o prompt `CHATGPT_PROJECT_PROMPT.md`
descrevem instalação, comandos, escopo e recuperação sem depender da conversa
original. A ponte com GitHub usa Git autenticado no terminal; o conector
ChatGPT continua sem controlar o terminal do usuário.

Os testes locais usam repositórios Git e remotos bare temporários, sem modelos
reais. Foram verificados orçamento entre retomadas, proibição de bypass pela
CLI avulsa, diagnóstico sem aprovação, alterações de revisores, escopo por item,
preservação de patches cumulativos e publicação sem staging do candidato.
A CI de tooling inclui Linux e Windows e não chama modelos.
