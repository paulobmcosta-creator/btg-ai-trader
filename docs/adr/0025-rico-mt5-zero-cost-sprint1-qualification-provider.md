# ADR-0025 — Rico + MetaTrader 5 como provider de qualificação zero-cost do Sprint 1

- **Status:** Aceita
- **Data:** 2026-09-14
- **Escopo:** Sprint 1 — Market Observer
- **Refina/Substitui para o provider ativo do Sprint 1:** ADR-0023
- **Observação histórica:** o número ADR-0024 foi utilizado no caminho Cedro free-trial posteriormente revertido; não é reutilizado.

## Contexto

O ADR-0023 selecionou BTG Solutions Data Services como provider inicial de market data. A implementação correspondente foi útil como referência técnica, porém o owner estabeleceu posteriormente uma restrição dura de custo adicional recorrente igual a zero. O caminho BTG Data Services deixou, portanto, de ser aceitável como provider operacional canônico do Sprint 1.

Em seguida foi explorado Cedro Market Data por free trial. Esse caminho foi materializado historicamente como ADR-0024, mergeado e depois explicitamente revertido pelo commit `1616958de7db5f06b2dc82067fedfefe411dce5e`, porque um trial limitado no tempo não satisfaz o requisito de sustentabilidade pós-desenvolvimento.

O Sprint 1 mantém, sem relaxamento, suas obrigações de observação realtime, descoberta/resolução de instrumento, provenance e ausência de qualquer capacidade financeira.

Em 14/09/2026, a documentação pública corrente da Rico registra MetaTrader 5 como gratuito para clientes, contratação isenta de cobrança e, no comparativo oficial de plataformas, custo `GRÁTIS`, mínimo de corretagem `N/A`, isenção por quantidade de contratos/RLP `N/A` e operações automatizadas suportadas. Essas condições comerciais são evidência para seleção, mas não substituem prova runtime do feed real.

A documentação oficial MQL5 oferece duas propriedades de segurança relevantes para o Sprint 1:

1. conexão em **Investor mode** resulta em `ACCOUNT_TRADE_ALLOWED = false` e trading desabilitado;
2. custom indicators não podem chamar `OrderSend`, `OrderCheck`, `OrderCalcMargin` ou `OrderCalcProfit`.

## Decisão

Selecionar **Rico-supplied MetaTrader 5 market data** como provider a ser qualificado para o Sprint 1, utilizando uma fronteira estruturalmente read-only baseada em **custom MQL5 indicator** e transporte local unidirecional de market data para o BTG AI Trader.

A seleção é aceita; a qualificação de produção do provider permanece pendente até sessão real comprovada.

```text
PROVIDER_SELECTION = RICO_SUPPLIED_MT5
PROVIDER_SELECTION_STATUS = ACCEPTED_FOR_QUALIFICATION
REAL_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
```

Arquitetura alvo do Sprint 1:

```text
Rico / MT5 trade server
    -> MetaTrader 5 terminal
       -> INVESTOR / READ-ONLY authorization
       -> custom MQL5 INDICATOR attached to exact WIN symbol
          -> passive tick/price observations only
          -> bounded append-only local transport
             -> BTG AI Trader Python Market Observer
                -> RawFrame / admission / evidence / provenance
```

O processo Python confiável do Sprint 1 não deve importar o package `MetaTrader5` nem receber interface de conta, ordem, posição operacional ou trading.

## Invariantes negativas

A implementação e a qualificação devem preservar integralmente:

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

## Gate de qualificação runtime

A seleção somente poderá ser promovida para `SPRINT1_PROVIDER_QUALIFIED = YES` se uma sessão real comprovar, no mínimo:

1. MetaTrader 5 ativável na conta Rico sem cobrança adicional recorrente no estado de conta utilizado;
2. acesso ao contrato corrente da família WIN e resolução do símbolo exato;
3. recepção realtime de ticks/cotações suficiente para AC-05 e AC-07;
4. login efetivo em Investor/read-only mode ou mecanismo equivalente que resulte em trading desabilitado no servidor/terminal;
5. bridge executado como custom indicator;
6. evidência de que o processo Python não possui API de ordens nem credencial master;
7. timestamps, provenance, heartbeat/latência e evidências de captura compatíveis com os contratos congelados do Sprint 1;
8. ausência de requisito de operação real mínima para manter o entitlement de market data/plataforma utilizado na qualificação.

Falha em qualquer item rejeita **essa qualificação da Rico**, mas não altera o contrato abstrato do `MarketDataProvider` nem enfraquece os acceptance criteria.

## Consequências

### Positivas

- elimina dependência de trial temporário como provider canônico;
- preserva custo adicional recorrente zero como requisito arquitetural;
- mantém realtime como obrigação do Sprint 1;
- cria defesa em profundidade entre observação e trading;
- mantém broker/provider substituível atrás da abstração existente;
- preserva possibilidade de automação futura do MT5 em outro boundary, somente após gates posteriores, sem introduzi-la no Sprint 1.

### Restrições

- a gratuidade comercial é condição externa mutável e precisa ser revalidada antes de cada qualificação relevante;
- a documentação pública não prova, por si só, disponibilidade de WIN realtime na conta concreta do owner;
- a seleção deste ADR não autoriza `SPRINT1_ACCEPTANCE`, `PROMOTION_TO_SPRINT_2`, paper trading ou live trading;
- credencial master não pode ser usada como atalho caso Investor mode não esteja disponível.

## Alternativas consideradas

### BTG Solutions Data Services

Preservado como implementação histórica de referência, mas rejeitado como provider operacional atual devido ao requisito de custo adicional zero.

### Cedro Market Data free trial

Rejeitado como provider canônico por limitação temporal. O histórico permanece no Git e não é reescrito.

### B3 D-1 / histórico e brapi

Úteis para pesquisa, desenvolvimento e replay, mas não substituem evidência realtime exigida pelo Sprint 1.

### Outras corretoras com MT5

Permanecem fallback substituível se a qualificação Rico falhar, sem exigir mudança na semântica do Observer.

## Evidências públicas consultadas na decisão

- Rico — MetaTrader: https://www.rico.com.vc/plataformas/metatrader/
- Rico — Comparativo de plataformas: https://www.rico.com.vc/documentos/comparativo-plataformas/
- MQL5 — Trade Permission: https://www.mql5.com/en/docs/runtime/tradepermission
- MQL5 — Program Running / funções proibidas em indicators: https://www.mql5.com/en/docs/runtime/running

Esses links documentam a base da seleção em 14/09/2026. Condições comerciais e entitlement de market data devem ser revalidados no gate runtime.