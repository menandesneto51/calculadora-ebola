# Calculadora Ebola — V3

Ferramenta em Streamlit para apoio à investigação epidemiológica de janelas prováveis de exposição, transmissibilidade, monitoramento de contatos e mapa de possível cadeia de transmissão.

## Recursos da V3

- Cálculo automático para sintomas secos, úmidos e hemorrágicos.
- Cenário opcional por data de óbito.
- Cadastro de contatos reais ou codificados.
- Campo de caso-origem para montar cadeia provável.
- Data do último contato de risco.
- Classificação de risco.
- Campo de evolução do contato.
- Data de início dos sintomas, quando houver.
- Prazo de monitoramento por contato.
- Mapa visual de possível cadeia de transmissão.
- Exportação em CSV e JSON.

## Executar

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Observação

Ferramenta de apoio técnico. Não substitui definição de caso, investigação de campo, exames laboratoriais, protocolos oficiais, sistema de notificação ou comunicação imediata às autoridades sanitárias.
