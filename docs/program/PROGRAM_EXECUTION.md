# Program Execution — BTG AI Trader

## Checkpoint operacional corrente — 2026-09-13

Este arquivo é o checkpoint vivo de retomada. Estados anteriores permanecem preservados no histórico Git; este documento deve refletir apenas o estado operacional corrente.

```text
MANDATE_STATUS = IN_PROGRESS
EXECUTION_SURFACE = GITHUB_REMOTE
LOCAL_USER_CHECKOUT = OUT_OF_SCOPE
CONSOLIDATE_S1 = PRIORITY
NO_READY_WORK = FALSE
STOP_REASON = NONE

FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
PRE_CODE_RECONCILIATION = COMPLETE
S1_A_AUTHORIZED = YES
FIRST_FUNCTIONAL_CODE = AUTHORIZED
SPRINT1_ACCEPTANCE = NOT_GRANTED
CANONICAL_PROMOTION = GATE_CONTROLLED

REAL_MONEY = NO
LIVE_TRADING = NO
TRADING_CREDENTIALS = NO
BROKER_ORDER_SUBMISSION = NO
BROKER_ORDER_MODIFICATION = NO
BROKER_ORDER_CANCELLATION = NO
MODEL_DIRECT_TO_BROKER = NO
RISK_BYPASS = NO
```

## Baselines

- `main`: permanece na baseline histórica de Fundação; sem promoção automática.
- `sprint/1-market-observer`: HEAD atual confirmado após integração da composição do Observer: `64c419f5565cd5f222538ed7f79fcaaffb14476c`.
- PR #27 foi integrado por merge protegido pelo HEAD `87c8f92275e0db82dce026c6d15e37b7d94d7a65`.
- Merge commit do PR #27: `64c419f5565cd5f222538ed7f79fcaaffb14476c`.
- O merge do #27 promove composição funcional passiva do Observer para a baseline S1, mas NÃO concede aceitação do Sprint 1.

## Estado funcional S1

A baseline S1 agora contém de forma integrada:

- domínio de observação e temporalidade;
- registry e provider contracts;
- fixture provider;
- health/liveness passivo;
- fila bounded/FIFO e backpressure;
- dedup/late classification;
- admission/quarantine de fixtures;
- provenance, RunManifest e CaptureContext;
- EvidenceArchive/AuditJournal técnicos;
- composição síncrona `FixtureObserver`;
- testes integrados de composição e falhas de storage/backpressure.

Review independente do #27 encontrou PASS no HEAD `ad7835c...`. O delta posterior até `87c8f922...` foi apenas em teste para expor evidência sanitizada no CI; re-review do HEAD atual não encontrou blocker. Workflows do HEAD atual `34788510407` e `34788510362` concluíram SUCCESS antes do merge.

## NEG-CAP — PR #25

PR #25 foi retargetado para `sprint/1-market-observer` após o merge do #27.

HEAD corrente: `1eaa21aa9f61d6c32d120014b7eff83340bc0e8b`.

O subset estrutural já fecha as duas rotas de escape encontradas na revisão anterior:

- alias/cópia de módulo externo;
- alias de resultado obtido por reflexão finita.

Correções adicionais feitas nesta continuação:

- manifesto de boundary repinado para a composição revisada;
- `composition.py` incluído no inventário;
- pin de `storage_records.py` atualizado;
- `dataclasses.fields` e `typing.Any` explicitamente permitidos;
- reflexão finita de `ObserverConfig` catalogada;
- exceções AST limitadas apenas aos dois serializers já revisados (`ObserverConfig.canonical_bytes` e `_wire`).

A branch foi reancorada por merge GitData sobre a baseline S1 integrada, preservando somente o delta NEG-CAP no PR.

Status de gate:

```text
NEG_CAP_STRUCTURAL = IN_PROGRESS
NEG_CAP_RUNTIME_01_TO_10 = NOT_YET_COMPLETE
SECURITY_DIFF_SCAN = NOT_EXECUTED
SECURITY_DIFF_SCAN_REASON = REMOTE_TOOLING_UNAVAILABLE
```

Nenhum PASS final deve ser declarado antes de CI verde do HEAD corrente e execução das obrigações runtime aplicáveis.

## Properties / mutation — PR #26

PR #26 foi reancorado sobre a baseline S1 integrada preservando exatamente três arquivos de teste/documentação.

HEAD corrente: `650c073e66ba89088845b773f70455cf71235888`.

A campanha histórica anterior demonstrou:

- 36 casos gerados;
- 10 mutantes selecionados;
- 10 detectados;
- 0 sobreviventes;
- source canônico preservado.

Essa evidência precisa ser reexecutada no novo ancestry antes de ser usada como prova final de aceitação.

## Próximos READY nodes

1. Confirmar CI remota do PR #25 no HEAD `1eaa21aa...`.
2. Corrigir qualquer finding real do boundary checker sem enfraquecer o escopo.
3. Implementar/executar NEG-CAP runtime 01..10 sobre a composição integrada.
4. Confirmar CI e campanha de mutação do PR #26 no HEAD `650c073e...`.
5. Atualizar/reconciliar PR #16 (41 RQMs / 118 S1-EC / 20 NC / 10 NEG-CAP / Exit Criteria) usando apenas evidência do ancestry integrado.
6. Avaliar blockers reais restantes para `SPRINT1_ACCEPTANCE`.
7. Manter Security Diff Scan como `NOT_EXECUTED` até existir superfície remota compatível ou waiver humano explícito.

## Trabalho futuro preservado

- Replay causal reclassificado para Sprint 2, isolado.
- MT5 continua spike import-only; DD-60 permanece indeciso.
- S9/S12 experimentais permanecem preservados, sem prioridade sobre o fechamento S1.
- Nenhum novo workstream S3–S12 deve ser aberto antes de resolver os READY nodes de aceitação S1, salvo correção necessária ou trabalho trivial independente.

## Regra de retomada

Na próxima execução:

```text
READ THIS FILE
→ VERIFY REMOTE SHAS
→ CHECK PR25/PR26 CI
→ CONTINUE NEG-CAP + RQM EVIDENCE
→ DO NOT REPLAN FROM ZERO
→ DO NOT USE USER LOCAL CHECKOUT
```

Pare somente por `NO_READY_WORK`, `HUMAN_ONLY_DECISION`, `SAFETY_BLOCKER`, `EXTERNAL_CREDENTIAL_REQUIREMENT` ou `TOOL_OR_SESSION_LIMIT`.
