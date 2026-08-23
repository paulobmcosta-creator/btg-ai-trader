# Protocolo 0E-G — Promoção, Paper Trading e Rejeição

- **Status:** Fechado tecnicamente no Sprint 0E
- **Data da baseline:** 2026-08-20
- **Consome:** ADR-0001, ADR-0007, ADR-0008, ADR-0010, ADR-0011, ADR-0016, ADR-0017, ADR-0019, ADR-0020, ADR-0021, ADR-0022
- **Subordinado a:** QPI-01, QPI-03, QPI-04, QPI-05, QPI-06, QPI-08, QPI-09, QPI-10, QPI-11, QPI-12, QPI-13, QPI-14, QPI-15

---

## 1. Finalidade e Escopo

O Protocolo 0E-G estabelece as regras de governança, transição de estado e critérios de admissibilidade para responder às seguintes questões:
1. Quando um candidato avaliado pode avançar da pesquisa histórica para a etapa prospectiva de Paper Trading?
2. Quando um candidato exige evidência empírica adicional (*More Evidence Required*)?
3. Quando uma hipótese ou estratégia deve ser rejeitada ou arquivada (*Rejected / Retired*)?
4. O que o Paper Trading deve demonstrar além do que o Backtest é capaz de comprovar?
5. Quais classes de bloqueadores materiais impedirão futuramente qualquer consideração de operação em ambiente real (*Live Trading*)?

---

## 2. Semântica de Promoção e Máquina de Estados

### 2.1. Definição de Promoção Quantitativa
Decisão governada e auditável de permitir que um candidato avance de uma classe de evidência histórica para outra classe de avaliação mais próxima das condições prospectivas de uso (ex.: de Backtest protegido para Paper Trading).

> **Invariante central:** Promoção quantitativa é estritamente uma progressão entre classes de evidência empírica. Ela **nunca concede autoridade econômica ou autorização de trading**.

### 2.2. Separação entre Avaliação e Promoção
Uma avaliação técnica favorável (`StrategyEvaluation = FAVORABLE`) é condição necessária, mas não suficiente para a promoção. A promoção exige o cumprimento cumulativo de requisitos de governança, completude de evidência e viabilidade operacional em Paper.

### 2.3. Máquina Conceitual de Estados de Candidatos
O ciclo de vida de um candidato segue a máquina de estados conceitual:

```text
                  RESEARCH_CANDIDATE
                          |
                          v
               QUANTITATIVELY_EVALUATED
                          |
         +----------------+----------------+----------------+----------------+
         |                |                |                |                |
         v                v                v                v                v
  INVALID_EVIDENCE    REJECTED      MORE_EVIDENCE     RESEARCH_ONLY   PAPER_ELIGIBLE
                                      REQUIRED                               |
                                                                             v
                                                                           PAPER
                                                                             |
                                                      +----------------------+----------------------+
                                                      |                      |                      |
                                                      v                      v                      v
                                                 PAPER_FAILED        PAPER_INCONCLUSIVE       PAPER_EVIDENCE
                                                                                                ACCEPTABLE
```

*Nota:* É proibido o uso de status genéricos e ambíguos como `APPROVED`.

### 2.4. Distinção Crucial: INVALID vs REJECTED vs INCONCLUSIVE
- **`INVALID_EVIDENCE`:** A avaliação metodológica foi violada (vazamento temporal, contaminação de dados ou falha epistemológica). A evidência é nula e não pode ser interpretada.
- **`REJECTED`:** A avaliação foi metodologicamente válida, mas o candidato apresentou resultado econômico desfavorável, risco inaceitável ou fragilidade estrutural.
- **`MORE_EVIDENCE_REQUIRED` / `INCONCLUSIVE`:** A avaliação foi válida, mas o volume de dados, número de trades ou precisão estatística é insuficiente para uma decisão afirmativa.
- **`RESEARCH_ONLY`:** O candidato possui valor científico ou explicativo relevante, mas não atende aos critérios de progressão evidenciária para Paper.

---

## 3. Requisitos para Elegibilidade a Paper Trading

Para que um candidato atinja o estado `PAPER_ELIGIBLE`, é obrigatório o atendimento cumulativo de dez classes de requisitos (sem compensação entre elas):

