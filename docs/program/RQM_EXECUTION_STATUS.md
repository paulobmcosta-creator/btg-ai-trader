# RQM execution status — snapshot de branches

Esta matriz registra evidência parcial, não fechamento de RQM, conformidade das 118 cláusulas ou aceitação S1. PARTIAL = implementação/teste limitado ao escopo citado; NOT_IMPLEMENTED = obrigação sem implementação/evidência direta identificada. Nenhuma linha é PASS de gate. A norma integral permanece [0F-E](../foundation/0F-E_sprint1_entry_contract.md), blob b04901dcc5612d3d418a6603a3a51a8e6e18ae08.

## Fontes exatas

| Ref | PR / head | CI |
|---|---|---|
| A | #10 / 5158dc3375fd9ed0a311dd745a981fadf2ea643a | 34780036474; 45 testes |
| B | #12 / a594a85cc41efab773e5d56d68560f3d281eda19 | 34780412293; 70 testes incluindo A |
| C | #15 / 146bec8a5a63255cd710c78ad6f663710d5cf72e | 34780999514; 69 testes incluindo A |
| H | #14 / 40a9b5788504dd8620fab74f6c04d4618422217e | 34780944239; 83 testes incluindo A |
| F | #13 / 99714c4df1abbb58daca9f9c19c5eb4737e2c316 | 34780763204; 7 checks |
| R | #9 / ad969b48e0cfbc5e942755cbbebeab89e5085aa4 | 34779661666; pesquisa isolada |
| M | #11 / 8c81980205a9b934af39614b67083a03b6695f6b | 34780543045; spike isolado |

CI indicada é evidência por SHA. Não somar suítes: B/C/H são branches irmãs sobre A, não composição integrada. R não integra S1; F verifica documentos, não comportamento RQM. M não integra dependências S1. Reviews C/H ainda pendentes no snapshot consultado; esta matriz não substitui revisão.

Paths relativos ao repositório, resolvidos no SHA da ref:
- A: `src/btg_ai_trader/observer/{temporal,values,market,envelope,identity}.py`; teste D = `tests/observer/test_domain.py`.
- B: `src/btg_ai_trader/observer/{instruments,provider}.py`; teste B = `tests/observer/test_registry_provider.py`.
- C: `src/btg_ai_trader/observer/{provenance,lineage}.py`; teste C = `tests/observer/test_provenance.py`.
- H: `src/btg_ai_trader/observer/health.py`; teste H = `tests/observer/test_health.py`.

## Obrigações e lacunas

| RQM | Status | Evidência direta / limite |
|---|---|---|
| RQM-001 | PARTIAL | A temporal/D: eixos separados; falta fluxo de ingestão. |
| RQM-002 | PARTIAL | A temporal/D: rejeita naive/não UTC; calendário/conversão B3 ausentes. |
| RQM-003 | PARTIAL | A values/D: MissingReason preservado; ingestão ausente. |
| RQM-004 | PARTIAL | A values/D: Decimal zero distinto de missingness. |
| RQM-005 | PARTIAL | A market/D: volume zero preservado; ausência de tick no fluxo não testada. |
| RQM-006 | PARTIAL | A envelope/D: ordem desconhecida não sintetizada; fluxo ausente. |
| RQM-007 | NOT_IMPLEMENTED | Sem deduplicação idempotente de eventos. |
| RQM-008 | PARTIAL | A envelope/D: envelope v1; metadados de captura ainda não integrados. |
| RQM-009 | PARTIAL | A envelope/D: sequence exige scope; sem fonte real. |
| RQM-010 | PARTIAL | A envelope/D: versões desconhecidas rejeitadas; sem serialização. |
| RQM-011 | PARTIAL | A envelope/D: correlation/causation não sintetizados. |
| RQM-012 | PARTIAL | C provenance/C: inputs/manifests imutáveis; sem arquivo auditável real. |
| RQM-013 | PARTIAL | C provenance/C: aliases/hash abreviado rejeitados; bytes não verificados. |
| RQM-014 | PARTIAL | C lineage/C: filtering N→M; pipeline/raw archive ausentes. |
| RQM-015 | PARTIAL | C provenance/C: restart novo RunId e colisão rejeitada; sem processo real. |
| RQM-016 | PARTIAL | C provenance/C: RESUMES_FROM tipado; sem recovery integrado. |
| RQM-017 | PARTIAL | C provenance/C: contexto run/code/config/provider; referências só sintáticas. |
| RQM-018 | PARTIAL | C provenance/C: labels restritos/sem payload config; logs/scan secretos ausentes. |
| RQM-019 | PARTIAL | C lineage/C: DAG e ciclos rejeitados em permutações; grafo só em memória. |
| RQM-020 | PARTIAL | A identity/D+B instruments/B: IDs/papéis distintos; registry em memória. |
| RQM-021 | PARTIAL | A/B modelos passivos; não há teste NEG-CAP sistêmico de executabilidade. |
| RQM-022 | PARTIAL | H health/H: timeout/staleness por fixtures; sem heartbeat/feed real. |
| RQM-023 | PARTIAL | H health/H: elapsed monotônico scoped; não mede latência real de captura. |
| RQM-024 | PARTIAL | B provider/B: FidelityMode/resolução/UNKNOWN; garantia da fonte não verificada. |
| RQM-025 | NOT_IMPLEMENTED | Sem canal de quarantine ou fluxo de isolamento. |
| RQM-026 | NOT_IMPLEMENTED | Sem classificação de late arrivals no fluxo. |
| RQM-027 | NOT_IMPLEMENTED | Sem fila finita/backpressure/load test. |
| RQM-028 | PARTIAL | B provider/B: Protocol só de metadados; subscrição/adapter ausentes. |
| RQM-029 | NOT_IMPLEMENTED | Sem persistência append-only de observações. |
| RQM-030 | NOT_IMPLEMENTED | EvidenceArchive/AuditJournal não implementados. |
| RQM-031 | PARTIAL | A market/D+C lineage/C: originais imutáveis; correção persistida ausente. |
| RQM-032 | PARTIAL | H health/H: três dimensões distintas; runtime integrado ausente. |
| RQM-033 | PARTIAL | H health/H: heartbeat vivo não implica readiness; avaliação pura. |
| RQM-034 | PARTIAL | H health/H: transição imutável observável; journal auditável ausente. |
| RQM-035 | PARTIAL | Modelos passivos A/B/C/H; scan e dez testes NEG-CAP completos pendentes. |
| RQM-036 | NOT_IMPLEMENTED | Sem prova sistêmica das 11 condições; SDK dual-use só no spike M. |
| RQM-037 | PARTIAL | Modelos A/B sem autoridade financeira; teste de fluxo integrado ausente. |
| RQM-038 | PARTIAL | A market/D: intervalo/finalidade/disponibilidade e limites temporais. |
| RQM-039 | NOT_IMPLEMENTED | Lineage C não herda restrições temporais; clock R não prova RQM S1. |
| RQM-040 | PARTIAL | B instruments/B: resolução valid/known scoped; discovery/futuros real ausente. |
| RQM-041 | PARTIAL | C provenance/C: referências input/config; sem hash de bytes/config/reprocessamento. |

Security Diff Scan oficial, suíte NEG-CAP integral, streaming, quarantine, archive, configuração concreta e integração permanecem pendentes. Tabelas/counters F não demonstram implementação. DD-60 segue indefinido; import MT5 M não prova as onze condições nem autoriza conexão.
