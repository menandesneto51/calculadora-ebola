# Investigation Quality Engine — V17

Este módulo avalia **qualidade do registro e coerência estrutural da investigação**. O índice não representa risco de infecção, probabilidade diagnóstica ou gravidade clínica.

## Verificações iniciais
- identificadores duplicados;
- campos essenciais ausentes;
- caso-origem inexistente;
- auto-vínculo;
- ciclos na cadeia;
- início de sintomas anterior à exposição registrada.

## Índice de qualidade
O valor 0–100 funciona como indicador de pendências de qualidade. Cada problema permanece visível com código, entidade, gravidade e ação corretiva.

## Uso pelos agentes
O Data Quality Agent deve executar esta camada antes de aceitar exportações analíticas, snapshots institucionais ou interpretação da cadeia. O Coordinator Agent deve bloquear promoção para HML/PRD quando existirem erros estruturais não justificados.
