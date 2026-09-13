# ADR 0024 — Persistência técnica em arquivos imutáveis no Observer

- **Status:** Decidida para implementação limitada sob mandato remoto de 2026-09-13; revisão independente e promoção pendentes.
- **Estado:** Decisão in-sprint registrada antes do código; não representa aprovação humana de produção.
- **Data:** 2026-09-13.
- **Escopo:** Sprint 1, DD-02/DD-21 e mecanismo local DD-26.
- **Base:** `da6dde512beb95bc0a501f4bd65d2267f49443c0`, PR #15.

## Contexto

ADRs 0009/0018 distinguem EvidenceArchive, AuditJournal e snapshots; archived não significa admitted ou canonical. O contrato 0F-E §16 exige preservação append-only de evidência técnica, sem acesso ao ledger. S1-C fornece identidades e hashes tipados, mas não escreve nem verifica bytes. Este incremento cria um adapter de arquivos para laboratório e fixtures de CI, sem provider ou composição de ingestão.

## Problema

Preservar bytes raw e registros técnicos, identificar writes repetidos ou incertos por identidade lógica e impedir sobrescrita silenciosa, sem escolher banco ou importar semântica financeira.

## Alternativas consideradas

- Banco de dados: ativaria DD-20; desnecessário neste incremento.
- Um arquivo JSONL compartilhado: exige protocolo adicional de tail parcial e atomicidade de múltiplos registros.
- Arquivo completo por identidade, publicado por hardlink exclusivo: torna visível somente o conteúdo completo e não substitui destino existente; exige filesystem compatível.
- Rename com replace: rejeitado por permitir sobrescrita do histórico.

## Decisão

**DD-02:** envelope JSON UTF-8 versão 1, campos explícitos, keys ordenadas, separadores fixos, sem NaN, newline final. Bytes raw são base64 estrito, preservados exatamente; SHA256 do raw é calculado/verificado. Timestamps são UTC ISO explícito. Decodificação rejeita duplicação de keys, campos extras, versões desconhecidas, tipos incompatíveis e representação não canônica. Não é esquema universal para todos os eventos futuros.

**DD-21:** dois diretórios preexistentes controlados pelo caller, distintos e não aninhados: EvidenceArchive para raw e AuditJournal para fatos técnicos. IDs lógicos UUID canônicos tipados determinam nomes internos; caller não fornece nomes de arquivos. Roots/ancestrais symlink e aliases entre roots são rejeitados, e identidade física dos roots é revalidada nas operações. Isso depende de diretórios controlados, single-writer e ausência de mutação adversarial concorrente; não é proteção universal contra TOCTOU, junctions ou adulteração do filesystem.

EvidenceRecord contém identidade lógica de persistência separada da identidade EventId/ArtifactId, bytes e hash do input, CaptureContext opcional e relação explícita opcional com registro anterior. Ausência de captura é legítima, sem RunId fabricado. Archive preserva inclusive evidência não admitida; não resolve consistência global das identidades declaradas pela fonte. TechnicalJournalRecord aceita apenas tipos técnicos de lifecycle/anomalia, RunId, UTC e nome lógico limitado; não recebe dict genérico ou payload financeiro. Não se aloca JournalPosition neste lote: nem nome do arquivo nem ordem de leitura representa source sequence, event time ou cronologia global. Se introduzida no futuro, JournalPosition exigirá scope explícito.

**DD-26:** atomicidade da publicação de um arquivo. Escrever temporário no mesmo root, flush e fsync do arquivo, fechar e publicar com hardlink exclusivo; solicitar fsync do diretório após publicação. Nunca replace, update ou delete de registro canônico. Sem grupo/batch atômico. Temporários não publicados não são registros e sua limpeza é best-effort. Falta de suporte a hardlink ou sync falha explicitamente, sem fallback silencioso.

Mesmo ID e bytes canônicos idênticos retorna ALREADY_PRESENT, sem novo artefato. Mesmo ID com bytes diferentes, arquivo não regular, symlink, conteúdo malformado ou hash incorreto falha fechado. Erro durante/depois da tentativa de publicação produz outcome UNKNOWN com identidade/hash esperados, pois exceção não prova ausência do arquivo. Caller deve resolver pelo mesmo ID/hash; não há retry automático, nem geração de novo ID para contornar incerteza. Lookup confirma bytes encontrados ou ausência observada naquele instante; não prova durabilidade após queda de energia.

Receipt de publicação informa somente que as solicitações técnicas de sync retornaram, e receipt de idempotência informa somente bytes existentes verificados. Não promete atomicidade distribuída, tamperproof, fs guarantees universais ou permanência após power loss. O limite máximo de bytes de um registro é parâmetro obrigatório, inteiro positivo, validado, sem threshold operacional universal.

## Invariantes

- Histórico canônico nunca é sobrescrito pelo adapter; correção usa novo registro e relação explícita.
- Identidade lógica não é hash, path ou posição física; cópia não cria artifact novo.
- EvidenceArchive e AuditJournal permanecem separados, sem snapshot nem ledger.
- Erro/ambiguidade não é convertido em sucesso ou ausência.
- Stored/archived não implica admitted, tradable, current ou autoridade financeira.
- Reader valida conteúdo e identidade esperada, inclusive em resolução de resultado incerto.

## Consequências

O laboratório pode verificar roundtrip raw, detecção de corrupção, repetição idempotente e falhas de publicação em filesystem real de CI. Um arquivo por registro tem custo de diretórios e I/O; desempenho de captura real, concorrência e operação contínua não são alegados. Roots e bytes fornecidos devem ser controlados e livres de segredos; este adapter não é scanner de secrets.

O uso de fsync é exclusivamente flush técnico de arquivo unitário. **Não decide DD-24 econômico**, persist-before-act financeiro ou DurabilityRequirement financeiro. DD-20 (DB), DD-23 (WAL), DD-25 (replication), DD-27 (snapshots), DD-28 (retention), DD-54 (concorrência), DD-60 (provider) e DD-65 (configuração de execução) permanecem não selecionadas. Receber paths/limite via API não cria configuração de runtime.

## Verificação e limites da evidência

Testes com tmp_path e filesystem Ubuntu no GitHub Actions: roundtrip binário/UTC, JSON/versionamento estritos, roots separados, traversal via ID rejeitado, symlinks/aliases, idempotência, conflitos, corrupção, falha antes da publicação, exceção com publicação efetiva e resolução pelo mesmo ID/hash, falha de sync e preservação de originais. Seis checks herdados; somente resultados no HEAD exato são evidência. Não há execução no checkout físico do usuário.

RQM-029/030/031 recebem mecanismo técnico parcial; RQM-014/041 recebem preservação e vínculo de contexto em fixtures. Captura real, integração com admission/quarantine, reinício operacional, audit trail completo, capacidades negativas e Security Diff Scan continuam pendentes.

## Condições para reabrir

Primeiro requisito de múltiplos writers, filesystem sem as primitivas assumidas, batch atômico, DB, retenção, storage remoto ou garantia maior de durabilidade exige decisão própria e testes anteriores à dependência. Mudança normativa material segue ADR; não modifica os snapshots aprovados.

## Relação com outros ADRs

Concretiza o escopo técnico permitido por ADRs 0009/0018 e preserva identidades/proveniência de ADRs 0015/0021. Mantém as restrições de AGENTS.md, SAFETY.md e 0F-E. Não ativa o ADR 0023 de fila nem depende de ingestão.
