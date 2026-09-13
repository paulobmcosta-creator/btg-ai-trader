# BTG AI Trader — Instruções permanentes

## Propósito e prioridade

Este repositório será a fonte de verdade técnica do BTG AI Trader, um sistema quantitativo intradiário em Python. Segurança operacional, preservação de capital, integridade dos dados, auditabilidade e reprodutibilidade têm precedência sobre velocidade de entrega ou desempenho aparente.

## Estado atual

A fase de Fundação (Sprints 0A a 0F) está formalmente concluída e aprovada. Os contratos 0D-A a 0D-E e os protocolos 0E-A a 0E-G permanecem congelados e auditados, e o Foundation Final Gate (0F-F) foi formalmente aprovado. A abertura do Sprint 1 — Market Observer foi autorizada pela coordenação humana em 2026-08-25, e seu lifecycle está `OPEN` exclusivamente no gate documental pré-código (`CURRENT_GATE = PRE_CODE_RECONCILIATION`). A primeira implementação funcional permanece não autorizada (`S1_A_AUTHORIZED = NO`; `FIRST_FUNCTIONAL_CODE = NOT_YET_AUTHORIZED`) até revisão humana e merge do PR deste gate.

Não há autorização para negociação automática, envio de ordens, execução em produção ou uso de dinheiro real.

## Autoridade normativa e realidade implementada

- Decisões normativas aprovadas são definidas exclusivamente pelos artefatos normativos vigentes do projeto (ADRs, protocolos quantitativos e contratos de entrada).
- Código, testes, configurações e estrutura física representam o estado que está efetivamente implementado no repositório.
- A realidade implementada não pode silenciosamente superseder a autoridade normativa: se implementação e norma divergirem, isso constitui drift/finding a ser reconciliado explicitamente.
- ADRs históricos aprovados não são reescritos silenciosamente; mudanças normativas exigem o mecanismo formal de refinement ou supersession aplicável.
- Restrições de integração física vigentes durante a Fundação foram restrições de estágio e não constituem proibição permanente de integração read-only de market data no Sprint 1.
- Qualquer integração futura de market data no Sprint 1 permanece estritamente subordinada a `SPRINT1_REQUIRED_READ_ONLY_BY_CONSTRUCTION = TRUE` e `SPRINT1_REQUIRED_CAPABILITY_ESCALATION = STRUCTURAL_ESCALATION`.

## Restrições absolutas nesta fase

- Não conectar a corretoras ou plataformas para fins de execução financeira.
- Não transmitir, criar, alterar ou cancelar ordens.
- Não usar nem introduzir chamadas a `order_send()`.
- Não habilitar negociação automática.
- Não operar com dinheiro real.
- Não implementar estratégia de trading nem machine learning operacional.
- Não inserir credenciais, tokens, chaves, senhas, números de conta ou outros segredos.
- Não fazer deploy nem provisionar infraestrutura de produção.

Qualquer mudança futura dessas restrições exige decisão humana explícita, ADR aprovado e satisfação dos gates documentados. Ausência de proibição não equivale a autorização.

## Princípios arquiteturais

- O futuro Risk Engine deve ser independente e ter poder de veto sobre qualquer Signal/Decision Engine.
- `NO_TRADE` deve ser um resultado válido e preferível quando não houver evidência suficiente.
- Pesquisa/treinamento e execução deverão ser isolados; treinamento nunca deve disputar recursos com uma camada crítica de execução.
- Componentes financeiros críticos devem ser determinísticos quando possível, testáveis, observáveis e auditáveis.
- Dados, modelos, configurações e decisões devem ter versionamento e proveniência.
- Alterações arquiteturais relevantes exigem ADR em `docs/adr/`.

## Regras de dados, ML e validação

- Prevenir obrigatoriamente look-ahead bias, data leakage e contaminação entre treino, validação e teste.
- Usar separação temporal e validação fora da amostra antes de promover qualquer modelo.
- Modelar custos, spread, slippage, latência e liquidez em avaliações futuras.
- Backtest não é evidência suficiente de desempenho futuro.
- Exigir replay/backtest verificável e paper trading antes de qualquer discussão de produção.
- Modelos devem possuir versão, dados de origem, métricas, limitações e critérios de promoção/rejeição documentados.

## Gates mínimos para produção futura

Nenhuma execução real pode ser criada até aprovação explícita, no mínimo, de: qualidade dos dados; backtester/replay; ausência de leakage; validação fora da amostra; Risk Engine; paper trading; recuperação/reconciliação; observabilidade; auditoria de segurança e autorização humana final. Os critérios detalhados ainda serão definidos em ADRs e protocolos.

## Práticas de engenharia

- Usar layout `src/`, tipagem, testes automatizados e mudanças pequenas/revisáveis.
- Manter configuração separada de código; apenas exemplos seguros podem ser versionados.
- Falhar de modo seguro: incerteza, dados inválidos ou dependências indisponíveis devem impedir ações financeiras.
- Registrar decisões duráveis no repositório, não apenas em conversas.
- Antes de alterar código, ler este arquivo e a documentação aplicável.
- Não ampliar o escopo de um sprint sem aprovação.

## Definição de pronto

Uma mudança só está pronta quando escopo, testes, documentação, implicações de segurança e pendências estão claros. Para componentes críticos futuros, evidências auditáveis são obrigatórias.
