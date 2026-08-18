# ADR 0008 — Perfis operacionais, replay e determinismo

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

Replay, Backtest, Paper e Live possuem finalidades diferentes e não devem espalhar condicionais pelo domínio.

## Problema

Reutilizar o núcleo sem equiparar reprodução de eventos a experimento econômico.

## Alternativas consideradas

- Um `mode` global: gera condicionais difusas.
- Tratar replay como backtest: confunde finalidade e evidência.
- Perfis de composição: varia adaptadores e clock, preservando domínio.

## Decisão

Os quatro modos são perfis de composição por clock, fonte de mercado, execução, persistência e accounting. Replay reproduz eventos e pode não tomar decisões; Backtest é experimento econômico que combina replay, decisão, simulador, custos e métricas; Paper usa mercado contemporâneo e execução simulada; Live só poderá existir futuramente com adaptadores reais e reconciliação. O clock é controlável: avançado por evento em Replay/Backtest e sistêmico em Paper/Live. Dadas mesmas entradas, configuração, código, estado inicial e seeds, Backtest deve ser determinístico.

## Invariantes

- Todo backtest pode usar replay; nem todo replay é backtest.
- Se Replay produz decisão de domínio, provenance completa se aplica.
- Aleatoriedade futura exige seed explícita.

## Consequências positivas

Evita mode spaghetti e permite testes temporais reprodutíveis.

## Consequências negativas / trade-offs

Composição e simuladores precisam ser definidos antes da implementação dos modos.

## Condições para reabrir a decisão

Novo perfil comprovadamente não representável pelas dimensões semânticas definidas.

## Relação com outros ADRs

Depende de tempo/fidelidade (0004), provenance (0013) e estado/recovery (0010 e 0014).
