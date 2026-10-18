# Plano de conclusão do BTG AI Trader

Data: 18/10/2026. Status: proposta de planejamento, sem abertura de sprint,
alteração normativa, autorização de merge ou autorização operacional.

## 1. Diagnóstico e base de evidência

O projeto já possui uma base de engenharia substancial. A prioridade é concluir
a cadeia integrada, qualificar um candidato e produzir evidência prospectiva.

A branch local `work`, em `c64042c9f1501e94bc35c8eaf0cac119192eed0b`, corresponde
à baseline histórica de `main`. Seu pacote mínimo não representa o avanço total.
As refs remotas foram consultadas em 18/10/2026, sem alterar a branch de trabalho.

| Área | Estado encontrado | Consequência para o plano |
|---|---|---|
| Fundação e Sprints 1–7 | Fechamento/PASS registrado no checkpoint remoto | Reutilizar os módulos e respectivas evidências; não reiniciar essas etapas |
| Dados | Provider qualificado no S1: XP/MT5 passivo; captura histórica WINV26/M1 | Revalidar disponibilidade, instrumento vigente, calendário e qualidade antes da campanha futura |
| Risk Engine | Implementação sem efeitos externos aceita no S7 | Integrar preservando veto; isso não comprova prontidão de execução real |
| Entrada do S8 | PR #94 aberto, não integrado; parecer `CHANGES_REQUIRED` | Concluir o fluxo de revisão e integração documental sem declarar Paper autorizado |
| S8-B01: Strategy → TradeIntent → Risk | Implementação candidata em `s8/01-strategy-remediation`; issue #95 aberta | Consolidar revisão e CI no commit final e fechar canonicamente |
| S8-B02: candidato elegível | Ausência de candidato congelado e formalmente `PAPER_ELIGIBLE` registrada | Principal dependência quantitativa antes de implementar Paper |
| S8 funcional e Paper confirmatório | Não autorizados nos artefatos consultados | Planejar sua abertura após os pré-requisitos |
| S9–S12 | Há branches/propostas anteriores, mas esta inspeção não confirmou conclusão canônica | Inventariar reaproveitamento antes de estimar implementação restante |

O checkpoint do S7 registra 1.135 testes aprovados. Esse é um resultado histórico
documentado, não uma execução de testes nesta tarefa. Os relatos de PASS não
substituem uma auditoria atual dos componentes integrados.

Fontes principais, fixadas por commit:

