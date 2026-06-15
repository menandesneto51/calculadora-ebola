# Calculadora Ebola — V9

Ferramenta em Python/Streamlit para apoio à investigação epidemiológica de janela provável de exposição, transmissibilidade, monitoramento de contatos e possível cadeia de transmissão.

## Atualização V9

Esta versão acrescenta tratamento operacional para casos que evoluíram a óbito, incluindo exposição pós-óbito.

A V9 diferencia:

1. **Óbito como desfecho**, quando a data de início dos sintomas é conhecida.
2. **Óbito como base retrospectiva de cálculo**, quando a data de início dos sintomas é desconhecida.
3. **Exposição pós-óbito**, quando há manipulação do corpo, transporte, velório/funeral, sepultamento ou contato pós-óbito.

## Regra central

### Paciente foi a óbito com início dos sintomas conhecido

A ferramenta usa a data de início dos sintomas como base principal. A data do óbito é registrada como desfecho e compõe a definição do fim operacional da busca de contatos, especialmente se houver exposição pós-óbito.

### Paciente foi a óbito sem início dos sintomas conhecido

A ferramenta pode estimar retrospectivamente o início dos sintomas a partir da data do óbito, desde que o óbito tenha ocorrido após sintomas ou que a informação sintomática seja desconhecida.

### Óbito sem sintomas conhecidos

A ferramenta não deve gerar uma estimativa forte apenas pela data de óbito quando não há sintomas conhecidos nem informação clínica suficiente.

## Campos acrescentados

- Situação/desfecho do caso.
- Data do óbito.
- Óbito ocorreu após sintomas?
- Manipulação do corpo.
- Velório/funeral.
- Transporte do corpo.
- Contato pós-óbito identificado.
- Data de sepultamento seguro/fim da exposição pós-óbito.
- Data final da exposição em vida.
- Fim operacional da busca de contatos.

## Contatos pós-óbito

A lista de contatos inclui tipos de exposição como:

- Manipulação do corpo.
- Velório/funeral.
- Sepultamento.
- Transporte do corpo.
- Limpeza/desinfecção.

## Padrão de datas

- Interface: **DD/MM/AAAA**
- Tabelas: **DD/MM/AAAA**
- CSVs: **DD/MM/AAAA**
- JSON técnico: **AAAA-MM-DD**

## Executar localmente

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Atualizar no GitHub manualmente

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
git status
git add app.py README.md requirements.txt
git commit -m "Adiciona manejo de óbito e exposição pós-óbito"
git push
```

## Observação

Ferramenta de apoio técnico. Não substitui definição de caso, investigação de campo, exames laboratoriais, protocolos oficiais, sistema de notificação ou comunicação imediata às autoridades sanitárias.
