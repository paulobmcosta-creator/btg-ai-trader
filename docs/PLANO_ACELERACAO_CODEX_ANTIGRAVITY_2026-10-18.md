# Aceleração do BTG AI Trader com Codex e Antigravity

> Registro histórico da proposta inicial. A distribuição operacional de modelos
> abaixo foi substituída a pedido do usuário: Antigravity é o motor, ChatGPT
> coordena pelo GitHub e Codex fica reservado às etapas críticas. Para operar,
> siga [o guia 0.3.0](INICIAR_CHATGPT_WORKFLOW.md).

Data: 18/10/2026. Status: proposta operacional de desenvolvimento.
Complementa o [plano de conclusão](PLANO_DE_CONCLUSAO_2026-10-18.md).
Não altera contratos, gates, autorizações ou o escopo dos sprints.

## 1. Recomendação

Usar Codex como coordenador técnico e integrador; Antigravity como segunda
frente de implementação e análise; revisão independente em sessão separada,
preferencialmente com outra família de modelos. Manter no máximo duas frentes
de implementação simultâneas e uma de revisão, com responsáveis distintos por arquivo.

O ganho esperado vem de reduzir espera, retrabalho e conflitos, e de sobrepor
atividades independentes. Não vem de gerar mais candidatos indiscriminadamente,
repetir auditorias idênticas ou antecipar funções bloqueadas pelo contrato.

Meta inicial de planejamento: **5–9 semanas de calendário para engenharia da
versão Paper integrada e preparação da auditoria**, condicionada a dados prontos,
candidato elegível nas primeiras semanas, gates liberados, cotas suficientes e
coordenação diária. É uma hipótese a recalibrar após cinco dias de trabalho,
não uma previsão medida nem promessa de redução proporcional no prazo total.

A coleta prospectiva e o fechamento da auditoria com evidência de Paper vêm
depois, conforme suficiência amostral. Encontrar uma estratégia elegível e chegar
à produção continuam sem prazo garantido.

## 2. Modelos: disponibilidade verificada e escolha proposta

O usuário confirmou ChatGPT Plus com GPT-6.1 Sol, GPT-6 Sol, GPT-6 Astra e
GPT-6 Luna. A disponibilidade desses modelos está confirmada para este plano;
o saldo e os limites efetivos de uso ainda precisam ser observados na execução.
Fonte: [modelos do Work e Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex).

