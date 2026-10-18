# Scripts

Espaço reservado para utilitários reprodutíveis de desenvolvimento, qualidade e manutenção.

Scripts capazes de conectar a corretoras, controlar MT5, transmitir ordens, habilitar negociação ou fazer deploy de produção são proibidos nesta fase.

## Codex e Antigravity

`agent_workflow.py` coordena tarefas de engenharia em checkouts isolados, com
estado persistido, verificações locais, relatórios estruturados e passagem manual
de tarefas quando um CLI não está disponível. `start_agent_workflow.ps1` prepara
o acionamento no Windows. Consulte [o guia de execução](../docs/EXECUTAR_SEMIAUTOMACAO.md).

Na versão 0.3.0, use `sprint init/run/status/packet/sync` para executar lotes
ordenados pelo Antigravity, com limites persistentes de chamadas. Codex só é
acionado nas etapas críticas com `--allow-codex`. A publicação de checkpoints
em `workflow-status/<id>` permite coordenar pelo ChatGPT conectado ao GitHub.
O [guia autossuficiente](../docs/INICIAR_CHATGPT_WORKFLOW.md) e o
[prompt para novo chat](../docs/CHATGPT_PROJECT_PROMPT.md) substituem a
necessidade de consultar a conversa original.
