# Roteiro de atualização — Calculadora Ebola V14

## Objetivo

Remover os contatos fictícios padrão do painel inicial.

## Problema

A ferramenta iniciava com dois contatos fictícios:

- Contato 1
- Contato 2

Isso fazia o painel mostrar 2 contatos mesmo sem planilha importada.

## Correção

A função `default_contacts_df()` agora retorna uma tabela vazia, apenas com as colunas esperadas.

## Resultado esperado

Ao abrir a ferramenta:

- nenhum contato aparece automaticamente;
- o painel fica zerado;
- dados aparecem somente após upload da planilha ou digitação manual.

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
git commit -m "Remove contatos padrão do painel inicial"
git push
```

## Subir roteiro

```bat
git add ROTEIRO_ATUALIZACAO_V14.md
git commit -m "Adiciona roteiro de atualização da V14"
git push
```
