# CHANGELOG

## V17 — Inteligência Epidemiológica

### Arquitetura e governança
- regras epidemiológicas versionadas e separadas da interface;
- workflow Cursor com agentes especializados;
- CI com compilação e testes automatizados;
- quality gate técnico para promoção HML/PRD.

### Investigação
- histórico estruturado 1:N de exposições;
- linha temporal com proveniência;
- Temporal Chain Engine com compatibilidade de infectividade, incubação e compatibilidade global;
- alertas e priorização operacional;
- Command Center executivo;
- motor de qualidade para contatos, vínculos e exposições.

### Persistência e auditoria
- múltiplos eventos/investigações;
- SQLite com schema versionado;
- estado de trabalho mutável;
- snapshots imutáveis versionados;
- checksum SHA-256 e trilha de auditoria.

### Compatibilidade
- mantém leitura dos campos legados da V16 quando não há exposição estruturada;
- mantém visualizações e exportações da cadeia;
- compatibilidade temporal não equivale a transmissão confirmada.

### Pré-release
A V17 permanece em revisão pré-release até conclusão dos gates automatizados e revisão funcional/epidemiológica.
