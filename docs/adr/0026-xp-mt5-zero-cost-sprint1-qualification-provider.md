# ADR-0026 — XP + MetaTrader 5 como provider de qualificação zero-cost do Sprint 1

- **Status:** Aceita
- **Data:** 2026-09-14
- **Escopo:** Sprint 1 — Market Observer
- **Substitui para o provider ativo do Sprint 1:** ADR-0025
- **Preservação histórica:** ADR-0025 permanece imutável como registro da tentativa Rico/MT5.

## Contexto

O ADR-0025 selecionou Rico-supplied MetaTrader 5 para qualificação porque o programa exige `ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT` sem relaxar realtime, provenance ou a ausência de capacidade financeira.

A implementação MT5 construída sob esse ADR permaneceu tecnicamente útil, mas o fluxo concreto de provisionamento Rico não permitiu concluir a qualificação operacional. O próprio ADR-0025 preservou outras corretoras com MT5 como fallback substituível sem mudança na semântica do Observer.

Em 14/09/2026, a XP publicava MetaTrader 5 como gratuito para clientes e seu comparativo oficial registrava `METATRADER 5.0 | GRÁTIS | N/A | N/A | WINDOWS | UNICAST`. Essa evidência pública suporta seleção, mas não substitui prova da condição concreta da conta nem da disponibilidade realtime do WIN.

No mesmo dia, uma sessão preliminar do owner demonstrou, sem execução financeira:

1. autenticação funcional no MT5 fornecido/servido pela XP;
2. criação e uso local de autorização Investor/read-only, sem exposição de senha ao repositório ou ao chat;
3. compilação do custom indicator revisado com `0 errors, 0 warnings` antes desta reconciliação;
4. discovery passivo de `WIN*` no servidor XP, com 57.414 símbolos enumerados, 16 candidatos emitidos, `prefix_errors = 0` e `enumeration_errors = 0`;
5. presença de `WINV26` no conjunto observado e identificação preliminar desse contrato como alvo point-in-time.

Essa sessão é **pré-qualificação**. Ela não satisfaz AC-05/AC-07, não prova entitlement econômico da conta e não autoriza declarar o provider qualificado.

## Decisão

Selecionar **XP-supplied MetaTrader 5 market data** como provider ativo a ser qualificado para o Sprint 1, preservando a fronteira estruturalmente read-only já aprovada:

```text
XP / MT5 trade server
    -> MetaTrader 5 terminal
       -> INVESTOR / READ-ONLY authorization
       -> custom MQL5 INDICATOR attached to exact WIN symbol
          -> passive tick/price observations only
          -> bounded append-only FILE_COMMON transport
             -> BTG AI Trader Python Market Observer
                -> RawFrame / admission / evidence / provenance
```

```text
PROVIDER_SELECTION = XP_SUPPLIED_MT5
PROVIDER_ID = xp-mt5
PROVIDER_SELECTION_STATUS = ACCEPTED_FOR_QUALIFICATION
REAL_QUALIFYING_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
```

A troca Rico -> XP é uma substituição de provider concreto, não uma mudança do contrato abstrato `MarketDataProvider` nem uma autorização para execução.

## Compatibilidade de implementação

Para reduzir churn antes da primeira captura probatória, nomes físicos históricos como `rico_mt5_bridge.py`, `RicoMt5BridgeReader`, `RicoMarketDataBridge.mq5` e `scripts/rico_mt5_first_lab_capture.py` podem permanecer temporariamente como nomes de compatibilidade.

Esses nomes **não** definem a identidade de provenance. A identidade ativa da captura deve ser `xp-mt5`. O custom indicator recebe `ProviderId = xp-mt5` e o trusted Python deve validar a mesma identidade.

A generalização/renomeação física desses artefatos pode ocorrer em mudança posterior, desde que não seja usada para atrasar ou confundir a evidência runtime e preserve os mesmos gates.

## Invariantes negativas

```text
TRUSTED_PYTHON_IMPORTS_METATRADER5 = NO
MT5_MASTER_PASSWORD_IN_PROJECT = NO
MT5_MASTER_PASSWORD_IN_CHAT = NO
MT5_MASTER_PASSWORD_IN_SECRET_STORE = NO
MT5_INVESTOR_PASSWORD_ONLY = YES
MQL5_BRIDGE_PROGRAM_TYPE = CUSTOM_INDICATOR
MQL5_ORDER_SEND = STRUCTURALLY_PROHIBITED
PYTHON_ORDER_API = ABSENT
BROKER_ACCOUNT_API = ABSENT
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
REAL_MONEY_PATH = ABSENT
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

Nenhuma tentativa de ordem pode ser usada como teste de read-only.

## Gate de qualificação runtime

XP somente poderá ser promovida para `SPRINT1_PROVIDER_QUALIFIED = YES` quando evidência revisada demonstrar, de forma conjuntiva:

1. MT5 disponível na conta XP concreta sem cobrança adicional recorrente da plataforma/feed usado na qualificação;
2. ausência de requisito de operação real mínima, RLP, corretagem mínima ou equivalente para preservar esse entitlement específico;
3. Investor/read-only efetivo no terminal/servidor, sem credencial master no trusted path;
4. discovery completo e resolução explícita do contrato corrente da família WIN no contexto da sessão;
5. recepção realtime de ticks/cotações suficiente para AC-05 e AC-07;
6. pelo menos um candle genuinamente finalizado por transição observada enquanto o indicator está anexado;
7. custom indicator como único bridge MT5 e ausência de `MetaTrader5`, conta, posição ou ordem no Python confiável;
8. timestamps, provenance, RunId, config hash, heartbeat/staleness e latência monotônica local preservados dentro do escopo real da evidência;
9. exact-final-tree CI/NEG-CAP green após reconciliação da evidência;
10. official Security Diff Scan executado no exact final Sprint 1 tree.

Falha em qualquer item rejeita essa qualificação XP sob as restrições atuais; não enfraquece o contrato do Sprint 1.

## Consequências

### Positivas

- reaproveita a fronteira MT5 read-only já implementada e testada;
- resolve o bloqueio operacional de provisionamento encontrado no caminho Rico;
- preserva custo adicional recorrente zero como condição de arquitetura;
- mantém realtime como obrigação, não como pressuposto;
- mantém o provider substituível e o Python sem API de execução;
- preserva todo o histórico Rico/BTG/Cedro para auditoria.

### Restrições

- a evidência preliminar de 14/09/2026 não é captura qualificadora;
- `WINV26` precisa ser confirmado/preservado como mapping point-in-time na sessão qualificadora;
- marketing/tabela pública da XP não substituem comprovação da condição da conta concreta;
- este ADR não autoriza Sprint 1 PASS, Sprint 2, Paper, Risk, Strategy, ML operacional ou live trading.

## Evidências públicas consultadas na decisão

- XP — Plataformas de negociação: https://www.xpi.com.br/plataformas/
- XP — Comparativo de plataformas: https://web.xpi.com.br/xp/documentos/comparativo-de-plataformas/
- MetaTrader 5 — Authorization: https://www.metatrader5.com/pt/terminal/help/startworking/authorization
- MQL5 — Program Running / restrictions: https://www.mql5.com/en/docs/runtime/running

Condições externas devem ser revalidadas no gate runtime.