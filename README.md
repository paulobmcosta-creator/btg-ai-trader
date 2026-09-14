# BTG AI Trader

Fundação de um futuro sistema quantitativo intradiário em Python, orientado a dados, avaliação de cenários, gestão independente de risco e operação auditável.

> **Estado:** a Fundação (Sprints 0A a 0F) está formalmente concluída e aprovada. O Sprint 1 — Market Observer está em desenvolvimento sob gates próprios. A branch padrão `main` preserva deliberadamente a baseline histórica da Fundação; o estado operacional corrente deve ser consultado no checkpoint do programa e nas branches de sprint aplicáveis. Não há estratégia operacional, capacidade de enviar ordens nem execução financeira real autorizada nesta fase.

## Repositório público e independência

Este é um projeto independente de engenharia e pesquisa. **Não é um produto oficial do Banco BTG Pactual, não é patrocinado, endossado, mantido ou afiliado ao BTG Pactual ou a empresas de seu grupo.** A referência a “BTG” no nome do projeto identifica o contexto técnico de integração estudado pelo autor e não implica vínculo institucional.

Marcas, nomes comerciais, APIs, SDKs e demais sinais distintivos de terceiros pertencem aos respectivos titulares. Nenhuma documentação deste repositório constitui declaração sobre disponibilidade, suporte ou autorização de uso de serviços de terceiros além do que estiver expressamente documentado por seus fornecedores.

A visibilidade pública do código **não concede licença aberta de uso**. Consulte [LICENSE](LICENSE). Vulnerabilidades e achados de segurança devem seguir [SECURITY.md](SECURITY.md).

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

O pacote contém apenas metadados iniciais nesta baseline histórica. As dependências de desenvolvimento são fixadas no extra `dev`; tecnologias físicas, bibliotecas de dados, armazenamento e integração são materializadas apenas quando autorizadas pelo estágio correspondente e pelos ADRs aplicáveis.

## Próximo marco

A fase de [Fundação (Sprint 0)](docs/sprints/SPRINT_0.md) está formalmente concluída e aprovada (0A a 0F). O desenvolvimento posterior ocorre sob o Contrato de Entrada 0F-E e gates de promoção, sem alterar retroativamente os snapshots históricos aprovados. Consulte a [baseline de arquitetura e contratos](docs/architecture/README.md), os [protocolos quantitativos](docs/protocols/quantitative/README.md) e, quando presente na branch de desenvolvimento aplicável, o checkpoint vivo em `docs/program/PROGRAM_EXECUTION.md`.

## Aviso

Projeto experimental de engenharia e pesquisa. Não constitui recomendação de investimento, oferta de serviço financeiro, convite à negociação de ativos nem garantia de resultado.
