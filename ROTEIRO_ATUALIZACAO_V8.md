# Roteiro de atualização — Calculadora Ebola V8

## Objetivo

Atualizar a Calculadora Ebola para a versão V8, incluindo cálculo para paciente detectado já em fase posterior.

## Cenários contemplados

A ferramenta passa a contemplar:

- Paciente detectado com sintomas secos/iniciais.
- Paciente detectado com sintomas úmidos/tardios.
- Paciente detectado com sinais de gravidade.
- Paciente detectado com sangramento observado.
- Paciente identificado por óbito.

## Lógica nova

Quando a data de início dos sintomas é conhecida, a ferramenta usa essa data diretamente.

Quando a data de início dos sintomas não é conhecida, a ferramenta estima retrospectivamente o início dos sintomas com base na condição clínica observada na detecção.

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

Conferir se aparecem os campos:

- Data da última exposição.
- Data da detecção/avaliação.
- Condição clínica observada na detecção.
- Data de início dos sintomas é conhecida?
- Data real/estimada de início dos sintomas, quando aplicável.
- Data final para busca de contatos.
- Alerta para sintomas úmidos/tardios.
- Alerta para sangramento/sinais de gravidade.

## Passo 4 — Subir para GitHub

```bat
git status
git add app.py README.md requirements.txt
git commit -m "Adiciona cálculo para detecção em fase posterior"
git push
```

## Passo 5 — Subir o roteiro, se desejar

```bat
git add ROTEIRO_ATUALIZACAO_V8.md
git commit -m "Adiciona roteiro de atualização da V8"
git push
```

## Passo 6 — Limpeza

Não envie o arquivo ZIP para o GitHub. Ele é apenas pacote de atualização.