1. **Validade Metodológica:** Ausência de blocker metodológico aplicável.
2. **Completude de Evidência:** Todas as classes de evidência materialmente necessárias à claim foram avaliadas.
3. **Evidência Histórica Protegida:** Existe evidência temporalmente protegida apropriada à claim.
4. **Admissibilidade Econômica:** Resultados econômicos foram avaliados líquidos das fricções materiais aplicáveis e não apresentam blocker incompatível com Paper.
5. **Evidência de Risco:** Downside, tail e path risk materialmente pertinentes foram avaliados e não apresentam blocker incompatível com Paper.
6. **Robustez:** Fragilidade temporal, paramétrica, de regime e de execução materialmente pertinente foi avaliada; eventual fragilidade permanece explicitamente incorporada à decisão.
7. **Comparator Evidence:** A claim pertinente foi confrontada com comparator/baseline apropriado. Superioridade só é requisito quando a própria claim reivindica superioridade ou valor incremental.
8. **Selection Burden:** Multiplicidade e histórico material de busca foram incorporados à interpretação.
9. **Candidate Identity:** Identidade, versão e elementos quantitativamente materiais estão suficientemente resolvidos e versionados antes de Paper (mudanças comprovadamente não materiais permanecem possíveis com rastreabilidade de proveniência).
10. **Paper Executability:** A claim pode ser exercitada prospectivamente no profile Paper.

---

## 4. O Protocolo de Paper Trading

### 4.1. Definição de Paper Trading
Avaliação prospectiva na qual o núcleo decisório do sistema opera sobre dados de mercado recebidos contemporaneamente em tempo real, gerando decisões reais do sistema (`StrategyDecision`, `TradeIntent`, `RiskDecision`, `OrderPlan`), porém **sem qualquer exposição financeira real ou envio de ordens a contas reais** (*non-funded*).

### 4.2. O que o Paper Trading Deve Comprovar (além do Backtest)
- Comportamento estritamente prospectivo sem acesso a dados futuros;
- Resiliência à chegada assíncrona de eventos e flutuações de latência computacional;
- Capacidade de operar sob a mistura de regimes de mercado do tempo presente;
- Continuidade operacional, ausência de erros críticos e estabilidade de estado;
- Discrepância real entre o modelo de execução simulado no backtest e as cotações contemporâneas observadas.

### 4.3. O que o Paper Trading NÃO Comprova Automaticamente
- Preenchimento garantido de ordens no book da corretora ou da bolsa;
- Prioridade real em filas de ordens e impacto de mercado da própria ordem;
- Confirmação de regras de liquidação, margem e garantias da corretora;
- Prontidão operacional completa (*Operational Readiness*) para infraestrutura de produção;
- Suficiência do plano de Disaster Recovery e reconciliação de conexões reais;
- Equivalência com ambiente de negociação real (*Live Trading*).

### 4.4. Compatibilidade Distribucional Backtest ↔ Paper
A compatibilidade entre o Backtest e o Paper Trading não exige identidade pontual de P&L, mas sim conformidade estrutural e distribucional nas dimensões materialmente aplicáveis ao candidato e à claim avaliada:
- Frequência de oportunidades e taxa de decisões `NO_TRADE`;
- Distribuição de scores e probabilidades geradas pelos modelos (quando a estratégia utilizar modelos probabilísticos/scores);
- Frequência e horários de propostas de trade;
- Níveis de spread observados em relação aos modelados;
- Discrepância de slippage e latência realizada (qualificadas pela proveniência da observação);
- Comportamento sob diferentes regimes de volatilidade e mercado (quando materialmente pertinente à claim).

> **Regra de Discrepância:** Discrepâncias materiais observadas em Paper Trading constituem evidência empírica legítima e não podem ser silenciadas ou ajustadas no passado. A calibração de novos modelos de execução gera uma nova versão de simulador para experimentos futuros.

---

## 5. Classes de Bloqueadores para Produção Futura (Live Trading)

A transição futura para qualquer operação com dinheiro real permanece absolutamente bloqueada nesta etapa. No futuro, a autorização exigirá a superação cumulativa de dez classes de bloqueadores (*Blocker Classes*):

