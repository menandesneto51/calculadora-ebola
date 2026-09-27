# Motor de inteligência da investigação — V17

## Objetivo
Transformar datas, evolução e vínculos epidemiológicos em pendências operacionais auditáveis, sem substituir avaliação epidemiológica humana.

## Saídas
O motor retorna:
- janelas temporais derivadas;
- término do acompanhamento;
- inconsistências de qualidade;
- alertas priorizados;
- proveniência de cada resultado calculado.

## Prioridades
- **critical**: requer avaliação epidemiológica prioritária;
- **high**: pendência relevante de investigação/seguimento;
- **medium**: qualificação necessária;
- **low**: preparação ou fechamento operacional.

## Alertas iniciais
- contato sintomático;
- exposição pós-morte;
- acompanhamento terminando hoje;
- acompanhamento terminando amanhã;
- acompanhamento vencido sem desfecho;
- contato sem caso-origem;
- necessidade de revisão da cadeia para confirmado/óbito.

## Princípio de segurança
Os alertas são apoio à decisão. Não constituem diagnóstico, classificação oficial automática ou substituição da investigação pela equipe responsável.
