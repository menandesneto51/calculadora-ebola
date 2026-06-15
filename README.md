# Calculadora Ebola — V5

Ferramenta em Python/Streamlit para apoio à investigação epidemiológica de janela provável de exposição, transmissibilidade, monitoramento de contatos e possível cadeia de transmissão.

## Atualização V5

Esta versão consolida a correção de nomenclatura clínica e padroniza a interface para uso no Brasil:

- Datas exibidas no padrão brasileiro **DD/MM/AAAA**.
- Campos de entrada de data em **DD/MM/AAAA**.
- CSVs exportados em **DD/MM/AAAA**.
- JSON técnico mantido em **AAAA-MM-DD** para interoperabilidade.
- Seção “Como as datas são calculadas” dentro da própria ferramenta.
- Importação de contatos por **CSV** ou **XLSX**.

## Nomenclatura clínica

- **Sintomas secos (iniciais)**: sintomas iniciais inespecíficos, como febre, fadiga, fraqueza, cefaleia, mialgia/artralgia, dor de garganta e perda de apetite.
- **Sintomas úmidos (tardios)**: sintomas tardios associados à eliminação de fluidos corporais, como náusea, dor abdominal, diarreia, vômitos e/ou sangramento inexplicado.
- **Sangramento / manifestação hemorrágica**: mantido apenas como subcategoria operacional de sintoma úmido/tardio, para uso quando a data disponível na investigação for a data do sangramento. Não deve ser tratado como terceira categoria clínica oficial independente.

## Como as datas são calculadas

### Caso índice

- Sintomas secos/iniciais: a data informada é considerada como o início estimado dos sintomas.
- Sintomas úmidos/tardios: a ferramenta subtrai o número de dias configurado para sintomas úmidos/tardios.
- Sangramento/manifestação hemorrágica: a ferramenta subtrai o número de dias configurado para sangramento.
- Óbito, quando informado: a ferramenta subtrai o número de dias configurado entre início dos sintomas e óbito.

### Janela provável de exposição

- Início provável da exposição = início estimado dos sintomas - incubação máxima.
- Fim provável da exposição = início estimado dos sintomas - incubação mínima.

### Janela operacional de transmissibilidade

- Início = início estimado dos sintomas.
- Fim = data final para busca de contatos informada pelo usuário.

### Contatos

- Possível início de sintomas do contato = data do último contato + incubação mínima até incubação máxima.
- Monitorar até = data do último contato + número de dias de monitoramento.

## Funcionalidades

- Cálculo automático para sintomas secos/iniciais, sintomas úmidos/tardios e sangramento como subcategoria operacional.
- Cenário opcional por data de óbito.
- Cadastro de contatos reais ou codificados.
- Importação de contatos por CSV ou XLSX.
- Campo de caso-origem para montar cadeia provável.
- Data do último contato de risco.
- Classificação de risco.
- Campo de evolução do contato.
- Data de início dos sintomas, quando houver.
- Prazo de monitoramento por contato.
- Mapa visual de possível cadeia de transmissão.
- Exportação em CSV e JSON.

## Executar localmente

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Atualizar no GitHub

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
git status
git add app.py README.md requirements.txt
git commit -m "Padroniza datas no formato brasileiro e documenta cálculo"
git push
```

## Observação

Ferramenta de apoio técnico. Não substitui definição de caso, investigação de campo, exames laboratoriais, protocolos oficiais, sistema de notificação ou comunicação imediata às autoridades sanitárias.