- **L1 — Validade Quantitativa:** Ausência de qualquer contaminação de dados, look-ahead bias ou falha metodológica em toda a cadeia de pesquisa.
- **L2 — Evidência Econômica:** Demonstração de edge líquido robusto após todos os custos e estresses de mercado.
- **L3 — Risco e Dimensionamento:** Políticas de dimensionamento (*sizing*), drawdown máximo e limites de exposição formalmente aprovados.
- **L4 — Evidência de Paper Trading:** Conclusão satisfatória do período de Paper Trading com suficiência amostral, compatibilidade com o backtest e ausência de erros críticos.
- **L5 — Suficiência Pré-Produção do Risk Engine:** Validação completa e independente de todos os mecanismos de veto, limites diários (*daily loss*), circuit breakers, kill switch e fail-safe em conformidade com o Gate E do Plano Mestre.
- **L6 — Recovery e Reconciliação:** Capacidade demonstrada de reconstruir estado após falhas de processo, tratar resultados desconhecidos (`UNKNOWN`) e reconciliar divergências sem duplicação de compromissos.
- **L7 — Prontidão Operacional (Operational Readiness):** Avaliação de prontidão favorável para todas as capacidades críticas de runtime.
- **L8 — Segurança e Auditoria:** Ausência de vulnerabilidades críticas, segredos versionados e garantia de rastreabilidade causal integral.
- **L9 — Execução e Conectividade:** Validação de adaptadores de conectividade sem introdução de ordens reais desgovernadas.
- **L10 — Aprovação Humana Formal:** Revisão formal por operadores responsáveis e autorização humana explícita documentada.

---

## 6. Protocol Requirements

1. **PR-0E-G-01:** A concessão de status `PAPER_ELIGIBLE` exige a verificação formal e não compensatória das dez classes de elegibilidade.
2. **PR-0E-G-02:** Antes do início de Paper Trading confirmatório, os elementos quantitativamente materiais do candidato devem estar pré-resolvidos e versionados (*candidate freeze*), com rastreabilidade de proveniência para eventuais mudanças não materiais.
3. **PR-0E-G-03:** Qualquer alteração material durante o Paper Trading encerra a partição de avaliação e inicia uma nova linhagem.
4. **PR-0E-G-04:** O encerramento de Paper Trading exige a emissão do artefato semântico `PaperGateAssessment`.
5. **PR-0E-G-05:** O status de elegibilidade de promoção não é perpétuo, estando sujeito a revalidação ou revogação quando versão, premissas, domínio, políticas ou outras condições materiais mudarem; prazos de expiração cronológica permanecem como parâmetro de policy.

---

## 7. Hard Quantitative Invariants (G-HQI-01 a G-HQI-50)

