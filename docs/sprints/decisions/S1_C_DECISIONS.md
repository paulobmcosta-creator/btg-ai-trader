# S1-C — Decisões de proveniência pura

- Data: 2026-09-13.
- Estado: DECISIONS_RECORDED_BEFORE_FIRST_MATERIAL_DEPENDENCY; implementação parcial sujeita a revisão e checks.
- Base: `5158dc3375fd9ed0a311dd745a981fadf2ea643a`, PR #10.
- Autoridade: mandato remoto reconciliado em [PROGRAM_EXECUTION](../../program/PROGRAM_EXECUTION.md).
- Fontes: ADRs [0013](../../adr/0013-observability-decision-provenance-and-traceability.md), [0015](../../adr/0015-refinement-event-envelope-processing-context-and-versioning.md), [0021](../../adr/0021-refinement-provenance-runs-capture-and-lineage.md), [0F-E](../../foundation/0F-E_sprint1_entry_contract.md) RQM-012..019/041, S1-EC-086/087/088/107.

## Decisões anteriores ao código

| DD | Escolha física deste incremento | Evidência prevista |
| --- | --- | --- |
| DD-01 (extensão) | RunId, ArtifactId, ReceiptId e LineageRecordId reutilizam wrappers frozen de UUID canônico. Restart usa UUID4 novo e relação RESUMES_FROM; colisão com predecessor é rejeitada, nunca reutilizada. | Parsing herdado, IDs distintos, teste adversarial de colisão no restart. |
| DD-40 | RunManifest frozen contém RunId, início UTC, code revision, config hash, tuple de inputs declarados e relação opcional. Terminalidade fica em RunCompletionRecord separado. CaptureContext e ProcessingReceipt são objetos separados do fato externo. | Imutabilidade, contextos explícitos, múltiplos receipts para a mesma identidade externa. |
| DD-41 | CodeRevision exige Git SHA completo lowercase de 40 hex; ConfigHash e ContentHash exigem SHA256 completo lowercase de 64 hex. Aliases, abreviações e valores inválidos são rejeitados. Callers fornecem referências resolvidas; este lote não consulta Git nem calcula hashes. | Testes de aliases e formatos, propagação exata das referências. |

DD-03 continua dataclasses stdlib frozen/slots e validação explícita, sem dependências novas. Não se escolhe formato de serialização DD-02, mecanismo de configuração DD-65, artifact registry DD-17, storage DD-20/21 ou secrets DD-43. Receber um hash de configuração não é implementar configuração. Nenhum ADR material é aprovado implicitamente; bifurcação normativa deve parar para classificação.

## Concretizações e fronteiras

- Start/restart recebem explicitamente contexto resolvido, inputs e timestamp UTC; não herdam silenciosamente configuração antiga. Restart não antecede início do predecessor. Completion separado não antecede início quando criado pela factory que recebe o manifesto.
- InputIdentity vincula EventId externo ou ArtifactId a ContentHash. Declarar um input no manifesto não comprova seu processamento efetivo; ProcessingReceipt registra input × run × component/stage e tempos por componente, sem mutar ou renomear o fato externo.
- Receipts e CaptureContext não são inseridos no envelope neste incremento. O mesmo EventId pode ter receipts de múltiplos runs, preservando identidade e hash.
- Campos de referência são tipados; não há config payload, dict genérico de metadados, credencial, URL ou secret value. ProvenanceLabel é nome lógico limitado a 64 caracteres lowercase, sem URLs, caminhos, espaços ou pares chave/valor. Isso não é scanner de segredos: callers continuam responsáveis por não passar segredos como nomes.
- ArtifactLineageRecord descreve derivação N→M com transformação tipada e roles opcionais de cardinalidade correspondente. Inputs e outputs são tuples; conjuntos vazios, repetição de identidade e self-derivation são rejeitados. Outputs derivados usam ArtifactId, nunca apropriam EventId externo.
- LineageGraph valida apenas o conjunto de registros fornecido em memória. Detecta ciclos globais independentemente da ordem, proíbe redefinir hash para a mesma identidade, duplicar record IDs ou reutilizar identidade já produzida. Acrescentar registro retorna novo grafo; falha preserva original.
- FILTERING/CLEANING são metadados de derivação, sem executar limpeza, apagar raw ou provar persistência. Relações N→M não significam contabilização financeira.
- Hashes/SHAs são validados sintaticamente; existência do commit, hash real dos bytes, completude de inputs, efetividade da captura e persistência não são comprovadas pelo DTO.
- Factory de restart é o caminho oferecido para alocar identidade; não existe registro persistente global de UUIDs, lifecycle operacional, coleta real, replay, provider, estratégia, risco, ledger ou execução.

## Rastreabilidade parcial

RQM-012/013/015/016/017/019 recebem tipos e testes puros. RQM-014 recebe metadados de derivação; preservação raw em storage permanece pendente. RQM-018 recebe superfície de campos sem consumo de credenciais, sem substituir auditoria de secrets ou Security Diff Scan. RQM-041 recebe identidade declarada de inputs e config hash, sem manifestos de sessão real. O conjunto não fecha esses requisitos integralmente nem satisfaz o gate do Sprint 1.

Testes preparados cobrem imutabilidade, aliases, restart/colisão, completion separado, múltiplos receipts, roles N→M, ciclos em todas as permutações do grafo fixture, alteração de hashes e preservação de originais. A validação deve ocorrer nos seis checks remotos herdados do PR #10. Resultados só valem para seu HEAD. Nenhuma execução local foi realizada.

Este registro deve preceder o código dependente no histórico Git. Snapshots normativos permanecem intactos. PR draft; sem merge, sem conclusão S1-C integral e sem claims financeiros.
