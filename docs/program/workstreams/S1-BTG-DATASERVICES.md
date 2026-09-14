# Sprint 1 — BTG Solutions Data Services provider workstream

## Estado

```text
DD_60 = ACCEPTED
PROVIDER = BTG Solutions Data Services
ADR = ADR-0023
DD_43 = TRIGGERED
DD_68 = RESOLVED
DD_68_INSTRUMENT_FAMILY = WIN
DD_68_CONCRETE_CONTRACT = RESOLVE_POINT_IN_TIME
DD_68_AUTO_FALLBACK = FORBIDDEN
DD_68_STREAM_TYPE = realtime
DD_68_DATA_GRANULARITY = trades
DD_68_INITIAL_CANDLES = NO
REAL_PROVIDER_CONNECTION = NOT_EXECUTED
REAL_CAPTURE = NOT_EXECUTED
VENDOR_AUTO_RECONNECT = DISABLED
TRADING_CAPABILITY = ABSENT
```

A seleção humana de DD-60 ocorreu em 2026-09-14: `Aprovo DD-60 = BTG Solutions Data Services`.

A decisão humana DD-68 também foi concluída em 2026-09-14: a família inicial é `WIN`; o contrato futuro concreto deve ser resolvido e confirmado point-in-time no BTG Data Services imediatamente antes de cada captura real; fallback/rollover silencioso é proibido; e o primeiro laboratório usa `trades` em `realtime`, sem candles como input inicial. Ver [`S1-DD68-FIRST-LAB.md`](S1-DD68-FIRST-LAB.md).

## Fontes oficiais consultadas

- Serviço e exemplo de WebSocket: https://dataservices.btgpactualsolutions.com/
- Cliente Python WebSocket: https://python-client-docs.dataservices.btgpactualsolutions.com/btgsolutions_dataservices.websocket.html
- Fonte publicada de `MarketDataWebSocketClient`: https://python-client-docs.dataservices.btgpactualsolutions.com/_modules/btgsolutions_dataservices/websocket/market_data_websocket_client.html
- Fonte publicada de autenticação: https://python-client-docs.dataservices.btgpactualsolutions.com/_modules/btgsolutions_dataservices/rest/authenticator.html
- Pacote PyPI: `btgsolutions-dataservices-python-client==4.8.0`

A documentação oficial confirma suporte a B3, `derivatives`, `trades`, candles e subscription/unsubscription. O `MarketDataWebSocketClient` entrega ao callback o texto recebido do WebSocket antes de qualquer parse do BTG AI Trader. Seu `Authenticator` troca API key por token via endpoint de autenticação.

## Implementação nesta branch

- ADR-0023 materializa DD-60 e a política DD-43.
- `BtgDataServicesSettings` restringe a primeira integração a B3/derivatives e suporta `trades`, `candles-1S` e `candles-1M`; DD-68 fixa o primeiro laboratório real especificamente em `realtime` + `trades`.
- `BtgDataServicesSubscription` expõe apenas lifecycle read-only, subscription, discovery passivo, capabilities e callback raw.
- O lifecycle é obrigatoriamente staged: `start()` apenas conecta; `request_available_instruments()` ocorre antes da assinatura; `subscribe_confirmed()` só é chamado depois da confirmação externa do contrato point-in-time.
- Mensagens recebidas antes da assinatura são roteadas exclusivamente para `control_sink` e nunca recebem `ProviderInstrumentRef`/`RawChannel` de market data. Após `subscribe_confirmed()`, mensagens textuais passam para `RawFrame` da referência confirmada.
- Discovery após assinatura e assinatura duplicada falham fechado.
- O wrapper recebe `credential_source` e não armazena o segredo no próprio adapter.
- O wrapper recebe `client_factory` por injeção; o runtime S1 continua sem import externo direto e o boundary fail-closed não é relaxado.
- O pacote oficial é um extra opcional explícito `btg-data`, não uma dependência runtime universal.
- CI separada instala o extra e verifica a presença apenas dos métodos read-only necessários, sem instanciar o cliente e sem autenticar.
- Testes usam cliente fake; nenhuma API key real, rede ou conta é usada.

