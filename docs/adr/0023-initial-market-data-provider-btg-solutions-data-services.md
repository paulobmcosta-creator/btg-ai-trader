# ADR 0023 — Provedor inicial de Market Data: BTG Solutions Data Services

- **Status:** Aceita
- **Data:** 2026-09-14
- **Decisão deferida resolvida:** DD-60 — Provedor inicial de Market Data
- **Autorização humana:** “Aprovo DD-60 = BTG Solutions Data Services”

## Contexto

O Sprint 1 exige um provider real read-only para `AC-05 — Read-Only Market-Data Subscription`, sem introduzir qualquer capability financeira. A baseline do Observer já possui contratos provider-agnostic, fixture provider, discovery point-in-time, ingestão, quarantine, proveniência, persistência, health, backpressure e NEG-CAP; faltava selecionar o primeiro provider concreto.

O spike MT5 demonstrou apenas compatibilidade de import e uma superfície dual-use ampla. Ele não provou conexão read-only, coleta, as 11 condições de admissibilidade nem isolamento suficiente para promover MT5 a provider canônico.

A documentação oficial atual do BTG Solutions Data Services oferece APIs de market data B3 e cliente Python, inclusive WebSocket com `trades`, `books`, candles, `instrument_status` e subtipo `derivatives`. O produto é de dados e usa API key para obter token de autenticação; não é uma API de brokerage/order routing.

## Decisão

Selecionar **BTG Solutions Data Services** como provider inicial de Market Data do Sprint 1.

A integração canônica usará exclusivamente uma superfície read-only do cliente oficial de market data. Para preservar o payload textual recebido pelo WebSocket antes da normalização do domínio, a primeira implementação usará `MarketDataWebSocketClient` atrás de um wrapper local estreito.

O wrapper do BTG AI Trader poderá expor somente capacidades de observação e lifecycle de assinatura, como:

- abrir o feed read-only;
- assinar instrumento explicitamente configurado;
- receber payloads de market data;
- consultar discovery/subscription quando necessário;
- cancelar assinatura;
- fechar a conexão;
- declarar capabilities do provider.

Métodos adicionais do SDK que não sejam necessários ao Market Observer não entram na interface do domínio nem no wiring do Observer.

## DD-43 — credencial read-only

A seleção de DD-60 aciona DD-43.

Política inicial:

- a API key é segredo externo ao repositório;
- não pode existir literal de credencial em código, config, fixtures, logs, manifestos ou evidências;
- a credencial é injetada apenas em runtime pelo ambiente autorizado/secret store;
- o adapter não registra, serializa, hasheia nem persiste o valor da API key;
- o cliente oficial pode manter a key/token somente em memória durante a sessão;
- erros e telemetria do BTG AI Trader nunca incluem a credencial;
- nenhuma credencial de trading/broker account é aceita ou necessária.

## DD-68 — primeiro laboratório

A decisão DD-68 foi **parcialmente resolvida** por coordenação humana em 2026-09-14:

- família inicial do laboratório: `WIN`;
- contrato futuro concreto: resolução e confirmação point-in-time no BTG Data Services imediatamente antes da captura;
- nenhum ticker concreto é default permanente do runtime;
- fallback automático, ranking implícito, troca silenciosa de vencimento e rollover invisível são proibidos;
- se o contrato pretendido estiver ausente, ambíguo ou não puder ser causalmente resolvido, a captura não inicia.

O símbolo concreto selecionado para uma sessão deve ser fixado no respectivo run/capture context antes da subscription e não pode ser trocado silenciosamente durante a sessão.

A granularidade/timeframe do primeiro laboratório permanece **UNDECIDED** e deve ser explicitamente resolvida antes da primeira captura real. Defaults de adapter/fixture não contam como decisão DD-68.

O registro operacional detalhado está em `docs/program/workstreams/S1-DD68-FIRST-LAB.md`.

## Restrições de segurança

- `REAL_MONEY = NO`
- `LIVE_TRADING = NO`
- `BROKER_ORDER_SUBMISSION = NO`
- `TRADING_CREDENTIALS = NO`
- `ECONOMIC_AUTHORITY = NONE`
- `MODEL_DIRECT_TO_BROKER = NO`
- `RISK_BYPASS = NO`

A presença do pacote oficial de Data Services não autoriza nenhuma outra API do ecossistema BTG.

## Evidência requerida antes do fechamento do Sprint 1

1. import/instalação reproduzível do cliente oficial em Python 3.12;
2. testes unitários do wrapper com cliente fake, sem rede e sem segredo real;
3. prova de que o wrapper expõe somente operações read-only necessárias;
4. callback preservando o payload textual recebido antes da decodificação de domínio;
5. subscription/unsubscription/lifecycle testados sem capability financeira;
6. integração do novo módulo ao boundary/NEG-CAP inventory;
7. resolução explícita da granularidade/timeframe de DD-68, API key read-only externa e captura real controlada com contrato WIN resolvido point-in-time;
8. Security Diff Scan oficial ou tratamento explícito do gate correspondente.

## Consequências

DD-60 deixa de ser blocker decisório. DD-43 passa a estar acionado, mas não exige armazenar qualquer segredo no GitHub. DD-61 continua não acionado porque MT5 não foi selecionado. O spike MT5 permanece histórico/experimental e não entra na baseline canônica do provider.
