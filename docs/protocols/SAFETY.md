# Protocolo de segurança — fase estrutural

## Objetivo

Garantir que o bootstrap permaneça sem capacidade de afetar mercados, contas ou capital.

## Controles obrigatórios

1. Não adicionar SDKs ou adaptadores de corretora/MT5.
2. Não criar funções de criação, envio, alteração ou cancelamento de ordens.
3. Não armazenar segredos ou dados identificadores de conta.
4. Não habilitar automação, serviços persistentes, cloud ou deploy.
5. Revisar alterações buscando capacidades proibidas e dependências inesperadas.
6. Tratar qualquer ambiguidade como bloqueio seguro e solicitar decisão humana.

## Evidência de conformidade

Cada entrega deve listar arquivos alterados, testes executados, limitações e pendências. Violações bloqueiam a entrega.
