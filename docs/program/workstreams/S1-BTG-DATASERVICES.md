# Sprint 1 — BTG Solutions Data Services provider workstream

## Estado

```text
DD_60 = ACCEPTED
PROVIDER = BTG Solutions Data Services
ADR = ADR-0023
DD_43 = TRIGGERED
DD_68 = UNDECIDED
REAL_PROVIDER_CONNECTION = NOT_EXECUTED
REAL_CAPTURE = NOT_EXECUTED
VENDOR_AUTO_RECONNECT = DISABLED
TRADING_CAPABILITY = ABSENT
```

A seleção humana de DD-60 ocorreu em 2026-09-14: `Aprovo DD-60 = BTG Solutions Data Services`.

## Fontes oficiais consultadas

- Serviço e exemplo de WebSocket: https://dataservices.btgpactualsolutions.com/
- Cliente Python WebSocket: https://python-client-docs.dataservices.btgpactualsolutions.com/btgsolutions_dataservices.websocket.html
- Fonte publicada de `MarketDataWebSocketClient`: https://python-client-docs.dataservices.btgpactualsolutions.com/_modules/btgsolutions_dataservices/websocket/market_data_websocket_client.html
- Fonte publicada de autenticação: https://python-client-docs.dataservices.btgpactualsolutions.com/_modules/btgsolutions_dataservices/rest/authenticator.html
- Pacote PyPI: `btgsolutions-dataservices-python-client==4.8.0`

A documentação oficial confirma suporte a B3, `derivatives`, `trades`, candles e subscription/unsubscription. O `MarketDataWebSocketClient` entrega ao callback o texto recebido do WebSocket antes de qualquer parse do BTG AI Trader. Seu `Authenticator` troca API key por token via endpoint de autenticação.

## Implementação nesta branch

- ADR-0023 materializa DD-60 e a política DD-43.
- `BtgDataServicesSettings` restringe a primeira integração a B3/derivatives e tipos de dados `trades`, `candles-1S` e `candles-1M`.
- `BtgDataServicesSubscription` expõe apenas lifecycle read-only, subscription, discovery passivo, capabilities e callback raw.
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

O cliente oficial passa `data` diretamente do callback WebSocket para `on_message`. Para frames textuais, o adapter exige `str` e preserva `data.encode("utf-8")` em `RawFrame` antes da admissão/normalização do domínio.

Isso preserva o conteúdo textual recebido pelo callback, mas não reivindica preservação de framing TCP/WebSocket ou bytes anteriores à decodificação UTF-8 feita pela biblioteca subjacente.

## DD-43 — política de credencial

A API key real deverá vir de secret store/ambiente autorizado e nunca de arquivo versionado. O repositório não contém valor real, placeholder configurável nem secret de CI.

O adapter não deve:

- persistir ou hashear a API key;
- colocar a API key em `CaptureContext`, `RunManifest`, EvidenceArchive ou AuditJournal;
- emitir o valor em logs/erros;
- aceitar credencial de conta de trading como requisito funcional.

O cliente oficial mantém sua autenticação somente no processo/sessão necessária à conexão.

## DD-68 — próximo gate humano

Antes da primeira captura real deve ser selecionado o primeiro instrumento de laboratório. Nenhum ticker é default do runtime. O identificador `TEST-DERIV-1` usado nos testes é explicitamente sintético e não constitui decisão DD-68.

## Evidência ainda necessária

1. CI completa desta branch;
2. CI específica do extra oficial;
3. revisão independente do diff;
4. escolha DD-68;
5. provisão de API key read-only fora do repositório;
6. sessão real controlada provando autenticação, discovery, subscribe, ticks/candles, heartbeat/disconnect e restart explícito com raw capture;
7. atualização da matriz RQM/XC no SHA integrado;
8. Security Diff Scan oficial antes do gate final, ou waiver humano explícito conforme governança.

## Proibições preservadas

`order_send`, OrderIntent, OrderPlan, ExecutionOrder, Paper, Strategy, ML operacional, Risk Authorization, ledger financeiro, conta broker e qualquer compromisso econômico permanecem fora do runtime S1.
