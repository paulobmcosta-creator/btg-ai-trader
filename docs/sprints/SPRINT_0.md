# Sprint 0 — Fundação e especificação

## Objetivo

Converter a visão inicial em arquitetura, contratos, protocolos e critérios de aceite verificáveis, preservando a ausência de capacidade de negociação.

## Etapa 0B — Ambiente de Desenvolvimento

**Estado:** concluída em 2026-08-17.

O projeto fixa Python 3.12 e fornece um extra `dev` instalável com `pytest`, `pytest-cov`,
Ruff e mypy. O backend de build e as ferramentas de desenvolvimento estão com versões
exatas para reduzir variações na instalação local. Não foram introduzidas dependências de
runtime, financeiras, de dados, ML ou integração externa.

Verificações exigidas: instalação em ambiente virtual limpo; `pytest` com cobertura; Ruff;
mypy; e `compileall`. O cache local do pytest é desabilitado para evitar que artefatos de
execução interfiram nas verificações do projeto.

### Pendência explícita

Antes de qualquer integração externa futura, validar e registrar por ADR a compatibilidade
de Python 3.12 com MetaTrader 5 e todas as dependências críticas que vierem a ser aprovadas.
Essa validação não autoriza integração, negociação ou uso de credenciais.

## Etapa 0C — Arquitetura lógica

**Estado:** ✅ APROVADO/CONCLUÍDO em 2026-08-18, após revisão documental e aprovação humana.

Foram materializadas as decisões 0C-01 a 0C-26 nos ADRs 0002–0014. A baseline fixa monólito modular orientado a eventos, envelope causal, semântica temporal e fidelidade histórica, identidade de instrumentos, fronteiras Signal/Risk/Execution, perfis operacionais, persistência, recovery, fail-safe, tratamento de eventos inválidos, ownership de posição/exposição e provenance de decisões.

Permanece proibida qualquer implementação funcional, Market Observer, integração BTG/MT5, ordem, ML, backtesting, dependência nova ou escolha de tecnologia física. Contratos e schemas pertencem exclusivamente à etapa 0D.

### Gate de encerramento 0C

- ADRs 0002–0014 presentes, aceitos e mutuamente referenciados;
- decisões 0C-01 a 0C-26 cobertas sem contradição documental;
- invariantes de veto de Risk, fail-closed, causalidade, temporalidade e ownership preservados;
- Plano Mestre e visão de arquitetura atualizados;
- nenhum código, dependência ou integração financeira adicionados;
- aprovação humana explícita registrada em 2026-08-18.

## Etapa 0D — Contratos e Modelo de Dados

**Estado:** ✅ formalmente fechado e aprovado em 2026-08-19 após o F1 final de consistência normativa/documental.

Os blocos 0D-A, 0D-B, 0D-C, 0D-D e 0D-E estão fechados e congelados. O 0D-F — Cross-contract Gate foi aprovado sem blocker arquitetural. A sincronização normativa/documental preservou os ADRs históricos e registrou os refinamentos do Sprint 0D nos ADRs 0015–0022.

O F1 final confirmou que ADRs históricos + refinements e os documentos vivos formam uma baseline normativa única, sem `CURRENT_NORM_CONFLICT`. Nenhuma implementação funcional de 0D foi iniciada e nenhuma tecnologia física foi escolhida.

O Sprint 0E — Protocolos Quantitativos **não foi iniciado**.

### Gate de encerramento 0D — F1

- relações de refinement 0003→0015, 0007→0016, 0008→0017, 0009→0018, 0010→0019, 0011→0020, 0013→0021 e 0014→0022 validadas;
- ADRs 0001–0022 contínuos e integralmente indexados;
- nenhum conflito normativo corrente detectado nas buscas transversais;
- links relativos e referências de refinement válidos;
- `git diff --check` sem erros;
- teste estrutural existente aprovado e `compileall` aprovado no ambiente de verificação;
- 0E confirmado como não iniciado.

## Próximas etapas após o fechamento do 0D
- definir aquisição, retenção, qualidade mensurável e proveniência física de dados, sem conexão nesta fase;
- escrever protocolos quantitativos de leakage, validação temporal, backtest/replay e paper trading;
- definir limites, tolerâncias, calendários concretos, gates mensuráveis e responsáveis por aprovação;
- confirmar escopo, instrumentos e horizonte do primeiro observador somente leitura quando o sprint apropriado for autorizado.

## Fora de escopo

Estratégias, modelos operacionais, integração BTG/MT5, coleta ao vivo, ordens, dinheiro real, cloud, produção e deploy.

## Critérios de aceite

- baseline arquitetural e ADRs revisados;
- riscos, limites não escolhidos e decisões deliberadamente adiadas visíveis;
- protocolos iniciais com evidências exigidas;
- ferramentas de qualidade escolhidas e executáveis;
- nenhum segredo ou capacidade de execução financeira no repositório.
