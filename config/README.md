# Configuração

Este diretório receberá contratos e exemplos de configuração não sensíveis.

Regras:

- nunca versionar credenciais, tokens, contas ou endpoints privados;
- configurações locais devem usar os padrões ignorados pelo `.gitignore`;
- valores inseguros não podem ser padrão;
- qualquer configuração futura relacionada à execução deve permanecer desabilitada e exigir gate explícito.

O formato físico e o mecanismo de validação da configuração constituem decisão de implementação classificada como `MAY_DECIDE_DURING_SPRINT_1` (DD-65), a ser formalizada no Sprint 1 antes da primeira capacidade que dependa materialmente de configuração.