## Reconnect fail-closed

A fonte oficial do cliente mostra que, no `on_close`, o reconnect interno chama `run(...)` novamente sem repassar `spawn_thread` e `default_logs`, que retornariam aos defaults. Além disso, uma assinatura feita depois de `run()` não passa a integrar automaticamente `self.instruments` do cliente para resubscription na reconexão.

Por isso, o Sprint 1 **desabilita o reconnect automático do vendor**. `BtgDataServicesSettings(reconnect=True)` falha fechado e o wrapper sempre chama `run(..., reconnect=False, spawn_thread=False, default_logs=False)`.

Após uma queda, a recuperação deverá encerrar a sessão e criar explicitamente uma nova sessão/subscription auditável. Isso preserva configuração, observabilidade e causalidade em vez de aceitar reconnect implícito com defaults diferentes.

## Fronteira de payload

O cliente oficial passa `data` diretamente do callback WebSocket para `on_message`. Para frames textuais, o adapter exige `str` e preserva `data.encode("utf-8")` antes de qualquer interpretação de domínio.

Antes de `subscribe_confirmed()`, esse payload é evidência de controle/discovery e vai apenas para `control_sink`; ele não é rotulado como tick/candle nem associado ao instrumento candidato. Depois da confirmação e assinatura explícitas, o payload textual de market data é materializado como `RawFrame` com a referência confirmada.

Isso preserva o conteúdo textual recebido pelo callback, mas não reivindica preservação de framing TCP/WebSocket ou bytes anteriores à decodificação UTF-8 feita pela biblioteca subjacente.

## DD-43 — política de credencial

A API key real deverá vir de secret store/ambiente autorizado e nunca de arquivo versionado. O repositório não contém valor real, placeholder configurável nem secret de CI.

O adapter não deve:

- persistir ou hashear a API key;
- colocar a API key em `CaptureContext`, `RunManifest`, EvidenceArchive ou AuditJournal;
- emitir o valor em logs/erros;
- aceitar credencial de conta de trading como requisito funcional.

O cliente oficial mantém sua autenticação somente no processo/sessão necessária à conexão.

## DD-68 — laboratório WIN / trades realtime

A família `WIN` foi aprovada como primeiro laboratório. Nenhum ticker concreto é default permanente do runtime.

Antes de cada captura real, o sistema deverá resolver no discovery do BTG Data Services qual contrato WIN concreto será usado e confirmar sua disponibilidade point-in-time. O símbolo selecionado fica fixo para aquele run/capture context. Se a resolução for ausente, ambígua ou inválida, a captura não inicia.

É proibido fallback automático, ranking implícito, troca silenciosa para outro vencimento ou rollover invisível. O identificador `TEST-DERIV-1` continua sendo somente fixture.

Para a primeira captura real, DD-68 fixa:

```text
stream_type = realtime
data_type = trades
data_subtype = derivatives
initial_candles = no
```

A capacidade futura de candles permanece disponível no adapter, mas não integra o primeiro laboratório real e não pode substituir silenciosamente o stream de trades.

## Evidência ainda necessária

1. CI atual do HEAD desta branch executado com runners funcionais;
2. CI específica do extra oficial no HEAD atual;
3. revisão independente do diff atual;
4. provisão de API key read-only fora do repositório;
5. sessão real controlada provando autenticação, discovery point-in-time do contrato WIN, confirmação antes de `subscribe_confirmed()`, observação `trades/realtime`, heartbeat/disconnect e restart explícito com raw capture;
6. atualização da matriz RQM/XC no SHA integrado;
7. Security Diff Scan oficial antes do gate final, ou waiver humano explícito conforme governança.

## Proibições preservadas

`order_send`, OrderIntent, OrderPlan, ExecutionOrder, Paper, Strategy, ML operacional, Risk Authorization, ledger financeiro, conta broker e qualquer compromisso econômico permanecem fora do runtime S1.
