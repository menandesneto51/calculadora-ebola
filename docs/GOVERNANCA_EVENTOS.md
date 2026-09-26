# Governança de eventos e snapshots — V17

## Unidade de trabalho
Cada investigação deve possuir um `event_id` estável. Dados, contatos, vínculos, alertas e snapshots devem permanecer associados ao evento correto.

## Snapshot
Um snapshot é uma representação versionada do estado operacional do evento. Cada snapshot contém:
- identificação do evento;
- versão do protocolo;
- versão do snapshot;
- data/hora UTC;
- payload;
- checksum SHA-256.

O checksum apoia integridade e rastreabilidade, mas não substitui assinatura digital nem controles institucionais de segurança.

## Auditoria
Alterações relevantes devem gerar eventos de auditoria contendo:
- event_id;
- ação;
- tipo de entidade;
- identificador;
- ator;
- data/hora;
- detalhes mínimos necessários.

## Dados pessoais
Não registrar CPF, nome completo ou outros identificadores pessoais em logs de auditoria. Preferir códigos internos/pseudonimizados.

## Persistência
A V17 define contratos de domínio antes de escolher o backend. Evolução prevista:
1. memória/sessão Streamlit para protótipo;
2. SQLite para desenvolvimento local controlado;
3. PostgreSQL/API institucional em HML/PRD;
4. políticas de acesso, retenção, backup e auditoria definidas pela SES/MT.

## Cursor e agentes
Mudanças no modelo de persistência exigem revisão dos agentes Data Quality, Security/Governance, Testing/QA e Coordinator.
