# S1-A — Decisões locais anteriores aos modelos de observação

- Data: 2026-09-13.
- Estado: DECISIONS_RECORDED_BEFORE_FIRST_MATERIAL_DEPENDENCY.
- Autoridade: mandato humano de execução autônoma reconciliado em `docs/program/PROGRAM_EXECUTION.md`; este registro não inventa aprovação de ADR nem adjudica gates.
- Base documental: `183203307169f41ce40e035fe19f1d0a570e3e16`.
- Escopo: primeiro incremento de modelos puros do Market Observer. Não conclui S1-A integralmente nem o Sprint 1.
- Fontes: [0F-E](../../foundation/0F-E_sprint1_entry_contract.md), [0F-B](../../foundation/0F-B_deferred_decision_register.md), ADRs [0003](../../adr/0003-event-envelope-causality-and-ordering.md), [0004](../../adr/0004-temporal-semantics-and-historical-fidelity.md), [0005](../../adr/0005-instrument-identity-lifecycle-and-rollover.md), [0015](../../adr/0015-refinement-event-envelope-processing-context-and-versioning.md), [0021](../../adr/0021-refinement-provenance-runs-capture-and-lineage.md), [0E-B](../../protocols/quantitative/0E-B-dataset-temporal-integrity.md).

## Decisões ativadas

| DD | Decisão local e justificativa | Primeira dependência | Verificação planejada |
| --- | --- | --- | --- |
| DD-01 | UUID em string canônica lowercase com hífens, dentro de value objects tipados distintos para EventId, CorrelationId, InstrumentFamilyId e TradableInstrumentId. Sem geração automática durante parsing. O símbolo externo continua separado, com provider e scope explícitos. | Tipos de identidade e envelope | Parsing válido/inválido, separação dos tipos e escopos. |
| DD-03 | `dataclasses` da biblioteca padrão, `frozen=True`, `slots=True`, validação explícita em construção e tipagem estrita. Nenhuma dependência nova. Alternativas de frameworks permanecem desnecessárias neste incremento. | Tick, Candle, tempos e envelope | Rejeição de tipos inválidos, mutação ordinária bloqueada, preservação do original. |
| DD-04 | Envelope v1 e payload schema v1 são campos independentes; somente inteiro exato 1 é aceito, rejeitando bool, versões desconhecidas ou incompatíveis. Não há migração, upcast ou fallback. Evolução posterior exige decisão explícita antes da dependência. | Envelope inicial | Versões inválidas rejeitadas em cada campo. |
| DD-67 | Campos de preço e quantidade recebem somente `Decimal` finito ou razão explícita de ausência; não há coerção de float/int/str nem arredondamento/quantização ocultos. Valores monetários não são calculados. Volume negativo é inconsistência estrutural. Limites empíricos de preço permanecem DD-79. | Tick e Candle | Precisão decimal preservada, rejeição de float, bool, NaN, infinito e volume negativo; zero distinto de ausência. |

As classificações epistêmicas canônicas de 0F-B são preservadas. DD-01/04/67 continuam decisões de concretização de itens `DELIBERATELY_DEFERRED`; DD-03 é `IMPLEMENTATION_DETAIL`. A implementação local não modifica contratos arquiteturais. Para DD-04/DD-67, cujo ADR é condicional no 0F-E, não se ativa neste lote mudança normativa ou arquitetura material: v1 apenas, sem migração ou política financeira. Caso isso mude, a funcionalidade dependente deve parar para classificação e o ADR exigido.

Este documento deve estar em commit ancestral ao primeiro código dependente, conforme S1-EC-044/045/046/048/049/069. O timestamp do commit e sua ancestralidade são a evidência da ordem; documentação posterior não substitui esse requisito.

## Concretizações de validação dentro de DD-03