| ID | Hard Quantitative Invariant | Mapeamento QPI |
|---|---|---|
| **G-HQI-01** | Promoção quantitativa entre etapas de pesquisa nunca cria autoridade operacional ou econômica de trading. | QPI-13 |
| **G-HQI-02** | Avaliação técnica favorável da estratégia não promove o candidato automaticamente. | QPI-13, QPI-15 |
| **G-HQI-03** | Todo status de aprovação deve identificar explicitamente o gate normativo específico ao qual se refere. | QPI-13, QPI-15 |
| **G-HQI-04** | As disposições `INVALID`, `REJECTED` e `INCONCLUSIVE` permanecem conceitualmente distintas. | QPI-10, QPI-11 |
| **G-HQI-05** | Evidência metodologicamente inválida não pode sustentar nenhuma decisão de promoção. | QPI-10, QPI-01 |
| **G-HQI-06** | Valor explicativo para pesquisa científica (*RESEARCH_ONLY*) não equivale a elegibilidade para promoção. | QPI-01, QPI-13 |
| **G-HQI-07** | A elegibilidade para Paper Trading exige atendimento cumulativo de todas as classes materiais obrigatórias. | QPI-15, QPI-01 |
| **G-HQI-08** | Bloqueadores rígidos de promoção (*hard blockers*) são estritamente não compensatórios. | QPI-10, QPI-15 |
| **G-HQI-09** | O status de promoção é específico à versão/configuração avaliada e não se transfere automaticamente para versões materialmente modificadas. | QPI-12 |
| **G-HQI-10** | O Paper confirmatório exige que o candidato e o desenho materialmente relevantes estejam pré-resolvidos e versionados antes da observação dos resultados. | QPI-12, QPI-03 |
| **G-HQI-11** | Qualquer alteração material durante o período de Paper Trading cria uma nova fronteira de evidência. | QPI-12, QPI-03 |
| **G-HQI-12** | O Paper Trading opera com decisões prospectivas reais do sistema sem risco de capital real (*non-funded*). | QPI-14 |
| **G-HQI-13** | O Paper Trading deve executar a estratégia candidata exata, sendo proibido o uso de substitutas favoráveis. | QPI-14, QPI-12 |
| **G-HQI-14** | A validade empírica de Paper Trading é restrita ao que o ambiente é capaz de observar contemporaneamente. | QPI-14, QPI-01 |
| **G-HQI-15** | A execução em Paper Trading não equivale por presunção à execução em ambiente de produção real (*Live*). | QPI-14, QPI-05 |
| **G-HQI-16** | A compatibilidade entre Backtest e Paper Trading é de natureza estrutural e distribucional. | QPI-01, QPI-14 |
| **G-HQI-17** | Discrepâncias materiais observadas em Paper Trading permanecem registradas como evidência empírica. | QPI-14, QPI-12 |
| **G-HQI-18** | A adaptação ou ajuste da estratégia motivada por dados de Paper Trading consome a independência desses dados. | QPI-03, QPI-14 |
| **G-HQI-19** | A suficiência de Paper Trading não é definida unicamente por dias de calendário, mas por volume informacional. | QPI-01, QPI-14 |
| **G-HQI-20** | O Paper Trading avalia todas as decisões geradas, inclusive a taxa e oportunidade de decisões `NO_TRADE`. | QPI-09, QPI-14 |
| **G-HQI-21** | A ocorrência de erro crítico não resolvido durante o Paper Trading bloqueia a progressão do candidato. | QPI-10, QPI-15 |
| **G-HQI-22** | O impacto de falhas e erros operacionais deve ser avaliado no escopo específico em que ocorreram. | QPI-01 |
| **G-HQI-23** | Estabilidade operacional em Paper Trading não equivale a prontidão operacional (*readiness*) para Live. | QPI-14, QPI-13 |
| **G-HQI-24** | O Paper Trading não pode contornar ou desabilitar verificações de risco para inflar o volume de trades. | QPI-08, QPI-14 |
| **G-HQI-25** | Análises contrafactuais em Paper Trading são ferramentas exploratórias e não substituem o comportamento canônico. | QPI-14, QPI-01 |
| **G-HQI-26** | Toda decisão de promoção deve registrar sua proveniência, evidências e responsáveis de forma auditável. | QPI-12, QPI-13 |
| **G-HQI-27** | As políticas e regras de aprovação de gates possuem identidade de versão e vigência temporal. | QPI-12, QPI-15 |
| **G-HQI-28** | O status de elegibilidade de um candidato não é perpétuo e deve poder ser revalidado ou revogado quando versão, premissas, domínio, políticas ou outras condições materiais mudarem. | QPI-13 |
| **G-HQI-29** | Novas evidências materiais desfavoráveis podem suspender ou revogar o status de elegibilidade. | QPI-13, QPI-15 |
| **G-HQI-30** | A rejeição formal de um candidato não apaga seu histórico de desenvolvimento e linhagem de pesquisa. | QPI-04, QPI-12 |
| **G-HQI-31** | Falhas repetidas de candidatos de uma mesma família permanecem registradas para controle de multiplicidade. | QPI-04 |
| **G-HQI-32** | A operação em ambiente real (*Live*) exige a superação formal de todas as classes de bloqueadores aplicáveis. | QPI-15, QPI-13 |
| **G-HQI-33** | Os gates de evolução do sistema são independentes e estritamente conjuntivos. | QPI-15 |
| **G-HQI-34** | O Paper Trading deve confrontar os resultados observados contra as expectativas ex ante do backtest. | QPI-14, QPI-01 |
| **G-HQI-35** | Mudança estrutural no regime de mercado (*domain shift*) pode limitar a validade da evidência de Paper. | QPI-01, QPI-14 |
| **G-HQI-36** | Regras de interrupção (*stopping rules*) de Paper Trading devem ser pré-especificadas no desenho do teste. | QPI-14 |
| **G-HQI-37** | A interrupção de Paper Trading por motivos de segurança operacional prevalece sobre a suficiência amostral. | QPI-15, QPI-14 |
| **G-HQI-38** | Resultado financeiro positivo em Paper Trading, isoladamente, é insuficiente para satisfazer o Paper Gate. | QPI-07, QPI-14 |
| **G-HQI-39** | O Paper Trading gera novos artefatos de evidência de forma append-only, sem reescrever o histórico. | QPI-12, QPI-14 |
| **G-HQI-40** | O diagnóstico de falha em Paper Trading exige demonstração empírica baseada em dados e logs. | QPI-01, QPI-14 |
| **G-HQI-41** | Candidato materialmente modificado após falha em Paper Trading deve retornar aos gates do pipeline aplicáveis antes de reivindicar nova progressão. | QPI-03, QPI-10 |
| **G-HQI-42** | A aprovação humana em comitê não tem poder para validar evidência quantitativamente contaminada. | QPI-10, QPI-13 |
| **G-HQI-43** | Suposta urgência comercial ou de mercado não autoriza o bypass ou flexibilização de gates normativos. | QPI-15, QPI-10 |
| **G-HQI-44** | O estado de promoção é plenamente revogável a qualquer momento diante de novas evidências. | QPI-13, QPI-15 |
| **G-HQI-45** | Estar elegível para uma etapa não equivale a ter iniciado ou concluído a referida etapa. | QPI-13, QPI-11 |
| **G-HQI-46** | O sucesso na execução operacional de Paper Trading não comprova o mérito quantitativo da estratégia. | QPI-08, QPI-14 |
| **G-HQI-47** | A observação de baixo risco em Paper Trading não substitui a necessidade dos controles do Risk Engine. | QPI-08, QPI-14 |
| **G-HQI-48** | Gates posteriores adicionam requisitos de segurança e não atenuam exigências não cumpridas em gates prévios. | QPI-15 |
| **G-HQI-49** | Candidatos derivados de uma estratégia herdam sua linhagem de pesquisa, mas não seu status de promoção. | QPI-12, QPI-13 |
| **G-HQI-50** | O escopo de promoção não pode exceder as configurações, instrumentos e condições efetivamente testadas. | QPI-01, QPI-13 |

