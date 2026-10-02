# BTG AI Trader

Fundação de um futuro sistema quantitativo intradiário em Python, orientado a dados, avaliação de cenários, gestão independente de risco e operação auditável.

> **Estado:** Sprints 0A–0F e Sprints 1–7 estão formalmente concluídos. O Sprint 7 — Risk Engine foi fechado/PASS no head canônico `e379e9b34a8b607e86165bd3336d23fcd9406259`. O Risk Engine é determinístico e side-effect-free; Sprint 8/Paper Trading, Live Trading, envio de ordens, broker execution e dinheiro real permanecem não autorizados.

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

O checkpoint canônico atual é o fechamento do Sprint 7 — Risk Engine. O PR #90 foi integrado em `e379e9b34a8b607e86165bd3336d23fcd9406259` e validado pós-merge. O Sprint 8 — Paper Trader permanece `NOT_AUTHORIZED`; qualquer nova fase exige gate e autorização humana explícitos. O desenvolvimento ocorre diretamente no GitHub; consulte o [checkpoint do programa](docs/program/PROGRAM_EXECUTION.md), o [fechamento do Sprint 7](docs/program/S7_FINAL_ACCEPTANCE.md), a [baseline de arquitetura e contratos](docs/architecture/README.md) e os [protocolos quantitativos](docs/protocols/quantitative/README.md).

## Aviso

Projeto experimental de engenharia e pesquisa. Não constitui recomendação de investimento nem garantia de resultado.