- `MissingReason` distingue `UNKNOWN`, `NOT_PROVIDED` e `NOT_APPLICABLE`. Campos numéricos e temporais desconhecidos não são preenchidos com zero ou timestamps sintéticos. `None` é usado apenas para metadados opcionais de causalidade, IDs externos e sequência não fornecidos.
- Timestamps absolutos aceitos devem ter offset UTC explícito; naive ou offset não zero são rejeitados. O caller deve fazer conversão explícita antes da construção. Não há leitura de relógio, cálculo de latência ou escolha de calendário B3.
- `EventTime` exige três argumentos: valor, base e resolução da evidência. Base/resolução desconhecidas são razões explícitas de ausência; não se fabrica precisão.
- `ObservationTimes` separa event time, ingestion time, knowledge time e effective time. Não deduz um eixo do outro nem exige desigualdade numérica entre eles.
- Candle separa intervalo, estado de finalização, instante de finalização e disponibilidade. A disponibilidade de atualização aberta pode preceder o fim do intervalo. Finalização conhecida exige estado FINAL e não precede o fim do intervalo; estado FINAL pode ter instante desconhecido sem preenchê-lo.
- OHLC conhecidos devem respeitar low/high conhecidos; bid conhecido não excede ask conhecido. Não são aplicados filtros estatísticos ou thresholds empíricos. Dados rejeitados pela construção precisarão ter sua evidência bruta preservada pelo futuro canal de quarantine, ainda não implementado aqui.
- Envelope associa tipo de evento ao payload imutável correspondente. Source sequence exige scope e vice-versa; sequência e ordem de ingestão são inteiros não negativos explícitos, sem geração, comparação entre streams ou inferência a partir do timestamp.
- Fatos exógenos não recebem run_id, correlation_id ou causation_id sintéticos. Correlação, quando fornecida, tem tipo próprio. Não se implementa CaptureContext nem processamento/linhagem neste lote.
- ProviderInstrumentRef contém provider, scope e símbolo; os tipos não resolvem símbolos nem escolhem instrumento. A implementação do registry DD-58 permanece pendente.

Estas são representações físicas reversíveis dos contratos já existentes, não novas regras de pesquisa ou autorização financeira.

## Rastreabilidade e limites do incremento

| Cláusula | Exercício neste incremento | Limite explícito |
| --- | --- | --- |
| S1-EC-081/082 | Campos temporais separados, UTC, finalização/availability de candle | Não implementa derivação ancestral RQM-039 nem calendário DD-56. |
| S1-EC-083 | Missingness explícita e zero distinto de ausência | Não infere ausência de trades a partir de ausência de tick. |
| S1-EC-084 | Scope obrigatório para sequência; nenhuma ordem sintética | Deduplicação, backpressure e reordenação permanecem pendentes. |
| S1-EC-085 | Envelope v1, compatibilidade explícita, causalidade opcional | Sem serialização DD-02 ou migração DD-05. |
| S1-EC-089 | Tipos distintos de família, instrumento concreto e referência externa | Registry e resolução point-in-time DD-58/RQM-040 permanecem pendentes. |
| S1-EC-103 | Testes unitários determinísticos dos modelos | Evidência de execução será registrada pelos checks remotos no SHA final. |

Nenhuma capability de provider, rede, execução, ordens, risco, paper, ML, replay operacional ou persistência é introduzida. As 10 obrigações NEG-CAP completas não são reivindicadas por testes de DTOs. Permanecem pendentes runtime, provider/fakes, quarantine, provenance, persistência e todos os critérios XC-01..XC-11 que dependam desses componentes.

DD-02/20/21/22/26/33/36/37/40/41/43/54/56/57/58/59/60/61/62/65/68/79 não são resolvidas por este lote. Sua avaliação ocorrerá antes das respectivas primeiras dependências materiais.

## Validação e revisão

Testes planejados: `pytest tests/observer`, `ruff check src tests` e `mypy src tests` no ambiente Python 3.12 já declarado. Execução local não foi realizada: o fluxo autorizado é remoto via GitHub. Não afirmar sucesso até existir resultado dos checks no SHA do código.

A revisão deve conferir os arquivos alterados, as limitações acima, a ancestralidade deste registro e a ausência de dependências inesperadas. Este registro não modifica snapshots 0F-B/0F-E/0F-F. A [Issue #6](https://github.com/paulobmcosta-creator/btg-ai-trader/issues/6) continua como errata histórica de rastreabilidade; nenhuma correção retroativa foi aplicada.