No Antigravity, o usuário confirmou Gemini 4 Argon, Gemini 3.8 Flash,
Claude Opus 5.5, Claude Sonnet 5.5 e GPT-OSS 120B (Medium). Interpretação do
nome digitado “gemini 3.i8, flash”: Gemini 3.8 Flash. O nome do plano Antigravity
não foi informado, mas não é necessário para distribuir esses modelos já acessíveis.
Usar Argon na interface em que o usuário já o vê disponível. A documentação
anuncia retirada do GPT-OSS 120B em 02/11/2026; ele não será dependência do fluxo.
Fonte: [catálogo oficial do Antigravity](https://www.antigravity.google/docs/models/).

As atribuições abaixo são uma proposta para este repositório, não um ranking
comprovado por benchmark. Confirmar com tarefas reais antes de ampliar o uso.

| Papel | Escolha inicial | Alternativa | Aplicação |
|---|---|---|---|
| Coordenação e integração | Codex / GPT-6.1 Sol, médio; alto para contratos críticos | GPT-6 Sol | Dependências, pacotes de trabalho, contratos, reconciliação de branches |
| Implementação cotidiana | Antigravity / Claude Sonnet 5.5 | Codex / GPT-6.1 Sol | Módulos delimitados, adaptadores e testes pertinentes |
| Problemas críticos | Codex / GPT-6 Astra, alto | Antigravity / Claude Opus 5.5 | Causalidade, concorrência, alocação de risco, falhas difíceis |
| Revisão de código escrito no Antigravity | Codex / GPT-6.1 Sol; Astra para bloqueios complexos | Revisor humano | Verificar contratos e reproduzir defeitos no commit exato |
| Revisão de código escrito no Codex | Antigravity / Claude Opus 5.5 | Gemini 4 Argon | Contraprovas e análise independente de invariantes |
| Leitura e síntese de muitos artefatos | Antigravity / Gemini 4 Argon | Sol ou Sonnet | Matriz de evidências, lacunas e dependências; uso sujeito ao teste piloto |
| Tarefas mecânicas | Codex / GPT-6 Luna ou Antigravity / Gemini 3.8 Flash | Modelo padrão já contratado | Índices, relatórios de CI, documentação delimitada, inventários |
| Reserva opcional | Antigravity / GPT-OSS 120B (Medium) | Luna ou Flash | Somente tarefas pequenas, não críticas e verificáveis; fora do caminho principal |

Começar com raciocínio médio na implementação delimitada; elevar para alto
quando houver ambiguidade ou falha persistente. Usar o equivalente disponível
no seletor; nomes de esforço e opções variam entre modelos.

Não trocar de modelo apenas por novidade. Usar Astra/Opus para destravar um
problema concreto, não para cada atualização de documentação. Não depender de
apelidos antigos, como Terra, para selecionar um modelo atual.

## 3. Organização das frentes

| Frente | Responsável sugerido | Trabalho inicial | Dependência/limite |
|---|---|---|---|
| A — Fechamento S8-B01 | Antigravity implementa; Codex revisa | Consolidar achados e correções da estratégia e de seu verificador | Partir da branch de remediação existente; respeitar issue #95 |
| B — Qualificação S8-B02 | Codex conduz método; Antigravity prepara artefatos e executa experimentos autorizados | Inventário de dados, protocolo, matriz de dez classes e candidato versionado | Agora pode produzir planejamento; pesquisa nova depende do mandato aplicável |
| C — Operação e interface | Antigravity, com revisão Codex | Inventariar trabalho S9/S10 e propor contratos de telemetria/recuperação | Inicialmente leitura e especificação; código futuro depende de escopo autorizado |
| D — Integração e evidências | Codex / Sol | Manter commits, CI, pacote de entrega e caminho crítico | Único responsável por integração e checkpoint compartilhado |

As quatro frentes são filas de trabalho, não quatro implementadores simultâneos.
Iniciar com A e uma atividade independente de B, mantendo D como coordenação.
Ativar C quando houver capacidade e autorização. Revisão pode ocorrer enquanto
outro pacote independente avança, sem editar a branch que está sendo revisada.

Os LLMs são ferramentas de engenharia e análise neste plano. Não compõem uma
decisão discricionária de trading em runtime nem substituem modelos quantitativos validados.

## 4. Atacar primeiro o retrabalho de S8-B01

O histórico consultado registra correções de proveniência, frescor dos dados,
aliases e execução implícita via decorators, atributos e subscritos. Isso sugere
uma revisão consolidada por classes de problema, em vez de descobrir apenas
uma variante por rodada. Não prova que os defeitos conhecidos persistam no HEAD.

1. Fixar um commit candidato e inventariar todos os achados conhecidos, com
   repro, correção e teste correspondente.
2. Rever conjuntamente as fronteiras de entrada confiável, reexecução causal,
   identidade do candidato, frescor, veto e limitações do scanner estático.
3. Distinguir controle de alterações de código de isolamento de execução:
   o scanner AST existente é defesa adicional, não um sandbox geral de Python.
4. Entregar um relatório consolidado com achados reproduzíveis, severidade,
   condição de ocorrência e vínculo ao requisito aplicável.
5. Um único implementador corrige o lote; outro revisor verifica as correções,
   os caminhos afetados e novos riscos introduzidos.
6. Encerrar quando os critérios existentes estiverem satisfeitos. Não enfraquecer
   regras nem descartar achados válidos para cumprir um número de rodadas.

Se duas rodadas repetirem a mesma classe de falha, pedir diagnóstico de causa
ao modelo crítico antes de mais remendos. Uma eventual alteração estrutural
deve seguir o ADR e a autorização aplicáveis; não é mudança aprovada por este plano.

## 5. Cronograma acelerado, com dependências explícitas

| Janela proposta | Codex | Antigravity | Marco de saída |
|---|---|---|---|
| Dias 1–2 | Fixar baseline, estado de PRs e critérios; preparar pacotes | Inventariar achados/testes e medir uma tarefa piloto | Escopo e responsáveis definidos; nenhum arquivo com dois donos |
| Dias 3–5 | Revisão consolidada B01; planejar avaliação B02 | Correções B01 e evidências de CI | Pacote B01 pronto para decisão de integração, se aprovado |
| Semanas 2–3 | Método, validação temporal e análise do candidato | Preparação de dados/relatórios e execução reprodutível autorizada | Dossiê B02: elegível, rejeitado ou mais evidência |
| Semanas 3–6, após gate | Contratos, alocação de risco e integração | Execução/contabilidade fictícias e observabilidade em módulos separados | Paper integrado com testes adversos |
| Semanas 5–8, conforme escopo | Continuidade, reconciliação e revisão | Monitoramento, runbooks e verificação de interface | Versão operável e recuperável |
| Semanas 8–9, ou antes se pronto | Auditoria de engenharia e pacote de release | Reprodução independente e correções | Preparação da campanha/auditoria concluída |
| Janela própria | Avaliar suficiência e compatibilidade com backtest | Operação supervisionada e relatórios | PaperGateAssessment após evidência suficiente |

Os intervalos sobrepostos são possibilidades de execução, não autorização para
ignorar a ordem dos gates. Se B02 não passar, o caminho funcional de Paper para;
atividades já autorizadas e independentes podem continuar. Testes e documentação
de engenharia não substituem pregões ou oportunidades de decisão.

## 6. Protocolo de trabalho entre as ferramentas

### Isolamento e integração

- Cada tarefa recebe branch e worktree/checkout exclusivos a partir de um SHA explícito.
- Codex e Antigravity não editam a mesma árvore de trabalho simultaneamente.
- Um dono por arquivo; contratos e utilitários compartilhados passam pelo integrador.
- Evitar dois agentes implementando a mesma solução. Duplicação é útil apenas
  em revisão crítica ou experimento de comparação pequeno e deliberado.
- Revisar um SHA imutável. Mudanças posteriores invalidam a conclusão sobre os
  trechos alterados e exigem as verificações aplicáveis novamente.
- Integrar na ordem das dependências. Preservar autorizações de merge já concedidas;
  quando ausentes e exigidas pelo projeto, apresentar o pacote pronto para decisão.

### Pacote mínimo de cada tarefa

```text
ID / objetivo / responsável / ferramenta / modelo e esforço
Branch base + SHA / branch de trabalho / autorização aplicável
Documentos normativos relevantes / arquivos permitidos e proibidos
Entradas / saídas / contratos / dependências
Critérios de aceite / testes exigidos / efeitos externos permitidos
Orçamento de tempo e uso / condição de escalonamento
Entrega: SHA, diff, comandos, resultados, limitações e pendências
```

Dividir por comportamento verificável: por exemplo, validar expiração de uma
autorização com casos de fronteira, em vez de pedir “implemente todo o sistema”.
Usar pacotes de aproximadamente meio a dois dias, ajustados ao risco.

### Ciclo de revisão

```text
Contrato → implementação + testes locais → CI no SHA candidato
→ revisão independente → correção consolidada → verificação aplicável
→ integração autorizada → CI pós-integração → checkpoint
```

O revisor recebe requisitos, código, testes e evidências; começa sua própria
análise antes de se apoiar na conclusão do implementador. Divergências se
resolvem por reprodução, norma e decisão responsável, não por votação de modelos.

## 7. Custos, cotas e medição

Usar primeiro as assinaturas existentes. Não contratar plano, comprar créditos,
habilitar cobrança de API ou iniciar infraestrutura paga neste planejamento.
O ChatGPT Plus e o acesso aos modelos acima foram confirmados pelo usuário.
Executar dentro das cotas existentes; não há valor monetário adicional presumido.
No Plus, preservar Astra para bloqueios críticos, pois seu uso pode consumir a
franquia mais rapidamente. Não presumir cotas independentes por modelo: conferir
os contadores de cada serviço antes de redistribuir trabalho por esgotamento.

- Perfil econômico: Sol/Luna no Codex e Flash no Antigravity; revisão crítica
  com o modelo forte já incluído na conta. Aceitar menor paralelismo.
- Perfil recomendado para a conta confirmada: Sol 6.1 como integrador, Sonnet como implementador, Astra
  ou Opus por exceção, Flash/Luna para tarefas mecânicas.
- Perfil ampliado: acrescentar Argon para análise transversal e segundo
  revisor apenas em mudanças críticas, se útil no piloto.

Distribuição inicial concreta:

1. Sol 6.1 prepara o pacote B01 e consolida o estado de revisão/CI.
2. Sonnet 5.5 implementa o lote de correções delimitado; Sol 6.1 faz a revisão
   independente, com Astra acionado apenas diante de ambiguidade crítica.
3. Argon inventaria evidências e lacunas de B02 em paralelo, sem editar a estratégia
   nem executar pesquisa ainda não autorizada; Flash organiza a matriz resultante.
4. Luna prepara o resumo factual de testes e pendências a partir dos resultados reais.
5. Opus 5.5 revisa mudanças críticas escritas pelo Codex, quando existirem;
   não duplicar automaticamente toda revisão já concluída.

Esses são papéis alternados conforme a demanda, não seis agentes permanentemente
ativos. Manter duas tarefas ativas e uma revisão como limite inicial.

Em todos os perfis, reduzir contexto repetido: checkpoint curto, contratos
relevantes e links para evidências. Evitar reenviar o repositório inteiro a cada turno.
Começar com duas tarefas ativas; ampliar somente se a fila de revisão não crescer.

Medir por tarefa: tempo até aceite, consumo/quota quando disponível, número
de rodadas, falhas de CI, retrabalho e bloqueios encontrados após revisão.
Não usar linhas geradas, tokens consumidos ou número de agentes como produtividade.

Piloto de cinco dias: uma correção delimitada, um caso de teste de fronteira
e uma síntese de evidências. Comparar adequação, tempo e retrabalho entre modelos
usando os mesmos critérios de aceite. Não generalizar resultados de uma tarefa
de documentação para alterações de risco. Rever a estimativa ao fim do piloto.

## 8. Prompts prontos para distribuição

### Codex — coordenador

> Leia AGENTS.md da branch aplicável, PROGRAM_EXECUTION.md e o pacote da tarefa.
> Confirme branch, SHA, gates e autorização antes de executar. Monte no máximo
> duas tarefas de implementação independentes, com arquivos exclusivos, mais
> uma fila de revisão. Use a remediação existente de S8-B01. Não recrie Sprints
> 1–7, não implemente Paper bloqueado e não confunda esta solicitação de
> planejamento com autorização de merge. Entregue pacotes com critérios de
> aceite, dependências e evidências exigidas. Atualize o checkpoint apenas
> quando autorizado e sustentado por resultados verificáveis.

### Antigravity — implementador

> Execute somente o pacote [ID] na branch [BRANCH], baseada em [SHA], sob a
> autorização [REFERÊNCIA]. Leia as regras e contratos indicados. Edite apenas
> os arquivos permitidos. Preserve invariantes e implemente o comportamento
> especificado com testes pertinentes. Não altere gates para fazer testes
> passarem. Entregue SHA, resumo do diff, comandos e resultados reais, pendências
> e limitações. Não integre nem produza efeitos externos sem autorização aplicável.

### Revisor independente — Codex ou Antigravity

> Revise [SHA] contra [BASE_SHA] e os contratos indicados, sem editar a branch.
> Verifique causalidade, proveniência, dados inválidos/atrasados, veto, limites
> de capacidade e recuperação conforme o escopo. Reproduza cada achado e informe
> arquivo, linha, condição, consequência e requisito violado. Consolide os achados
> por causa. Diferencie defeito bloqueador de sugestão opcional. Informe o que
> foi executado e o que permanece sem evidência. Não declare aprovação financeira.

## 9. Próxima ação concreta

Primeiro pacote: **fechamento técnico de S8-B01**, usando o commit remoto atual
da branch existente, com Antigravity nas correções e Codex na revisão. Em paralelo,
produzir o plano de evidências de S8-B02 e inventariar os dados já disponíveis.

Este documento foi produzido por inspeção do repositório e consulta a catálogos
oficiais. Não foram iniciados agentes externos, tarefas no Antigravity, novos
experimentos quantitativos, implementações, merges ou operações financeiras.

## 10. Semiautomação proposta

### Experiência desejada

O usuário escolhe um pacote já autorizado e inicia a execução. Um coordenador
local prepara a branch, entrega o pacote ao implementador, executa verificações,
encaminha o resultado ao revisor e reúne uma entrega para decisão. O usuário
intervém quando há mudança de escopo, bloqueio não resolvido ou aprovação exigida.

```text
Pacote autorizado + SHA base
→ checkout exclusivo
→ Sonnet implementa no Antigravity
→ testes determinísticos executados pelo coordenador
→ snapshot imutável da alteração
→ Sol 6.1 revisa no Codex
→ correções delimitadas, se necessárias
→ repetição dos checks aplicáveis no resultado final
→ relatório e diff prontos para decisão humana
```

Astra entra apenas em um bloqueio crítico. Para implementação feita pelo Codex,
Opus assume a revisão independente. Autorizações existentes são reutilizadas;
o coordenador não cria nova autoridade por inferência a partir de uma resposta de IA.

### Duas etapas de adoção

1. **Assistida por arquivos:** os aplicativos recebem o mesmo pacote de tarefa,
   em checkouts separados. Scripts locais executam testes e montam o relatório;
   o usuário inicia o implementador e o revisor nas interfaces. É a opção inicial
   se o acesso aos modelos não estiver disponível nos CLIs.
2. **Orquestrada por CLI:** um pequeno programa Python aciona os CLIs, interpreta
   os resultados e persiste o estado da tarefa. Continua dependendo das contas,
   cotas e permissões existentes; não exige adotar uma API paga como arquitetura.

Confirmações técnicas: o ambiente desta conversa tem Codex CLI 0.159.2, cujo
`codex exec` suporta execução não interativa, saída JSONL e schema de resposta.
A documentação do Antigravity descreve `agy -p`, saída estruturada, seleção de
modelo e autenticação previamente estabelecida. O executável `agy` não foi
encontrado neste ambiente; isso não verifica sua instalação no computador do usuário.

Fontes: [Codex não interativo](https://developers.openai.com/codex/noninteractive)
e [Antigravity headless](https://www.antigravity.google/docs/cli/headless/).

Antes de ativar a segunda etapa, verificar os CLIs na máquina escolhida, login,
modelos efetivamente acessíveis e cobrança. Os nomes exibidos no aplicativo
não garantem acesso idêntico no CLI. Não copiar tokens para o repositório.

### Estado persistido e decisões automáticas

Estados propostos: `READY`, `IMPLEMENTING`, `CHECKING`, `REVIEWING`,
`FIXING`, `READY_FOR_HUMAN`, `BLOCKED` e `DONE`.

Cada tarefa registra ID, autorização, SHA base, arquivos permitidos, branch,
modelo efetivo, identificadores das sessões, hash do diff/snapshot, verificações
executadas, achados, rodadas e motivo de parada. O coordenador, não o texto do
modelo, controla as transições.

- Só despachar tarefas com dependências satisfeitas e autorização aplicável.
- Travar a tarefa para impedir dois processos de executá-la ao mesmo tempo.
- O coordenador executa a lista fixa de checks; não executa comandos arbitrários
  extraídos do relatório do modelo.
- Exigir exit codes, artefatos e resultados verificáveis. Uma resposta `PASS`
  ou processo encerrado com código zero não demonstra que todos os checks rodaram.
- Detectar mudanças fora do escopo e preservar o diff para análise, sem promovê-lo.
- Permitir no máximo duas rodadas automáticas de correção por pacote como limite
  inicial. Se persistir um achado, marcar `BLOCKED`; nunca ignorá-lo para encerrar.
- Pausar em cota esgotada, timeout, permissão negada ou alteração de requisito;
  não migrar silenciosamente para cobrança paga ou modelo diferente.
- Vincular a revisão ao snapshot exato e exigir revalidação após alterações.
- Preservar logs e estado para retomada; uma interrupção não deve repetir etapas
  com efeitos externos. Na primeira versão, não incluir push, merge nem deploy.

As permissões de execução devem ser delimitadas no ambiente, além das instruções
do prompt. No modo headless do Antigravity, uma ferramenta pode ser negada sem
falha do processo: verificar também stderr, eventos e presença dos artefatos.

### Primeiro piloto

Usar uma correção pequena e já autorizada de S8-B01, não o sprint inteiro.
Validar primeiro o coordenador com executores simulados: sucesso, falha de teste,
relatório inválido, revisão de snapshot antigo, cota esgotada e interrupção.
Depois realizar um ciclo real, limitado, conferindo modelo, consumo e diff.

Critério de sucesso: o usuário recebe uma entrega reproduzível com alteração,
testes e revisão ligados ao mesmo snapshot, sem copiar repetidamente contexto
entre aplicativos.

Atualização de execução: a primeira versão do coordenador e o lançador Windows
foram implementados em `scripts/agent_workflow.py` e `scripts/start_agent_workflow.ps1`.
O [guia de execução](EXECUTAR_SEMIAUTOMACAO.md) descreve os comandos e limites do MVP.
Os controles de etapa são explícitos pelo operador; o ciclo completo por modelos
ainda depende de validar login, rede, modelos e permissões na máquina Windows.
