# ADR 0025 — Composição síncrona de fixtures do Observer

- **Status:** Decidida para implementação limitada sob mandato remoto de 2026-09-13; revisão independente e promoção pendentes.
- **Data:** 2026-09-13.
- **Escopo:** S1-F experimental, somente upstreams S1 no assembly37ff91bc9a86269cd68ddf5537b474f49b7d0510.
- **Base normativa:** ADR0003/0004/0006/0009/0012/0015/0018/0021/0023/0024 e contrato0F-E integral.

## Contexto e problema

Os incrementos existentes isolam raw, admission, registry, dedup, FIFO, health e armazenamento. Falta composição que preserve evidência, ordem e estado pendente quando a fila ou o filesystem recusa progresso. Arquivo publicado não significa admissão; receipt persistido não significa efeito operacional ou commit econômico.

## Alternativas consideradas

- Worker assíncrono/plugins/callbacks: não necessário ao laboratório e introduziria superfícies adicionais.
- Consumo antecipado de múltiplos frames: aumenta retenção pendente e permite perda sob falha.
- Um proprietário síncrono, um frame pendente, fila/canonical finitos: escolhido, com avanço explícito pelo caller.

## Decisões antes do código

DD54: execução de ingestão exclusivamente síncrona, single-owner, sem threads, tasks, concorrência ou callback injetável. advance lê no máximo um frame. Métodos não podem ser usados concorrentemente. Não é implementação de worker contínuo de produção.

DD68: execução experimental usa somente símbolos e canais declarados nas fixtures do laboratório. Nenhum ativo BTG, universo operacional ou timeframe padrão é selecionado. Candles carregam intervalo explícito no schema; ticks não recebem timeframe inventado. Fonte real/DD60 continua indefinida.

DD65: ObserverConfig recebe somente provider, capture_scope, queue_capacity, dedup_capacity, max_payload_bytes, clock_scope, heartbeat_timeout_ns, market_staleness_ns. Strings são nomes lógicos limitados, inteiros positivos estritos. from_mapping exige dict exato com todas as chaves e rejeita extras; não lê ambiente, arquivos de credenciais ou defaults. Configuração efetiva é a instância imutável; bytes canônicos JSON calculados dessa instância determinam ConfigHash real.

DD40/41: RunManifest com RunId explícito, started_at UTC e CodeRevision pin fornecido pelo caller; não há alegação de verificar os bytes Git no runtime. Manifesto serializado canonicamente com configuração integral e identidades/hash dos inputs declarados. CaptureContext deriva desse manifesto. O artefato de início é persistido antes do primeiro read; STARTED técnico referencia o manifesto. ID/hash de persistência e ArtifactId são distintos. ConfigHash autentica os bytes de configuração calculados, não garante segredo ausente em dados externos.

DD02/62: raw é EvidenceRecord com ArtifactId técnico alocado uma única vez, hash real e CaptureContext; não recebe EventId falso para dados ainda não decodificados. Decoder24 roda apenas depois de archive receipt. Resultado de admission, registry sidecar, dedup e late produzem artefato técnico de decisão com referências raw e valores tipados preservados. Registry só usa valid_at e knowledge_cutoff explícitos; UNKNOWN valid_at, NOT_FOUND/AMBIGUOUS ou ID conflitante bloqueiam admissão sem reescrever fato/EventId/instrument_id original. Lateness usa frontier explícito, nunca seleção/avanço implícito. O artefato preserva ingress knowledge, event/effective time e candle finality/finalized_at/available_at como sidecars. Processing completion e disponibilidade derivada permanecem explicitamente UNKNOWN neste audit receipt, nunca antecipadas a ancestrais; não é herança temporal genérica nem dataset disponível (RQM039 parcial).

Journal ganha OBSERVATION_RECORDED, nome técnico para registro da decisão/receipt, sem significado de ledger ou admissão econômica. Schema de arquivo permanece1 com novo valor do catálogo técnico; leitores antigos que não o conheçam rejeitam explicitamente, sem fallback. O journal referencia o artefato da decisão. O artefato registra health anterior, avaliação completa atual (sample/policy/phase/posture/readiness/reasons/watermarks/queue counters) e avaliação após commit de fila rotulada PLANNED. Não confunde plano persistido com commit efetivo em memória. A decisão/journal documentam o plano e sua evidência; não alegam atomicidade com fila em memória.

