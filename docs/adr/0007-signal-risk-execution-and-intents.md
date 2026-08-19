# ADR 0007 — Fronteira Signal, Risk, Execution e intents

- **Status:** Aceita
- **Data:** 2026-08-18
- **Refinada por:** ADR 0016 — Refinamento da cadeia Strategy, Risk, autorização e Execution

## Contexto

Separar análise, proposta econômica, autorização de risco e efeito externo é requisito de segurança.

## Problema

Definir autoridade e lifecycle sem transformar Risk em executor.

## Alternativas consideradas

- Signal/modelo envia ordem: viola veto independente.
- Risk altera intent e monta ordem: perde autoria e mistura responsabilidades.
- Cadeia explícita de artefatos imutáveis: preserva evidência e controle.

## Decisão

`Signal` é informação analítica sem autoridade financeira. Antes de Risk, uma seleção resolve a família para `TradableInstrument`. `TradeIntent` é proposta econômica imutável e causalmente identificável; tamanho proposto não é autorização. Risk produz `RiskDecision`/autorização (`APPROVE`, `APPROVE_WITH_LIMITS`, `REJECT`) com motivos auditáveis, sem enviar ordem ou alterar silenciosamente o TradeIntent. Order Planning, na fronteira de Execution, transforma autorização válida em `OrderIntent` imutável. Só Execution pode solicitar efeito externo. Autorização de risco expira por tempo, versão de estado ou ambos; sem validade, execução é proibida.

## Invariantes

- Signal, TradeIntent e Risk nunca enviam ordem.
- `OrderIntent` não é ordem enviada nem altera posição.
- Autorização limitada registra diferença entre proposta e limite aprovado.
- `NO_TRADE` e rejeição são resultados válidos.

## Consequências positivas

Mantém veto independente e cadeia econômica auditável.

## Consequências negativas / trade-offs

Há mais artefatos e verificações de validade entre decisão e execução.

## Condições para reabrir a decisão

Somente requisito que preserve veto independente e rastreabilidade, por ADR substitutivo.

## Relação com outros ADRs

Depende de instrumentos (0005), estado de risco (0014), persistência (0009) e recovery (0010).