- [Checkpoint canônico após S7](https://github.com/paulobmcosta-creator/btg-ai-trader/blob/1226aea13bc8a99303b8c008883fd36068247829/docs/program/PROGRAM_EXECUTION.md).
- [Checkpoint da remediação S8-B01](https://github.com/paulobmcosta-creator/btg-ai-trader/blob/3c485edc99649d6eafece1357d26ffc4437c7f21/docs/program/PROGRAM_EXECUTION.md).
- [Contrato de entrada S8](https://github.com/paulobmcosta-creator/btg-ai-trader/blob/3c485edc99649d6eafece1357d26ffc4437c7f21/docs/program/S8_ENTRY_CONTRACT.md).
- [Histórico de correções da estratégia](https://github.com/paulobmcosta-creator/btg-ai-trader/blob/3c485edc99649d6eafece1357d26ffc4437c7f21/docs/program/workstreams/S8-STRATEGY-REMEDIATION.md).
- [PR #94](https://github.com/paulobmcosta-creator/btg-ai-trader/pull/94) e [issue #95](https://github.com/paulobmcosta-creator/btg-ai-trader/issues/95), consultados diretamente.
- [Protocolo 0E-G](protocols/quantitative/0E-G-promotion-paper-rejection.md) e [plano mestre](BTG_AI_TRADER_MASTER_PLAN.md).

## 2. O que significa concluir

**Marco A — versão utilizável em Paper:** receber dados contemporâneos, executar
um candidato congelado, aplicar o Risk Engine, simular execução e contabilidade,
exibir o estado e recuperar falhas, com todas as decisões rastreáveis e sem
capacidade de enviar ordens reais.

**Marco B — avaliação concluída:** campanha prospectiva encerrada conforme protocolo,
com `PaperGateAssessment`, comparações com backtest e decisão explícita. Um
resultado inconclusivo ou de rejeição é possível e não deve ser convertido em PASS.

**Marco C — produção mínima controlada, condicional:** cumprir os gates de execução,
reconciliação, risco, segurança e autorização humana. Não é consequência automática
da conclusão do código nem do resultado do Paper.

## 3. Sequência de trabalho e critérios de saída

### Etapa 0 — Consolidar o ponto de partida

- Fixar a branch canônica, commits funcionais e dependências dos PRs empilhados.
- Conferir revisões, CI e pendências atuais, inclusive alterações posteriores aos checkpoints.
- Registrar diferenças entre documentação histórica e estado vivo sem reescrever snapshots.
- Inventariar propostas S9–S12 e identificar código reutilizável, experimental e ausente.
- Definir responsáveis por engenharia, validação quantitativa, revisão e decisão operacional.

Saída: matriz única de entregas, commits, bloqueios, responsáveis e evidências.
Estimativa inicial: 2–3 dias úteis.

### Etapa 1 — Encerrar S8-B01: estratégia integrada ao risco

- Partir da implementação existente; revisar os achados e correções acumulados.
- Verificar causalidade, imutabilidade, identidade do candidato, `NO_TRADE`,
  dados inválidos/atrasados e preservação de proveniência no adaptador de risco.
- Validar o veto do Risk Engine e a ausência de efeitos financeiros externos.
- Executar a CI exigida no commit final, obter revisão independente e encaminhar
  integração conforme a autorização aplicável; validar novamente o resultado integrado.
- Atualizar o checkpoint com fechamento canônico, sem fechar S8-B02 por associação.

Saída: S8-B01 encerrado com evidências ligadas ao commit integrado.
Estimativa: 3–7 dias úteis, revisável se a revisão revelar novos problemas.

### Etapa 2 — Resolver S8-B02: qualificar e congelar um candidato

- Escolher uma hipótese e delimitar instrumento, sessão, horizonte, entradas,
  saídas, sizing, dados, custos e identidade/versionamento.
- Avaliar a estratégia completa com os módulos existentes, separação temporal,
  teste protegido, custos, comparadores, regimes e estresses de execução.
- Preservar histórico de busca e tentativas rejeitadas; não selecionar usando
  o conjunto de teste protegido nem confundir métricas de modelo com resultado de estratégia.
- Produzir um dossiê cobrindo as dez classes de 0E-G: validade metodológica,
  completude, evidência histórica protegida, admissibilidade econômica, risco,
  robustez, comparadores, multiplicidade da busca, identidade e executabilidade Paper.
- Fixar previamente a política de Paper: suficiência de pregões/oportunidades,
  tolerâncias de discrepância e latência, regras de interrupção e critérios de decisão.
- Registrar adjudicação e congelar todos os elementos quantitativamente materiais.

Saída: candidato exato `PAPER_ELIGIBLE` e congelado, ou decisão documentada de
rejeição/mais evidência. A ausência de candidato elegível mantém o S8 bloqueado.
Estimativa: 2–4 semanas para um primeiro ciclo com dados disponíveis; não há prazo
garantido para encontrar uma hipótese elegível.

### Etapa 3 — Sprint 8: implementar e integrar Paper

Após satisfação dos pré-requisitos e autorização funcional:

- Integrar dados admitidos → estratégia → intenção → risco → alocação → plano → execução fictícia.
- Definir e testar reserva atômica de capacidade, expiração, concorrência,
  liberação e prevenção de consumo duplicado de autorização.
- Implementar simulação com inputs contemporâneos e políticas explícitas de
  spread, latência, slippage e limitações de observação.
- Manter caixa, posição e P&L fictícios separados do futuro FinancialLedger canônico.
- Registrar todas as decisões, inclusive `NO_TRADE`, vetos e falhas, em evidência imutável.
- Testar ponta a ponta, duplicação, gaps, quedas de conexão e reinício, além das fronteiras negativas.

Saída: cadeia Paper funcional e reproduzível, sem caminho para ordens reais,
com revisão e regressão aprovadas. Harness sintético não conta como Paper confirmatório.
Estimativa: 2–4 semanas após liberação do gate.

### Etapa 4 — Sprints 9 e 10: operação supervisionada e monitoramento

- Qualificar lifecycle, watchdog, persistência, retomada e reconciliação do estado fictício.
- Exercitar falhas de processo, indisponibilidade de dados, disco e inconsistências de estado.
- Exibir saúde dos dados, atraso, candidato ativo, decisões, vetos, exposição
  fictícia, P&L, alertas e histórico de incidentes.
- Implementar pausa e parada com semântica explícita; não presumir que parada implica zeragem.
- Documentar instalação, início/fim de sessão, recuperação, backup e suporte.
- Comparar ambiente existente com a futura infraestrutura; preservar custo recorrente
  adicional zero enquanto essa restrição vigorar. Qualquer cloud paga depende de decisão própria.

Saída: operador consegue observar, interromper e recuperar a sessão com roteiro testado.
Estimativa: 2–4 semanas. Trabalhos independentes podem se sobrepor ao S8 quando autorizados.
Manter a numeração e os contratos dos sprints; não antecipar capacidade fora do escopo aprovado.

### Etapa 5 — Campanha prospectiva e Sprint 11: auditoria

- Iniciar a campanha somente com candidato congelado, políticas fixadas e autorização aplicável.
- Coletar oportunidades, decisões, vetos, execuções fictícias, falhas e discrepâncias.
- Comparar Paper e backtest nas dimensões materiais, além de P&L.
- Mudança material encerra a partição corrente e inicia nova linhagem de avaliação.
- Auditar integridade temporal, risco, contabilidade fictícia, recuperação,
  observabilidade, segurança e rastreabilidade da versão integrada.
- Reconciliar pendências administrativas, inclusive a proteção de branches e a
  errata histórica apontadas no checkpoint, verificando primeiro seu estado atual.
- Emitir `PaperGateAssessment` e pacote de release com limitações e pendências explícitas.

Saída: Marco B, com parecer fundamentado e nenhum bloqueio escondido.
Esforço de auditoria: 1–2 semanas. A duração da campanha depende da suficiência
informacional fixada na Etapa 2; não deve ser substituída por um prazo arbitrário.

### Etapa 6 — Sprint 12: produção mínima, somente se elegível

- Antes de estimar execução, especificar o trabalho ainda necessário no adaptador
  oficialmente suportado, ciclo de ordens, persistência antes de efeitos externos,
  reconhecimento financeiro, Ledger canônico e reconciliação de resultados desconhecidos.
- Confirmar suporte de integração, ambiente e custos; o provider XP/MT5 de dados
  não comprova disponibilidade nem autorização de execução no BTG.
- Validar execução/recovery em ambientes apropriados conforme autorização própria,
  sem converter evidência de conta fictícia em prova de funcionamento com dinheiro real.
- Satisfazer todas as classes L1–L10 do 0E-G e gates A–G aplicáveis.
- Preparar limites iniciais, supervisão, interrupção e rollback; obter decisão humana final.

Saída: autorização formal de uma versão e configuração específicas, ou decisão de
permanecer em Paper. Prazo não estimável com responsabilidade antes do levantamento
da integração real e dos resultados quantitativos. Este plano não autoriza essa execução.

## 4. Caminho crítico e cronograma de referência

Sequência principal:

```text
Baseline verificada → S8-B01 encerrado → candidato elegível/congelado (S8-B02)
→ gate funcional S8 → Paper integrado → campanha suficiente → auditoria
→ decisão sobre produção → integração/qualificação real, se autorizada
```

Para uma pessoa dedicada à engenharia, com apoio quantitativo e disponibilidade
de revisão, reservar aproximadamente **8–16 semanas de esforço sequencial até a
versão Paper integrada e a auditoria**, usando as faixas acima como ordem de grandeza.
Essa estimativa exclui espera por aprovações, coleta prospectiva e novos ciclos de
pesquisa. Deve ser recalibrada após a Etapa 0 e a primeira revisão de S8-B01.

O tempo até produção não é dedutível dessa estimativa. Evidência insuficiente,
ausência de candidato elegível ou limitações do provedor podem impedir a promoção.

## 5. Primeiros dez dias úteis propostos

1. Dias 1–2: consolidar baseline, PRs, revisões e matriz de pendências.
2. Dias 3–5: concluir verificação e correções de S8-B01; preparar pacote revisável de integração.
3. Dias 6–7: registrar o resultado canônico quando integrado; especificar o ciclo
   de qualificação S8-B02, suas evidências e dependências de dados.
4. Dias 8–10: iniciar o ciclo quantitativo autorizado e fechar o backlog estimado
   de S8/S9/S10, sem iniciar funcionalidades que dependam de gates ainda não aprovados.

Cada entrega deve trazer escopo, responsável, dependências, commit, testes pertinentes,
evidências, decisão de aceite e próximo bloqueio. Engenharia produz a implementação;
validação quantitativa avalia o candidato; revisão independente verifica evidências;
coordenação humana decide as promoções exigidas pelos contratos.

## 6. Controle de escopo

Priorizar uma cadeia completa e um candidato verificável. Expansão de ativos,
modelos adicionais, RL, otimização extensa, dashboard sofisticado e serviços pagos
ficam fora do primeiro marco, salvo necessidade demonstrada e decisão explícita.

Este planejamento foi elaborado por inspeção de documentação, árvores e diferenças
de branches, refs remotas e metadados de PR/issue. Não executou modelos, testes de
runtime, auditoria de segurança, coleta de mercado, merge, deploy ou operação financeira.
