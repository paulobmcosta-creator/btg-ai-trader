# BTG AI Trader

Fundação de um futuro sistema quantitativo intradiário em Python, orientado a dados, avaliação de cenários, gestão independente de risco e operação auditável.

> **Estado:** Fase de Fundação (Sprints 0A a 0F) formalmente concluída e aprovada. O lifecycle do Sprint 1 — Market Observer está `OPEN`, com reconciliação pré-código concluída e primeira implementação funcional autorizada (`S1_A_AUTHORIZED = YES`) pelo mandato humano de 2026-09-13. Este repositório continua sem estratégia operacional, modelo operacional, capacidade de enviar ordens ou execução financeira real.

## Segurança nesta fase

- negociação automática: desabilitada e não implementada;
- dinheiro real: proibido;
- transmissão e criação de ordens, inclusive `order_send()`: proibidas;
- credenciais e segredos de execução: não devem ser versionados;
- produção e deploy: fora do escopo.

As regras permanentes e a distinção canônica entre autoridade normativa e realidade implementada estão em [AGENTS.md](AGENTS.md). Qualquer evolução futura será promovida por gates explícitos, começando por observação passiva de dados e pesquisa reprodutível, passando por validação fora da amostra e paper trading, e somente depois por auditoria e decisão humana.

## Estrutura

```text
config/                 exemplos e contratos de configuração seguros
docs/
  architecture/         visão e limites arquiteturais
  adr/                  decisões arquiteturais versionadas
  protocols/            protocolos de pesquisa, validação e segurança
  sprints/              planejamento e evidências por sprint
scripts/                utilitários de desenvolvimento (sem execução financeira)
src/btg_ai_trader/      pacote Python
tests/                  testes automatizados
```

## Ambiente de desenvolvimento

Requer Python **3.12**. A versão é fixada em [`.python-version`](.python-version) e em
`pyproject.toml`; versões posteriores não fazem parte do ambiente suportado nesta etapa.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest --cov=btg_ai_trader --cov-report=term-missing
python -m ruff check .
python -m mypy src
```

O pacote contém apenas metadados iniciais. As dependências de desenvolvimento são fixadas
no extra `dev`; não há dependências de runtime. Tecnologias físicas, bibliotecas de dados,
armazenamento e integração não foram prematuramente fixadas no Sprint 0; decisões técnicas
adiadas são formalizadas no primeiro estágio em que se tornam materialmente necessárias (para
decisões `MAY_DECIDE_DURING_SPRINT_1`, antes da primeira capability dependente), com registro
por ADR quando arquiteturalmente materiais.

## Próximo marco

A fase de [Fundação (Sprint 0)](docs/sprints/SPRINT_0.md) está formalmente concluída e aprovada (0A a 0F). O PR #5 foi integrado em `dabce69d92054b77cad72809669d4340c211c328` e a Issue #1 foi fechada como concluída. O mandato humano de execução autônoma de 2026-09-13 autoriza a primeira implementação funcional do Sprint 1 (`PRE_CODE_RECONCILIATION = COMPLETE`; `S1_A_AUTHORIZED = YES`; `FIRST_FUNCTIONAL_CODE = AUTHORIZED`), sob o contrato 0F-E integral e os gates de promoção. O desenvolvimento ocorre diretamente no GitHub; consulte o [checkpoint do programa](docs/program/PROGRAM_EXECUTION.md). Consulte também a [baseline de arquitetura e contratos](docs/architecture/README.md) e os [protocolos quantitativos](docs/protocols/quantitative/README.md).

## Aviso

Projeto experimental de engenharia e pesquisa. Não constitui recomendação de investimento nem garantia de resultado.