## Progresso e falhas

start persiste o mesmo manifesto e STARTED até sucesso; sem leitura da fonte antes disso. advance valida todos os argumentos, UTC/chronology/health e dependências antes read_next. Tipos concretos EXATOS FixtureMarketDataSource, TechnicalEvidenceStore e InstrumentRegistry são exigidos antes chamar métodos; não há slot de executor/plugin.

Cada frame pendente retém ingress, valid_at, cutoff, frontier, health sample, IDs e registros. Novas leituras são proibidas até concluir ou resolver o pendente. retry_pending não recebe contexto substituto. Raw, decisão e journal são writes distintos; falha em qualquer um conserva o estágio e o mesmo ID/hash. WriteUncertain só progride após resolução explícita desse ID/hash; ausência observada permite retry do MESMO registro, não outro ID.

NEW dedup e enqueue são estados staged, aplicados em memória somente após receipts da decisão/journal. Fila cheia registra pressão no estado limitado e retorna BACKPRESSURE conservando raw pendente; dedup não incorpora o item rejeitado. take pode drenar apenas sem pendente ou enquanto pendente aguarda capacidade; é transferência de ownership local, não processamento concluído. Não é permitido drenar durante writes staged, para evitar commit de snapshot antigo. Após take, retry pode aceitar uma única vez. CAPACITY_EXHAUSTED do dedup mantém pendente e bloqueia próximas leituras, sem evicção ou aumento automático.

DUPLICATE preserva incoming+canonical na decisão e não enfileira de novo. IDENTITY_CONFLICT e quarantine preservam causa/raw e não entram na FIFO. Unknown registry torna disposition não admitida; nenhuma identidade ou tempo é inferido. Quarantine é canal lógico typed separado do output admitido/FIFO, com referência ao raw; o mesmo archive técnico preserva todos os raws e não é um diretório de dados admitidos. Raw corrupto não encerra o feed quando sua quarantine foi persistida suficientemente para este contrato técnico.

Falha de storage coloca postura SAFE_HALT e bloqueia read; sucesso de retry não unlatch automaticamente. Health é avaliação passiva de sample explícito. Fonte com fidelity UNKNOWN força postura conservadora, assim como quarantine/bloqueio; fixture exhaustion não fabrica heartbeat ou mercado fresco. Nenhuma postura executa cancelamento/flatten.

## Invariantes e limites

- Nenhuma ordem, conexão de broker, credencial, Risk, Paper, estratégia, simulação econômica ou deploy.
- Um pending, fila e canonical finitos; não há lista ilimitada de receipts no runtime.
- Raw arquivado não é admitido; resolução registry é sidecar e nunca altera o fato.
- Writes não são transação multi-record; não existe exactly-once, recovery/restart automático ou garantia universal de power loss.
- IDs técnicos alocados não renomeiam EventId da fixture. Reinício requer RunId novo; este módulo não reconstrói pendentes após processo morto nem prova unicidade de RunId entre processos distintos.
- Hash/receipt confirmam somente bytes e escopo do adapter; readiness passiva não confere autoridade financeira.
- S1-F experimental não fecha41RQMs/118cláusulas/20NC/10NEG-CAP nem Security oficial.

## Verificação

GitHub Ubuntu temporário: manifesto antes read, hashconfig real, bad→good com bytes preservados; missing registry/tempo e conflitante; duplicate/identityconflict/lateUNKNOWN; backpressure→take→retry semduplicate/drop; falhas raw/decisão/journal e resolução de publicação incerta com mesmoID; rejeição de dependency ducktypes antes invocação; unknown config e chronologia inválida antes read; healthUNKNOWN e SAFE_HALT sem efeitos financeiros. Somente CI do HEAD exato é evidência.

## Consequências e condições para reabrir

O laboratório ganha composição verificável com bloqueios explícitos, mas não captura real ou recuperação durável de estado em memória. Concorrência, provider real, mudança de transporte, formato geral de mercado, tolerância a crash do processo, retention e qualquer capability financeira exigem decisões/gates próprios antes do código dependente.
