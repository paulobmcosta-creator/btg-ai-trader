# ADR 0010 — Recovery, reconciliação e resultados desconhecidos

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

Falhas entre persistência, comunicação e resposta externa podem deixar o resultado de uma tentativa desconhecido.

## Problema

Retomar operação sem duplicar efeitos ou mascarar divergências.

## Alternativas consideradas

- Retentar cegamente: pode duplicar efeito externo.
- Considerar falha como ausência de efeito: pode ignorar execução real.
- Recovery com reconciliação explícita e fail-closed: mantém segurança.

## Decisão

Startup segue máquina de estados: carregar estado, consultar fonte externa quando houver, reconciliar, registrar divergências, resolver explicitamente e só então `READY`. Enquanto inconsistente, novas exposições são proibidas. Resultado desconhecido de execução exige reconciliation; retry cego é proibido. Divergência ou ajuste não reescreve histórico: torna-se evento auditável e repercute por Ledger/PositionChange segundo ADR 0014.

## Invariantes

- `READY` exige consistência suficiente documentada.
- Incerteza operacional falha fechada para aumento de exposição.
- Reconciliation não sobrescreve posição silenciosamente.

## Consequências positivas

Reduz duplicidade, viés de estado e perda de trilha forense.

## Consequências negativas / trade-offs

Pode atrasar retomada e exige investigação de divergências.

## Condições para reabrir a decisão

Somente novos mecanismos externos com garantias verificáveis, sem permitir retry cego.

## Relação com outros ADRs

Usa journal (0009), fail-safe (0011) e ownership (0014).
