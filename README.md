# Calculadora Ebola — V4

Ferramenta em Python/Streamlit para apoio à investigação epidemiológica de janela provável de exposição, transmissibilidade, monitoramento de contatos e possível cadeia de transmissão.

## Atualização V4 — nomenclatura clínica

Esta versão corrige a nomenclatura dos cenários clínicos:

- **Sintomas secos (iniciais)**: sintomas iniciais inespecíficos, como febre, fadiga, fraqueza, cefaleia, mialgia/artralgia, dor de garganta e perda de apetite.
- **Sintomas úmidos (tardios)**: sintomas tardios associados a eliminação de fluidos corporais, como náusea, dor abdominal, diarreia, vômitos e/ou sangramento inexplicado.
- **Sangramento / manifestação hemorrágica**: mantido apenas como subcategoria operacional de sintoma úmido/tardio, para uso quando a data disponível na investigação for a data do sangramento. Não deve ser tratado como terceira categoria clínica oficial independente.

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

## Observação

Ferramenta de apoio técnico. Não substitui definição de caso, investigação de campo, exames laboratoriais, protocolos oficiais, sistema de notificação ou comunicação imediata às autoridades sanitárias.
