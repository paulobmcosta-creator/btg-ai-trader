# BTG AI Trader

Fundação de um futuro sistema quantitativo intradiário em Python, orientado a dados, avaliação de cenários, gestão independente de risco e operação auditável.

> **Estado:** Sprint 0E — Protocolos Quantitativos com sincronização documental concluída e gate final pendente. 0A–0D formalmente concluídos e aprovados. Este repositório continua sem estratégia operacional, modelo operacional, integração com BTG/MetaTrader 5 ou capacidade de enviar ordens.

## Segurança nesta fase

- negociação automática: desabilitada e não implementada;
- dinheiro real: proibido;
- conexões com corretoras e MT5: não implementadas;
- transmissão de ordens, inclusive `order_send()`: proibida;
- credenciais e segredos: não devem ser versionados;
- produção e deploy: fora do escopo.

As regras permanentes estão em [AGENTS.md](AGENTS.md). Qualquer evolução futura será promovida por gates explícitos, começando por dados confiáveis e pesquisa reprodutível, passando por validação fora da amostra e paper trading, e somente depois por auditoria e decisão humana.

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
no extra `dev`; não há dependências de runtime. A seleção de bibliotecas de dados, ML,
armazenamento e integração será decidida no Sprint 0 e registrada por ADR.

## Próximo marco

O [Sprint 0](docs/sprints/SPRINT_0.md) permanece em andamento: 0A–0D estão concluídos, 0E concluiu a sincronização documental e o gate 0F ainda não foi iniciado. A próxima etapa só pode ser aberta por decisão explícita e continua sem implementar trading real. Consulte também a [baseline de arquitetura e contratos](docs/architecture/README.md) e os [protocolos quantitativos](docs/protocols/quantitative/README.md).

## Aviso

Projeto experimental de engenharia e pesquisa. Não constitui recomendação de investimento nem garantia de resultado.
