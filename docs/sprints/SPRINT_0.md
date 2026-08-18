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

## Pendências propostas

- confirmar escopo, instrumentos e horizonte do primeiro observador somente leitura;
- definir glossário, requisitos funcionais e não funcionais;
- elaborar arquitetura de contexto/componentes e contratos entre camadas;
- decidir versão de Python, gestão de dependências e pipeline de qualidade;
- especificar política temporal, precisão numérica e calendários de mercado;
- definir aquisição, proveniência, qualidade e retenção de dados sem conectar nesta fase;
- modelar ameaças, falhas seguras, observabilidade e trilha de auditoria;
- escrever protocolos de leakage, validação temporal, backtest/replay e paper trading;
- definir gates mensuráveis e responsáveis por aprovação;
- registrar decisões relevantes em ADRs.

## Fora de escopo

Estratégias, modelos operacionais, integração BTG/MT5, coleta ao vivo, ordens, dinheiro real, cloud, produção e deploy.

## Critérios de aceite

- arquitetura e contratos revisados;
- riscos e decisões em aberto visíveis;
- protocolos iniciais com evidências exigidas;
- ferramentas de qualidade escolhidas e executáveis;
- nenhum segredo ou capacidade de execução financeira no repositório.
