# Roteiro de atualização — Calculadora Ebola V13

## Objetivo

Corrigir o erro de comparação entre `pandas.Timestamp` e `datetime.date` ao importar a planilha de contatos.

## Erro

```text
Cannot compare Timestamp with datetime.date.
Use ts == pd.Timestamp(date) or ts.date() == date instead.
```

## Correção

A V13 corrige:

- conversão explícita de `pandas.Timestamp` para `datetime.date`;
- normalização das colunas de data da planilha;
- conversões defensivas antes das comparações de janelas de transmissibilidade e monitoramento.

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

Importe a planilha de contatos e confira se o erro desapareceu.

## Subir para GitHub

```bat
git status
git add app.py README.md requirements.txt
git commit -m "Corrige comparação de datas importadas do Excel"
git push
```

## Subir roteiro

```bat
git add ROTEIRO_ATUALIZACAO_V13.md
git commit -m "Adiciona roteiro de atualização da V13"
git push
```
