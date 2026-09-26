# Cursor — fluxo obrigatório do projeto

A implementação da Calculadora Ebola utiliza o Cursor como ambiente padrão de continuidade técnica.

## Agentes
- Coordinator Agent
- Epidemiology Agent
- Data Quality Agent
- Transmission Chain Agent
- Testing/QA Agent
- Documentation Agent
- Security/Governance Agent

## Regra de merge
Nenhuma mudança em regra epidemiológica deve ser integrada sem teste correspondente e registro de proveniência.

## Estratégia
1. preservar a V16 funcional;
2. adicionar módulos V17;
3. executar testes;
4. conectar módulos ao app de forma incremental;
5. remover legado somente após equivalência funcional comprovada.

## Restrições
- não hard-codear novas regras epidemiológicas na UI;
- não converter estimativas em dados observados;
- não remover histórico sem migração;
- não incluir segredos no repositório;
- preferir commits pequenos e semanticamente identificáveis.
