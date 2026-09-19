# Sprint 5 — ML Engine

```text
SPRINT_5_STATUS = FORMALLY_CLOSED
SPRINT_5_LIFECYCLE = FORMALLY_CLOSED
SPRINT_5_ENTRY_GATE = PASS
SPRINT_5_FUNCTIONAL_IMPLEMENTATION = COMPLETED
SPRINT_5_FINAL_VERDICT = PASS
CANONICAL_SPRINT_5_BRANCH = sprint/5-ml-engine
WORK_BRANCH = s5/00-full-ml-engine
CANONICAL_BASE_SHA = 560dd83cdfdd50084ae277083d9f8732e5296356
ISSUE = #77
PR = #78
MERGE_COMPLETED = YES
CANONICAL_MERGE_SHA = 8b09a34ecc7c3b0b180e30ada0702d22d61d96d2
POST_MERGE_S5_CI_RUN = 35473144900
POST_MERGE_UPSTREAM_RUN = 35473144855
INDEPENDENT_REAUDIT = PASS
PROMOTION_TO_SPRINT_6_GATE = YES
SPRINT_6_ENTRY_GATE = AUTHORIZED
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
```

## 1. Contexto e Linhagem Canônica

- **Repositório:** `paulobmcosta-creator/btg-ai-trader`
- **Base SHA Obrigatória:** `560dd83cdfdd50084ae277083d9f8732e5296356`
- **Branch Canônica:** `sprint/5-ml-engine`
- **Branch de Trabalho:** `s5/00-full-ml-engine`
- **Issue de Acompanhamento:** Issue #77
- **Classificação:** `RESEARCH_ML_ENGINE_AND_PREDICTIVE_CANDIDATE_EVALUATION`

O Sprint 4 (Statistical Baselines) foi formalmente aprovado e fechado no HEAD canônico `560dd83cdfdd50084ae277083d9f8732e5296356` (após o merge funcional aceito `0786ace3e6a83ecb23a508af860f43a2fd5d64e8` e validação pós-merge verde nos runs CI 35304136357 e Upstream 35304136369).

O Sprint 5 constrói uma camada de pesquisa para estimar e avaliar modelos de Machine Learning clássicos sob validação temporal causal, com isolamento epistemológico de teste protegido (Out-of-Sample), registro determinístico de proveniência e comparação rigorosa contra os baselines estatísticos do Sprint 4.

---

## 2. Escopo do Sprint 5

### Incluído no Escopo
1. **Feature Pipeline Causal e Determinística:**
   - Consumo exclusivo de `PredictionInput` derivado causalmente de `StatisticalSample`.
   - `FeatureSchema` imutável com tipos `NUMERIC`, `CATEGORICAL`, `BOOLEAN`.
   - Ordenação determinística de features.
   - Políticas explícitas de missingness (`REJECT`, `CONSTANT`, `INDICATOR`).
   - Políticas explícitas de categorias desconhecidas (`REJECT`, `DECLARED_FALLBACK`).
   - `FittedFeaturePipeline` ajustado exclusivamente no domínio de treino (`TRAINING_FIT`).
2. **Contrato de Alvo Explícito (`TargetContract`):**
   - Vinculação de semântica do alvo, horizonte e cutoff de conhecimento.
3. **Catálogo de Modelos Preditivos:**
   - Classificação/Probabilidade Binária: `LogisticRegressionCandidate`, `RandomForestClassifierCandidate`, `GradientBoostingClassifierCandidate`.
   - Regressão Contínua: `RidgeRegressionCandidate`, `RandomForestRegressorCandidate`, `GradientBoostingRegressorCandidate`.
   - Interface comum `PredictiveCandidate`.
4. **Semântica de Determinismo e RNG:**
   - Contexto de RNG explícito (`RNGContext`) para candidatos estocásticos.
   - Proibição de seleção de "melhor seed" (`BEST_SEED`).
   - Execução single-thread via `threadpoolctl` e `n_jobs=1`.
   - Conversão de métricas e previsões para `Decimal` via `NumericPolicy`.
5. **Fronteira de Entrada e Manifesto de Treinamento:**
   - `ModelTrainingInputBoundary` imutável e verificada.
   - Extração estrutural de `model_state_digest` (sem serialização executável insegura).
   - `ModelTrainingManifest` criptograficamente vinculado via SHA-256.
