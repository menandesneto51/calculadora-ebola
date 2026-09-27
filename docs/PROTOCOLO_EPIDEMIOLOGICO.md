# Protocolo epidemiológico — V17

## Finalidade
Este sistema é uma ferramenta de apoio à investigação epidemiológica. Não substitui definição oficial de caso, avaliação clínica, protocolo assistencial ou decisão da autoridade sanitária.

## Proveniência
A V17 separa quatro classes de informação:
- **observed**: observada/documentada;
- **reported**: informada por fonte externa;
- **derived**: calculada deterministicamente a partir de dados observados/reportados;
- **estimated**: inferida por hipótese operacional.

## Regras oficiais parametrizadas
- período de incubação: **2–21 dias**;
- acompanhamento de contatos: **21 dias após a última exposição**;
- pessoas infectadas não são consideradas transmissoras durante a incubação; a infectividade é considerada a partir do início dos sintomas nos cálculos temporais.

Fontes oficiais de referência:
- WHO — Ebola disease fact sheet e Q&A;
- Ministério da Saúde do Brasil — Ebola, Saúde de A a Z.

As fontes devem ser revalidadas quando houver alteração de protocolo, contexto de surto, agente/espécie viral ou orientação nacional/internacional.

## Compatibilidade temporal
O Temporal Chain Engine avalia coerência entre datas registradas, período de infectividade e janela de incubação configurada. Resultado `compatible` significa apenas que a sequência temporal é possível segundo os parâmetros disponíveis. **Não confirma transmissão, vínculo causal ou diagnóstico.**

## Hipóteses operacionais
Offsets retrospectivos usados historicamente pela aplicação não constituem definições epidemiológicas oficiais.

Na configuração V17, os offsets de fase úmida (+4 dias), fase grave (+5 dias) e estimativa retrospectiva a partir do óbito (−10 dias) são classificados como `operational_assumption`. Quando utilizados:
1. o resultado deve ser marcado como **estimated**;
2. o método deve permanecer identificável;
3. não pode substituir uma data observada/reportada;
4. não pode ser apresentado como regra da OMS ou do Ministério da Saúde;
5. mudança do valor exige justificativa e teste.

## Limitações
- sintomas iniciais são inespecíficos e confirmação de Ebola depende de investigação e diagnóstico laboratorial;
- ausência de compatibilidade temporal pode indicar erro de dado, vínculo incorreto ou necessidade de revisão;
- compatibilidade temporal não estima probabilidade de transmissão;
- prioridade operacional e índice de qualidade são dimensões distintas da classificação epidemiológica.

## Governança
Toda alteração de parâmetro epidemiológico exige:
1. fonte e jurisdição;
2. versão/data;
3. justificativa;
4. classificação como regra protocolar ou hipótese operacional;
5. teste automatizado;
6. registro no CHANGELOG;
7. revisão no fluxo de agentes do Cursor.
