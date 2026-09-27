# Temporal Chain Engine — V17

O motor avalia coerência temporal de vínculos declarados sem confirmar causalidade.

## Classificações
- `compatible`: exposição registrada no mesmo dia ou após o início de sintomas do caso-origem;
- `incompatible`: exposição registrada antes do início de sintomas do caso-origem;
- `indeterminate`: dados insuficientes ou caso-origem ausente.

## Geração
A geração é topológica e deriva dos vínculos informados. Ela não constitui confirmação de cadeia de transmissão.

## Intervalo entre sintomas
Quando caso-origem e contato/caso possuem início de sintomas registrado, o sistema calcula a diferença em dias. O valor deve ser interpretado como intervalo entre sintomas do par vinculado, não como estimativa causal automática.

## Governança
Resultados devem manter vínculo com registros-fonte, qualidade da investigação e proveniência das datas.
