# Roteiro de atualização — Calculadora Ebola V9

## Objetivo

Atualizar a Calculadora Ebola para a versão V9, incluindo manejo de óbito e exposição pós-óbito.

## Cenários contemplados

- Paciente vivo/em acompanhamento.
- Paciente que foi a óbito com início dos sintomas conhecido.
- Paciente que foi a óbito com início dos sintomas desconhecido.
- Exposição pós-óbito: manipulação do corpo, transporte, velório/funeral, sepultamento e limpeza/desinfecção.

## Passo 1 — Substituir arquivos

Copie para a pasta:

`C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola`

Substitua:

- `app.py`
- `README.md`
- `requirements.txt`

## Passo 2 — Testar localmente

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"

call .venv\Scripts\activate.bat

python -m pip install -r requirements.txt

python -m streamlit run app.py
```

## Passo 3 — Validar na interface

Conferir se aparecem:

- Situação/desfecho do caso.
- Data do óbito.
- Óbito ocorreu após sintomas?
- Manipulação do corpo.
- Velório/funeral.
- Transporte do corpo.
- Contato pós-óbito identificado.
- Data de sepultamento seguro/fim exposição pós-óbito.
- Data final da exposição em vida.
- Fim operacional da busca de contatos.

## Passo 4 — Subir para GitHub

```bat
git status
git add app.py README.md requirements.txt
git commit -m "Adiciona manejo de óbito e exposição pós-óbito"
git push
```

## Passo 5 — Subir o roteiro, se desejar

```bat
git add ROTEIRO_ATUALIZACAO_V9.md
git commit -m "Adiciona roteiro de atualização da V9"
git push
```

## Passo 6 — Limpeza

Não envie o ZIP para o GitHub.