---

## 8. Policy / Experiment Parameters (Decisões Deliberadamente Adiada)

Permanecem abertos e parametrizáveis por experimento:
- Número mínimo exigido de pregões e oportunidades de decisão em Paper Trading;
- Limiares quantitativos de tolerância a discrepâncias entre Backtest e Paper;
- Tolerâncias máximas aceitáveis para slippage e latência de processamento;
- Prazos de validade temporal (*expiry*) e critérios de vigência de status de promoção definidos por policy;
- Critérios quantitativos para parada de emergência (*safety stop*) em Paper;
- Formato físico de relatórios de auditoria e telas de acompanhamento.

---

## 9. Gates Internos do Bloco 0E-G

- **0E-G1:** Semântica de promoção como progressão evidenciária sem autoridade de trading.
- **0E-G2:** Distinção entre disposição de avaliação técnica e decisão de promoção.
- **0E-G3:** Máquina de estados clara e prevenção de status ambíguos.
- **0E-G4:** Cumprimento cumulativo das dez classes de elegibilidade para Paper.
- **0E-G5:** Pré-resolução e versionamento dos elementos materialmente relevantes antes do início de Paper Trading.
- **0E-G6:** Execução prospectiva com decisões reais e sem capital real (*non-funded*).
- **0E-G7:** Critérios de compatibilidade distribucional Backtest ↔ Paper.
- **0E-G8:** Suficiência informacional de dados em Paper.
- **0E-G9:** Tratamento de erros críticos e estabilidade.
- **0E-G10:** Consumo de independência em adaptações durante o teste.
- **0E-G11:** Mecanismos de expiração e revogação de elegibilidade.
- **0E-G12:** Formalização das dez classes de bloqueadores para produção futura (*Live*).
- **0E-G13:** Fronteira de governança e autorização humana explícita.
- **0E-G14:** Conformidade cruzada com 0E-A a 0E-F.
- **0E-G15:** Conformidade integral com o Plano Mestre e ADRs 0001 a 0022.
