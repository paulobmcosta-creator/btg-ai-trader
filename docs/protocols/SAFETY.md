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

## Delimitação temporal e normativa

Os controles acima registram a postura histórica obrigatória da fase estrutural da Fundação e permanecem preservados como evidência do estágio em que foram estabelecidos. Eles não devem ser reescritos retrospectivamente como se a Fundação já autorizasse integrações externas.

Com o encerramento da Fundação, qualquer integração futura de **market data** no Sprint 1 somente pode existir sob o Contrato de Entrada 0F-E e a adjudicação histórica 0F-F, preservando cumulativamente:

```text
READ_ONLY_BY_CONSTRUCTION
STRUCTURAL_ESCALATION
NEGATIVE_CAPABILITIES = NC-01..NC-20
```

A eventual presença futura de adapter ou SDK para observação de dados, inclusive pacote dual-use, não constitui autorização de execução. Sua admissibilidade depende integralmente dos critérios de 0F-D/0F-E: nenhuma interface, configuração, credencial, permissão ou caminho de runtime pode tornar ordens ou compromissos econômicos alcançáveis sem nova alteração estrutural auditada.

Esta delimitação **não autoriza trading, paper trading, execução, ordens, dinheiro real ou credenciais de negociação**.
