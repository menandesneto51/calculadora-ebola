# Investigation Quality Engine — V17

Este módulo avalia **qualidade do registro e coerência estrutural da investigação**. O índice não representa risco de infecção, probabilidade diagnóstica, gravidade clínica nem confirmação de transmissão.

## Escopo

### Contatos e vínculos
- `DUPLICATE_CONTACT` — identificador de contato duplicado;
- `MISSING_REQUIRED_FIELDS` — campos essenciais ausentes;
- `ORPHAN_SOURCE` — caso-origem não localizado;
- `SELF_LINK` — contato vinculado a si próprio;
- `ONSET_BEFORE_EXPOSURE` — sintomas anteriores à exposição legada registrada;
- `TRANSMISSION_CYCLE` — ciclo estrutural na cadeia declarada.

### Exposições estruturadas
- `DUPLICATE_EXPOSURE` — identificador de exposição duplicado;
- `EXPOSURE_UNKNOWN_CONTACT` — exposição vinculada a contato inexistente;
- `EXPOSURE_UNKNOWN_SOURCE` — caso-origem da exposição não localizado;
- `ONSET_BEFORE_STRUCTURED_EXPOSURE` — sintomas anteriores ao início da exposição estruturada;
- `LEGACY_EXPOSURE_MISMATCH` — divergência entre o campo legado e o histórico estruturado;
- `EXPOSURE_BEFORE_SOURCE_ONSET` — exposição encerrada antes do início de sintomas conhecido da fonte, sinalizada para revisão epidemiológica.

## Índice de qualidade

O valor 0–100 é um indicador operacional de pendências de qualidade. Cada problema permanece disponível com código, entidade, gravidade e ação recomendada. O índice não deve ser combinado com prioridade operacional ou classificação epidemiológica.

## Quality gate HML/PRD

O Command Center expõe `promotion_allowed`, `blocking_issues` e `blocking_codes`.

Bloqueadores estruturais atuais:

- `DUPLICATE_CONTACT`
- `SELF_LINK`
- `TRANSMISSION_CYCLE`
- `DUPLICATE_EXPOSURE`
- `EXPOSURE_UNKNOWN_CONTACT`
- `ONSET_BEFORE_STRUCTURED_EXPOSURE`

A promoção técnica para HML/PRD deve permanecer bloqueada enquanto houver esses erros, salvo processo explícito de justificativa e revisão. Warnings exigem análise, mas não bloqueiam automaticamente a promoção.

## Agentes e Cursor

O **Data Quality Agent** executa esta camada antes de exportações analíticas, snapshots institucionais ou interpretação da cadeia. O **Coordinator Agent** consulta o quality gate antes da promoção. Epidemiology Agent, Testing/QA Agent, Documentation Agent e Security/Governance Agent revisam alterações que modifiquem regras, contratos ou critérios de bloqueio.

A regra operacional correspondente está em `.cursor/rules/epidemiology-governance.mdc`.
