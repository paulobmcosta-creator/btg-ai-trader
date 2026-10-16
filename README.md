# BTG AI Trader

Fundação de um futuro sistema quantitativo intradiário em Python, orientado a dados, avaliação de cenários, gestão independente de risco e operação auditável.

> **Estado:** Sprints 0A–0F e Sprints 1–7 estão formalmente concluídos. O Sprint 8 — Paper Trader permanece em Entry Gate `CHANGES_REQUIRED`. Em 2026-10-04 foi autorizada a remediação isolada de S8-B01 (caminho operacional `StrategyDecision`/`TradeIntent`) na Issue #95; o candidato de remediação aguarda CI/revisão e S8-B02 (`PAPER_ELIGIBLE` + freeze) continua aberto. Paper funcional, Live Trading, envio real de ordens e dinheiro real permanecem não autorizados.

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

O checkpoint atual continua sendo o Sprint 8 Entry Gate da Issue #93/PR #94, ainda não integrado. A coordenação autorizou em 2026-10-04 a remediação empilhada de S8-B01 na Issue #95 e branch `s8/01-strategy-remediation`, sem autorizar Paper. O próximo gate técnico dessa remediação é CI exato + revisão independente; S8-B02 permanece aberto. Consulte o [checkpoint do programa](docs/program/PROGRAM_EXECUTION.md), o [Entry Contract do Sprint 8](docs/program/S8_ENTRY_CONTRACT.md), o [fechamento do Sprint 7](docs/program/S7_FINAL_ACCEPTANCE.md) e os [protocolos quantitativos](docs/protocols/quantitative/README.md).

## Aviso

Projeto experimental de engenharia e pesquisa. Não constitui recomendação de investimento nem garantia de resultado.
