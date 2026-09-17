# Sprint 4 — Statistical Baselines

## 1. Contexto e Linhagem Canônica

- **Repositório:** `paulobmcosta-creator/btg-ai-trader`
- **Base SHA Obrigatória:** `922adee625029c0cbd6c665f8906e7fd99cf71cb`
- **Branch Canônica:** `sprint/4-statistical-baselines`
- **Branch de Trabalho:** `s4/00-full-statistical-baselines`
- **Issue de Acompanhamento:** Issue #73
- **Classificação:** `DETERMINISTIC_STATISTICAL_BASELINE_AND_TEMPORAL_VALIDATION_KERNEL`

O Sprint 3 (Deterministic Economic Backtesting) foi formalmente aprovado e fechado no HEAD canônico `922adee625029c0cbd6c665f8906e7fd99cf71cb` (após o merge funcional aceito `6333b8f431d43be9c40f3222fbbe17cf06509033` e validação pós-merge verde nos runs CI 35256018204 e Upstream 35256018048).

O Sprint 4 constrói uma camada de pesquisa para estimar e avaliar baselines estatísticos simples e determinísticos sob validação temporal estritamente causal, com isolamento metodológico do conjunto de teste protegido (Out-of-Sample).

## 2. Escopo do Sprint 4

### Incluído no Escopo
1. **Semântica Epistemológica de OOS:** Separação estrita entre Development, Training/Fit, Validation/Selection e Protected Evaluation.
2. **Modelo Temporal dos Samples (`StatisticalSample`):** Distinção explícita entre tempo de conhecimento dos atributos (`feature_knowledge_time`) e tempo de disponibilização do alvo (`target_knowledge_time`). Invariante causal: `target_knowledge_time <= knowledge_cutoff` para inclusão em fit.
3. **Fronteiras de Avaliação (`EvaluationBoundary`, `TemporalFold`, `WalkForwardPlan`):** Definição imutável e explícita dos intervalos de desenvolvimento, treino, validação e teste protegido com semântica de limites.
4. **Walk-Forward Causal:** Políticas de janela expansiva (`EXPANDING`) e rolante (`ROLLING`). Rejeição estrita de random shuffle para validação confirmatória.
5. **Purging & Embargo:** Remoção de amostras com horizonte de informação sobreposto à fronteira de avaliação e suporte a intervalo de embargo configurável.
6. **Catálogo de Baselines Determinísticos:**
   - `ConstantBaseline`
   - `PersistenceBaseline` / `LastObservedValueBaseline`
   - `HistoricalMeanBaseline`
   - `HistoricalMedianBaseline`
   - `HistoricalPriorProbabilityBaseline`
   - `MajorityClassBaseline`
   - `LastKnownClassBaseline`
7. **Tratamento de Cold-Start e Missingness:** Comportamento fail-closed ou explícito (`is_cold_start = True`, sem imputação silenciosa).
8. **Métricas Estatísticas Determinísticas:**
   - Contínuas: MAE, MSE, RMSE, Mean Bias.
   - Probabilidade Binária: Brier Score, Base Rate.
   - Categóricas: Accuracy, Class Prevalence, Confusion Counts.
   - Separação total de métricas financeiras/econômicas (pertencentes ao Sprint 3).
9. **Diagnóstico de Calibração de Probabilidades:** `CalibrationReport` com bins explícitos e Brier Score (diagnóstico descritivo, sem ML calibrators aprendidos).
10. **Distribuição Empírica entre Folds & Estabilidade:** Relato da distribuição fold-a-fold (pior fold, melhor fold, dispersão). Preservação do deferimento de thresholds universais de estabilidade (DD-91).
11. **Ponderação de Agregação de Folds:** Políticas explícitas (`EQUAL_FOLD`, `SAMPLE_WEIGHTED`).
12. **Comparação de Candidatos e Baselines:** Verificação estrita de paridade metodológica (mesma população, mesmo target, mesmos folds, mesmo horizonte).
13. **Proteção Estrutural contra Seleção em Teste Protegido:** Proibição de seleção de candidato vencedor utilizando resultados de `PROTECTED_TEST`.
14. **Identidade do Candidato & Proveniência:** Identidade determinística baseada em versão, parâmetros e código. `StatisticalEvaluationInputBoundary` e `StatisticalEvaluationManifest` com hash SHA-256 raiz.
15. **Rastreamento de Família de Busca (`SearchFamily`):** Registro de multiplicidade e candidatos avaliados.
16. **Scanner Estático de Fronteiras:** `scripts/check_s4_boundary.py` impedindo ML, stochasticidade, APIs de corretora e caminhos operacionais.

### Excluído do Escopo (Proibições Absolutas)
- Plataforma de Feature Engineering / Feature Store / Feature Registry.
- Model Registry / AutoML / Hyperparameter search engines.
- Modelos de Machine Learning (Random Forest, Gradient Boosting, XGBoost, LightGBM, PyTorch, TensorFlow, etc.) — pertencem ao Sprint 5.
- Regressão Logística operacional.
- Strategy Engine, Signal Engine ou Risk Engine operacionais.
- Negociação real, paper trading ou autoridade financeira.
- APIs de corretora, ordens ou conexão externa.
- Mutação do `FinancialLedger`.
- Dependências com custo financeiro adicional (`ADDITIONAL_RECURRING_COST = ZERO`).
- Novas dependências de runtime (`NEW_RUNTIME_DEPENDENCIES = 0`).

## 3. Invariantes Centrais

1. **OOS Epistemológico (C-HQI-01 a C-HQI-03):** OOS é uma relação entre a evidência e o histórico de desenvolvimento do candidato. Teste protegido não pode sofrer adaptação, seleção de hiperparâmetros ou escolha de vencedor.
2. **Causalidade Estrita de Labels (PR-0E-C-02, C-HQI-09):** Amostras futuras ou labels futuros (`target_knowledge_time > cutoff`) jamais entram no ajuste do modelo.
3. **Determinismo Byte-a-Byte (ADR-0017, DD-16):** Ausência de RNG, `uuid4`, `secrets`, `os.urandom` ou timestamps de relógio de parede como variáveis causais.
4. **Semântica Numérica Explícita:** Uso de `Decimal` exato para métricas, probabilidades e valores contínuos sujeitos a verificação de igualdade.
