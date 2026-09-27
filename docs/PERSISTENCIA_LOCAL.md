# Persistência local SQLite — V17

O SQLite é um backend de desenvolvimento local controlado, não a arquitetura definitiva de produção.

## Estrutura
- `events`
- `contacts`
- `snapshots`
- `audit_log`
- `schema_version`

Todas as entidades são vinculadas por `event_id`.

## Regras
- nenhuma gravação automática pela interface;
- persistência somente após ação explícita;
- identificadores técnicos pseudonimizados;
- integridade referencial;
- migrations versionadas;
- snapshots imutáveis;
- banco de dados fora do Git;
- logs sem dados pessoais desnecessários.

Caminho local recomendado: `data/calculadora_ebola.db`.

Evolução: DEV local SQLite → HML PostgreSQL/API → PRD institucional, preservando domínio e repository pattern.
