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


## Ciclo dos agentes — V17

Para cada alteração de regra ou motor de inteligência:

1. **Coordinator Agent** delimita escopo e impede alteração simultânea não testada.
2. **Epidemiology Agent** verifica semântica epidemiológica, protocolo e distinção entre regra oficial e hipótese.
3. **Data Quality Agent** testa cronologia, completude, duplicidade e coerência dos vínculos.
4. **Transmission Chain Agent** avalia efeitos sobre gerações e vínculos de transmissão.
5. **Testing/QA Agent** exige cobertura dos casos-limite e regressão da V16.
6. **Documentation Agent** atualiza metodologia, dicionário e changelog.
7. **Security/Governance Agent** verifica dados sensíveis, proveniência, auditoria e ausência de segredos.

O Coordinator Agent somente considera uma etapa pronta para integração após registrar as verificações aplicáveis.
