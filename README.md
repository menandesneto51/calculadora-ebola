# Calculadora Ebola — V17 Inteligência Epidemiológica

Sistema local-first de apoio à investigação epidemiológica de doença pelo vírus Ebola, com cálculo temporal auditável, histórico estruturado de exposições, acompanhamento de contatos, análise conservadora de vínculos e governança de qualidade.

> A aplicação apoia a investigação. Compatibilidade temporal, prioridade operacional e índice de qualidade não representam diagnóstico, confirmação de transmissão ou decisão clínica.

## V17

A V17 evolui a calculadora V16 para uma arquitetura de investigação epidemiológica com serviços testáveis e regras versionadas.

### Capacidades principais

- protocolo epidemiológico versionado, com incubação padrão de 2–21 dias e seguimento parametrizado;
- distinção entre valores observados, reportados, derivados e estimados;
- histórico 1:N de exposições por contato;
- linha temporal epidemiológica com proveniência;
- Temporal Chain Engine, separando compatibilidade de infectividade, incubação e compatibilidade global;
- Investigation Quality Engine para contatos, vínculos e exposições;
- Command Center com pendências operacionais e quality gate para HML/PRD;
- múltiplas investigações/eventos locais;
- persistência SQLite com migrações versionadas;
- estado de trabalho mutável separado de snapshots imutáveis;
- checksum SHA-256 e trilha de auditoria dos snapshots;
- exportações CSV, JSON, HTML e visualizações da cadeia;
- testes automatizados no GitHub Actions.

## Governança epidemiológica

Regras epidemiológicas devem ficar nos módulos de epidemiologia/configuração, acompanhadas de versão e fonte. Hipóteses operacionais não devem ser apresentadas como definições oficiais.

O sistema preserva a separação entre:

- **qualidade da investigação** — completude e coerência estrutural;
- **prioridade operacional** — ordenação de revisão e acompanhamento;
- **compatibilidade temporal** — coerência entre datas disponíveis;
- **classificação epidemiológica/decisão clínica** — permanece dependente dos protocolos e autoridades competentes.

## Estrutura V17

```text
app.py
config/
docs/
src/
  data/
  domain/
  epidemiology/
  persistence/
  services/
tests/
.cursor/rules/
```

## Executar localmente

```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Para desenvolvimento e testes:

```bat
python -m pip install -r requirements-dev.txt
python -m compileall -q app.py src tests
python -m pytest -q
```

## Persistência local

O banco SQLite é utilizado somente quando o usuário aciona explicitamente a persistência. **Salvar estado de trabalho** atualiza o estado mutável da investigação. **Criar snapshot imutável** registra deliberadamente um marco versionado com checksum e auditoria.

Arquivos de dados locais não devem ser versionados no Git.

## Quality gate

Erros estruturais definidos pelo projeto bloqueiam a promoção técnica para HML/PRD até correção ou justificativa documentada. Warnings permanecem visíveis para revisão, mas não equivalem automaticamente a bloqueio.

## Cursor

O Cursor é o ambiente padrão de implementação e continuidade técnica da V17. As regras de governança estão em `.cursor/rules/epidemiology-governance.mdc`; mudanças epidemiológicas exigem revisão pelos agentes de Epidemiologia, Qualidade de Dados, Testes/QA, Documentação e Segurança/Governança.

## Documentação

Consulte `docs/` para protocolo epidemiológico, arquitetura, persistência, governança de eventos, múltiplas exposições, linha temporal, cadeia temporal, qualidade da investigação e workflow do Cursor.

## Histórico

Os roteiros V5–V16 permanecem como registro histórico da evolução do produto. Eles não substituem a documentação normativa e arquitetural da V17.
