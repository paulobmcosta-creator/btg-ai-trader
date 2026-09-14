# ADR 0024 — Provedor de qualificação real do Sprint 1 sem custo: Cedro Market Data

- **Status:** Aceita
- **Data:** 2026-09-14
- **Decisão afetada:** DD-60 — Provedor inicial de Market Data
- **Substitui para qualificação real do Sprint 1:** ADR-0023 — BTG Solutions Data Services
- **Autorização humana:** coordenação determinou continuidade com alternativa de custo zero após constatar que o acesso real do BTG Data Services exige contratação comercial.

## Contexto

O contrato congelado `0F-E` exige, no Sprint 1, `AC-05 — Read-Only Market-Data Subscription` e `AC-07 — Tick & Candle Observation` em streaming/tempo real. Portanto, fontes gratuitas apenas de fim de dia, polling ou histórico não podem ser relabeladas como prova de subscription realtime.

A implementação BTG Data Services permanece tecnicamente válida e read-only, mas sua sessão real depende de credencial vinculada a serviço comercial. A coordenação definiu custo financeiro adicional igual a zero para o projeto. Esse novo requisito operacional não autoriza enfraquecer `0F-E`.

A pesquisa de alternativas encontrou:

- **B3 oficial:** histórico/fim de dia D-1 pode ser obtido/distribuído sem custo, mas isso não satisfaz `AC-05/AC-07` realtime;
- **brapi:** WIN/WDO podem ser consultados sem token em endpoints específicos, mas os dados de futuros são de fim de dia, atualizados após o pregão; não satisfaz streaming realtime;
- **Cedro Market Data:** oferece teste gratuito de 7 dias, WebSocket/Socket com dados B3 em streaming, realtime ou delay, cobertura BM&F/futuros, cotações e negócios realizados. A documentação pública separa Market Data de Trading e informa que a API de Market Data não envia ordens.

Fontes públicas consultadas em 2026-09-14:

- https://cedrotech.com/market-apis/api-websocket/
- https://cedrotech.com/produtos/market-data-cedro/
- https://docs.cedrotech.com/reference/market-data-introduction
- https://docs.cedrotech.com/reference/market-data-authentication
- https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/perguntas-frequentes/
- https://brapi.dev/docs/futuros

## Decisão

Selecionar **Cedro Market Data, exclusivamente por meio do teste gratuito**, como provider de qualificação real do Sprint 1.

Esta decisão preserva integralmente os requisitos do `0F-E`:

```text
COST_TO_PROJECT = R$ 0
PROVIDER = CEDRO_MARKET_DATA
ACCESS_MODE = FREE_TRIAL
TRIAL_WINDOW = 7_DAYS_AS_PUBLICLY_ADVERTISED
MARKET = B3_BMF
INSTRUMENT_FAMILY = WIN
TRANSPORT = STREAMING_WEBSOCKET_OR_SOCKET
DATA_PROFILE = REALTIME_TRADES
READ_ONLY = YES
ORDER_CAPABILITY_IN_S1_ADAPTER = ABSENT
BROKER_ACCOUNT = NOT_REQUIRED_BY_S1_MARKET_DATA_PATH
AUTO_FALLBACK = NO
AUTO_ROLLOVER = NO
```

O trial deve ser solicitado somente quando o adapter/testes estiverem prontos para evitar desperdiçar a janela de sete dias.

## Relação com ADR-0023 / BTG Data Services

ADR-0023 permanece como registro histórico aprovado e sua implementação não é apagada nem reescrita retroativamente.

Para **qualificação real do Sprint 1**, ADR-0024 substitui ADR-0023. O adapter BTG existente passa a ser `NON_CANONICAL_REFERENCE_IMPLEMENTATION` enquanto não houver decisão futura explícita de reativá-lo.

Nenhuma API key BTG deve ser adquirida ou provisionada para fechar o Sprint 1.

## Credenciais Cedro e DD-43

A API Market Data Cedro exige autenticação por usuário/senha e mantém sessão por cookie (`JSESSIONID`) segundo a documentação pública. Essas credenciais são credenciais **de market data**, não credenciais de corretora/trading.

Política:

- credenciais Cedro ficam fora do repositório e fora do chat;
- devem ser armazenadas apenas em GitHub Environment dedicado ao laboratório;
- o adapter S1 não aceita `user-identifier`, conta de corretora, `brokerServiceLogin` ou qualquer autenticação da API Trading;
- a sessão Market Data pode usar apenas `/SignIn` e superfícies de observação necessárias;
- qualquer endpoint `/services/negotiation/*`, API Trading, dados financeiros, garantias ou conta é proibido e deve ser coberto por NEG-CAP;
- cookie/sessão nunca é persistido em EvidenceArchive/AuditJournal, logs ou config.

## Primeiro laboratório

DD-68 continua válido sem alteração:

- família: `WIN`;
- candidato concreto explícito por sessão;
- confirmação point-in-time pelo provider antes da subscription;
- `trades` em realtime;
- zero candles no primeiro laboratório;
- sem ranking, fallback ou rollover automático.

O candidato `WINV26` continua apropriado para setembro/2026, mas só pode ser assinado se a Cedro confirmar sua disponibilidade no início da sessão.

## Uso de fontes gratuitas pós-trial

Após a qualificação realtime, pesquisa/replay futuro pode usar dados gratuitos B3 D-1/históricos e, quando tecnicamente apropriado, endpoints públicos sem token de WIN/WDO da brapi. Esses dados não substituem nem retroativamente reclassificam a prova realtime do Sprint 1.

## Critério de falha

Se o trial Cedro não oferecer efetivamente, para a credencial recebida, streaming realtime de negócios BM&F/WIN ou discovery suficiente para confirmar o contrato, a qualificação falha fechada e DD-60 deve ser reaberto novamente. Não é permitido degradar silenciosamente para EOD/delay e declarar PASS.

## Consequências

- não há custo financeiro para qualificar o Sprint 1;
- `0F-E` não é alterado nem enfraquecido;
- o trabalho funcional passa a ser um adapter Cedro estreito e read-only;
- a janela do trial só deve começar após CI/testes offline do adapter;
- Security Diff Scan oficial continua sendo gate independente;
- nenhuma decisão aqui autoriza Strategy, ML operacional, Paper, Risk, ordens, conta de corretora, ledger ou dinheiro real.
