# Scripts

Espaço para utilitários reprodutíveis de desenvolvimento, qualidade, manutenção e evidência técnica controlada.

No Sprint 1, um script pode abrir conexão externa **somente** quando todas as condições abaixo forem verdadeiras:

- o destino é um provider de Market Data read-only já aprovado por decisão canônica;
- não há conta de corretora, credencial de trading ou autoridade econômica;
- não há submit/modify/cancel de ordens nem qualquer API de execução;
- a credencial de dados é injetada apenas em runtime e nunca é versionada, impressa ou persistida;
- instrumento, escopo e duração são explícitos e limitados;
- a execução produz evidência técnica rastreável e falha fechado diante de ambiguidade.

`scripts/btg_first_lab_capture.py` é o único harness externo admitido nesta fase e está restrito ao BTG Solutions Data Services, perfil DD-68 `WIN / realtime / trades`, com discovery point-in-time antes da assinatura.

Continuam proibidos scripts capazes de conectar a corretoras, controlar MT5, acessar contas/posições, transmitir ou alterar ordens, habilitar negociação, assumir autoridade econômica ou fazer deploy de produção.
