# Arquitetura V17 — Calculadora Ebola

## Direção
A V17 evolui a calculadora para um sistema de apoio à investigação epidemiológica orientado a evento, mantendo o Streamlit atual como frontend.

## Camadas
1. **domain** — entidades e proveniência.
2. **epidemiology** — parâmetros e cálculos epidemiológicos puros.
3. **data** — qualidade e validação.
4. **services** — investigação, alertas, priorização e agregação.
5. **app.py** — apresentação e interação; não deve concentrar novas regras.

## Evento/surto
`OutbreakEvent` introduz identidade, jurisdição, status e versão de protocolo. Nesta fase o app usa um evento local padrão; a próxima evolução deverá permitir cadastro/persistência de múltiplos eventos.

## Priorização operacional
O índice 0–100 é uma soma limitada de fatores explícitos. Sua finalidade é ordenar trabalho da equipe.

Ele NÃO deve ser interpretado como:
- probabilidade de Ebola;
- risco de infecção;
- prognóstico;
- gravidade clínica;
- definição ou classificação oficial de caso.

Cada fator mantém código, pontos e justificativa.

## Visão executiva
O resumo agregado foi desenhado para futura visão CIEVS/SIS e contabiliza:
- contatos;
- acompanhamento ativo;
- sintomáticos/suspeitos;
- confirmados;
- óbitos;
- encerrados/descartados;
- ausência de caso-origem;
- exposições pós-morte.

## Próximas fronteiras
- persistência de eventos;
- identificador de evento configurável;
- auditoria de alterações;
- deduplicação e integridade de vínculos;
- API de serviço;
- painel multi-evento;
- integração com notificações e fontes institucionais autorizadas.
