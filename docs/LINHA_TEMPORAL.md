# Linha temporal epidemiológica — V17

A timeline organiza marcos por pessoa e evento sem converter sequência temporal em causalidade.

## Proveniência
- `observed`: observado diretamente;
- `reported`: informado/registrado;
- `derived`: calculado a partir de regra explícita;
- `estimated`: estimativa/heurística.

## Marcos iniciais
Exposição (início/fim), início de sintomas e fim derivado do monitoramento. O domínio suporta expansão para detecção, isolamento, evolução, óbito e eventos pós-morte.

## Intervalos
Intervalos são calculados apenas quando as duas datas existem. Exposição → sintomas é apresentado como intervalo temporal observado entre registros e não como prova de transmissão.

## Governança
Qualquer futuro cálculo de incubação observada, intervalo serial ou geração deve preservar as datas-fonte, proveniência, método e versão do protocolo.
