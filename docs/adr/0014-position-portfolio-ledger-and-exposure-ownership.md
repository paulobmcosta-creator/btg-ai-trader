# ADR 0014 — Ownership de Position, Portfolio, Ledger e exposição

- **Status:** Aceita
- **Data:** 2026-08-18
- **Refinada por:** ADR 0022 — Refinamento de Ledger, projeções financeiras e Exposure

## Contexto

Posição interna, fatos históricos e realidade externa respondem perguntas distintas e não podem competir como fontes autoritativas.

## Problema

Definir autoridade de estado, lifecycle de execução e snapshot consistente para Risk.

## Alternativas consideradas

- Ledger como posição corrente: mistura histórico e projeção.
- Strategy mantendo posição paralela: cria divergência sem autoridade.
- Autoridades separadas com ajustes explícitos: preserva domínio e reconciliação.

## Decisão

Ledger é a autoridade interna dos fatos financeiros/operacionais históricos, conceitualmente append-only. Position/Portfolio State é a projeção interna autoritativa do estado corrente derivado. Quando houver integração, broker/venue será autoridade sobre a realidade externa efetiva, não sobre nossa história ou causalidade. Strategy pode ter estado analítico, mas nunca posição financeira autoritativa paralela.

Lifecycle: `TradeIntent → RiskDecision/RiskAuthorization → OrderIntent → ExecutionAttempt → ordem enviada → ExecutionReport → Fill → Ledger → PositionChange → Position/Portfolio State`. Esses artefatos não são equivalentes: somente fill válido ou ajuste explícito de reconciliation pode causar `PositionChange`. Risk decide sobre snapshot consistente e identificável de posição, exposição e compromissos pendentes; exposição considera também capacidade comprometida/potencial relevante.

## Invariantes

- OrderIntent, envio e ACK não alteram posição por si.
- Toda RiskDecision referencia o estado de risco sobre o qual foi tomada.
- Divergência externa gera mismatch e ajuste auditável, não sobrescrita silenciosa.

## Consequências positivas

Evita posições concorrentes e permite distinguir fill normal de correção de reconciliation.

## Consequências negativas / trade-offs

Requer projeções, snapshots e futura modelagem de reservas de exposição.

## Condições para reabrir a decisão

Exigência de domínio que preserve as três autoridades e a cadeia explícita, formalizada em ADR.

## Relação com outros ADRs

É consumido por Risk/Execution (0007), persistência (0009), recovery (0010) e provenance (0013).
