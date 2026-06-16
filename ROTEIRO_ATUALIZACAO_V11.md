# Roteiro de atualização — Calculadora Ebola V11

## Objetivo

Atualizar a Calculadora Ebola para a versão V11, revisando as informações técnicas para alinhamento com as notas técnicas oficiais analisadas.

## Fontes consideradas

- Nota Técnica Conjunta nº 160/2026-DEMSP/SVSA/MS e DAHU/SAES/MS.
- Nota Técnica da Bahia sobre DVE — espécie Bundibugyo.
- Nota Técnica de Minas Gerais sobre FHV/Ebola Bundibugyo.
- Nota Técnica DAV nº 12/2026 do Paraná.

## Principais ajustes

- Incubação padrão: 2–21 dias.
- Janela 4–17 dias: mantida apenas como ajuste operacional local.
- Caso suspeito, confirmado e descartado revisados.
- Regra de descarte com segunda amostra quando a primeira coleta ocorrer antes de 72 horas.
- Contactante/comunicante revisado.
- Transmissibilidade após início dos sintomas.
- Contatos pós-óbito mantidos.
- Monitoramento diário por 21 dias após última exposição.
- Notificação imediata em até 24h, SINAN CID A98.4 e comunicação ao CIEVS.
- Fluxo laboratorial em referência nacional/serviço definido na fase de mobilização.
- Sintomas secos/iniciais, sintomas úmidos/tardios e alerta para sangramento/sinais de gravidade revisados.

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

## Passo 3 — Validar

Conferir:

- Padrão de incubação 2–21 dias.
- Botão para janela operacional ajustada 4–17 dias.
- Seção “6. Definições técnicas alinhadas às notas oficiais”.
- Abas: classificação de caso; clínica e sintomas; transmissão e contatos; notificação e laboratório; manejo inicial; janelas e parâmetros.

## Passo 4 — Subir para GitHub

```bat
git status
git add app.py README.md requirements.txt
git commit -m "Alinha definições técnicas às notas oficiais"
git push
```

## Passo 5 — Subir roteiro

```bat
git add ROTEIRO_ATUALIZACAO_V11.md
git commit -m "Adiciona roteiro de atualização da V11"
git push
```
