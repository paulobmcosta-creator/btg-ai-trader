# Scripts

Espaço para utilitários reprodutíveis de desenvolvimento, qualidade, manutenção e evidência técnica controlada.

No Sprint 1, um script pode abrir conexão externa **somente** quando todas as condições abaixo forem verdadeiras:

- o destino é um provider de Market Data read-only já aprovado por decisão canônica;
- não há conta de corretora, credencial de trading ou autoridade econômica;
- não há submit/modify/cancel de ordens nem qualquer API de execução;
- a credencial de dados é injetada apenas em runtime e nunca é versionada, impressa ou persistida;
- instrumento, escopo e duração são explícitos e limitados;
- a execução produz evidência técnica rastreável e falha fechado diante de ambiguidade.

`scripts/btg_first_lab_capture.py` permanece como harness histórico do BTG Solutions Data Services. Ele não é o caminho ativo de qualificação após ADR-0025.

`scripts/rico_mt5_first_lab_capture.py` é o harness ativo de evidência local para a qualificação Rico/MT5. Diferentemente do harness histórico BTG, ele **não abre conexão externa** e não controla o terminal: consome somente os arquivos append-only produzidos pelo custom indicator revisado, exige discovery completo do símbolo explícito, preserva prefixes brutos de ticks/candles e registra provenance, saúde e latência monotônica local no `TechnicalEvidenceStore`.

O harness Rico não recebe login, senha, token ou credencial como argumento, variável de ambiente ou configuração. Também não importa `MetaTrader5`, não acessa conta/posições e não contém interface de ordem.

Continuam proibidos scripts capazes de conectar a corretoras para execução, controlar MT5, acessar contas/posições, transmitir ou alterar ordens, habilitar negociação, assumir autoridade econômica ou fazer deploy de produção.
