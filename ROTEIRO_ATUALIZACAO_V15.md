# Roteiro de atualização — Calculadora Ebola V15

## Objetivo

Melhorar a legibilidade do mapa de possível cadeia de transmissão.

## Melhorias incluídas

- layout hierárquico por geração;
- espaçamento vertical automático;
- rótulo curto (ID apenas);
- hover com evolução, risco, município, tipo de contato, data e geração;
- legenda por evolução;
- filtros por geração e por evolução;
- destaque para pós-óbito;
- opção de destacar apenas nós clinicamente mais relevantes.

## Atualizar localmente

Copie para:

`C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola`

Substitua:

- `app.py`
- `README.md`
- `requirements.txt`

## Testar

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"

call .venv\Scripts\activate.bat

python -m pip install -r requirements.txt

python -m streamlit run app.py
```

## Subir para GitHub

```bat
git status
git add app.py README.md requirements.txt
git commit -m "Melhora visualização da cadeia de transmissão"
git push
```

## Subir roteiro

```bat
git add ROTEIRO_ATUALIZACAO_V15.md
git commit -m "Adiciona roteiro de atualização da V15"
git push
```
