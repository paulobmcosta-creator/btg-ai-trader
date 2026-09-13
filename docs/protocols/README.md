# Protocolos

Protocolos transformam princípios arquiteturais e científicos em procedimentos reproduzíveis, contratos conceituais e evidências auditáveis.

---

## 1. Protocolos de Segurança

- [Protocolo de Segurança — Fase Estrutural](SAFETY.md): Diretrizes e restrições obrigatórias para impedir a introdução de capacidades operacionais ou financeiras nas fases iniciais do projeto.

---

## 2. Protocolos Quantitativos (Sprint 0E)

Os protocolos quantitativos estabelecem a metodologia científica, a integridade temporal, a simulação realista de mercado, os critérios estatísticos de validação e as regras de promoção/rejeição de modelos e estratégias.

- **[Visão Geral e Índice dos Protocolos Quantitativos](quantitative/README.md)**
- **[0E-A — Semântica Experimental e Hipótese Quantitativa](quantitative/0E-A-experimental-semantics.md)**
- **[0E-B — Dados, RunInputBoundary e Integridade Temporal](quantitative/0E-B-dataset-temporal-integrity.md)**
- **[0E-C — Desenho de Validação, Out-of-Sample e Baselines](quantitative/0E-C-validation-oos-baselines.md)**
- **[0E-D — Backtest e Simulação de Mercado](quantitative/0E-D-backtest-market-simulation.md)**
- **[0E-E — Validação Estatística e Econômica](quantitative/0E-E-statistical-economic-validation.md)**
- **[0E-F — Avaliação de Modelos e Estratégias](quantitative/0E-F-strategy-model-evaluation.md)**
- **[0E-G — Promoção, Paper Trading e Rejeição](quantitative/0E-G-promotion-paper-rejection.md)**
- **[0E-H — Gate de Consistência Transversal](quantitative/0E-H-cross-protocol-gate.md)**
- **[Matriz de Rastreabilidade HQI ↔ QPI](quantitative/TRACEABILITY.md)**

---

## 3. Estado Normativo

Os protocolos quantitativos 0E-A a 0E-G e o gate 0E-H foram formalmente concluídos e aprovados (`FINAL_0E_DOC_GATE: PASS` | Human Approval: `APPROVED` em 2026-08-22). A fase de Fundação 0A–0F está formalmente fechada. O PR #5 foi integrado em `dabce69d92054b77cad72809669d4340c211c328` e a Issue #1 foi fechada como concluída. O mandato humano de execução autônoma de 2026-09-13 autoriza a primeira implementação funcional do Sprint 1 (`PRE_CODE_RECONCILIATION = COMPLETE`; `S1_A_AUTHORIZED = YES`; `FIRST_FUNCTIONAL_CODE = AUTHORIZED`), sob o contrato 0F-E integral e os gates de promoção. Nenhuma evidência experimental ou integração read-only de market data autoriza negociação real sem a superação cumulativa dos gates de produção e aprovação humana explícita.