6. **Espaço de Busca Finito e Histórico:**
   - `ModelSearchSpace` finito e pré-declarado.
   - `ModelSearchHistory` append-only preservando tentativas e falhas.
7. **Seleção de Modelos e Avaliação Temporal:**
   - Seleção exclusivamente em `VALIDATION_SELECTION`.
   - Proteção estrita do conjunto `PROTECTED_TEST` contra vazamento e reúso indevido.
8. **Comparação com Baselines do Sprint 4:**
   - Paridade experimental estrita com os baselines determinísticos do S4.
9. **Métricas e Diagnósticos:**
   - Métricas binárias (Brier, LogLoss, ROC-AUC, ECE/MCE).
   - Métricas contínuas (MAE, MSE, RMSE, Mean Bias, R²).
   - Suporte a ablação de features (`FeatureAblationSpec`, `AblationResult`).
   - Disposição formal de avaliação (`ModelEvaluationDisposition`).
10. **Research Model Registry & Model Card:**
    - `ResearchModelRegistry` com registros imutáveis (`ModelRecord`).
    - `ModelCard` determinístico com escopo declarado `EVALUATION_SCOPE = MODEL`.
11. **Scanner Estático de Fronteiras:**
    - `scripts/check_s5_boundary.py` e `scripts/verify_s5_acceptance_symbols.py`.

### Excluído do Escopo (Proibições Absolutas)
- Strategy Engine, Signal Engine ou Risk Engine operacionais.
- Negociação real, paper trading ou autoridade financeira.
- APIs de corretora, ordens (`order_send`), cancelamento ou alteração de ordens.
- Mutação do `FinancialLedger`.
- Endpoints de serving de modelo (FastAPI, Flask, REST) ou deploy em produção.
- AutoML, busca bayesiana adaptativa ou busca infinita.
- Redes neurais, deep learning (PyTorch, TensorFlow) ou Reinforcement Learning.
- Dependências com custo financeiro adicional (`ADDITIONAL_RECURRING_COST = ZERO`).
- Serviços externos de experiment tracking (MLflow, Weights & Biases).
- Desserialização executável arbitrária (`pickle.loads`, `joblib.load`).

---

## 3. Invariantes Centrais

1. **Separação entre Modelo e Estratégia (Protocolo 0E-F, F-HQI-01):** Mérito de modelo preditivo não equivale a mérito de estratégia de trading.
2. **Isolamento de Teste Protegido (Protocolo 0E-C, C-HQI-26):** Dados protegidos nunca entram no ajuste de atributos, treino de modelos ou seleção de candidatos.
3. **Causalidade Estrita de Labels (Protocolo 0E-B, Protocolo 0E-C):** Alvos futuros nunca são acessíveis no momento de previsão.
4. **Determinismo Numérico e de Replay (ADR-0017, DD-16):** Repetições idênticas produzem saídas e manifestos idênticos.
5. **Custo Adicional Zero:** Nenhuma dependência paga ou serviço comercial.


---

## 4. Fechamento formal

O Sprint 5 foi reaudited independentemente com `PASS` no HEAD `bcbf48c232dc0ae7e60d2570ea4012a495e2584e`. Após autorização humana explícita, o PR #78 foi integrado em `sprint/5-ml-engine` pelo merge commit `8b09a34ecc7c3b0b180e30ada0702d22d61d96d2`.

A validação pós-merge no SHA exato confirmou o run `35473144900` do Sprint 5 Python CI com 13/13 jobs PASS, 1064 testes de repositório PASS, 88 testes dedicados S5 PASS e cobertura do pacote ML de 1460/1460 statements e 472/472 branches. O pinned upstream run `35473144855` passou integralmente.

```text
SPRINT_5_STATUS = FORMALLY_CLOSED
SPRINT_5_LIFECYCLE = FORMALLY_CLOSED
SPRINT_5_FINAL_VERDICT = PASS
OPEN_BLOCKERS = 0
PROMOTION_TO_SPRINT_6_GATE = YES
SPRINT_6_ENTRY_GATE = AUTHORIZED
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
```

A promoção autoriza exclusivamente o Gate de Entrada do Sprint 6 — Scenario Engine. Não autoriza implementação funcional do Scenario Engine nem altera as proibições de Strategy, Risk, Paper, Live, broker order ou dinheiro real.
