# BTG AI Trader — Instruções permanentes

## Propósito e prioridade

Este repositório será a fonte de verdade técnica do BTG AI Trader, um sistema quantitativo intradiário em Python. Segurança operacional, preservação de capital, integridade dos dados, auditabilidade e reprodutibilidade têm precedência sobre velocidade de entrega ou desempenho aparente.

## Estado atual

O projeto está no bootstrap estrutural. Não há autorização para integração com corretora, negociação automática, execução em produção ou uso de dinheiro real.

## Restrições absolutas nesta fase

- Não conectar ao BTG, MetaTrader 5 ou qualquer corretora/plataforma de execução.
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
