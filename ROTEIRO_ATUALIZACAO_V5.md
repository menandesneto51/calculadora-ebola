# Roteiro de atualização — Calculadora Ebola V5

## Objetivo

Atualizar a Calculadora Ebola para a versão V5, com:

- Datas no padrão brasileiro DD/MM/AAAA.
- CSVs exportados em DD/MM/AAAA.
- JSON técnico mantido em AAAA-MM-DD.
- Seção explicativa “Como as datas são calculadas”.
- Manutenção da nomenclatura clínica correta:
  - Sintomas secos (iniciais)
  - Sintomas úmidos (tardios)
  - Sangramento / manifestação hemorrágica como subcategoria operacional.

## Passo 1 — Baixar e extrair o pacote

Baixe o arquivo:

`calculadora_ebola_v5_sistema_completo.zip`

Extraia o conteúdo.

Dentro do ZIP estarão:

- `app.py`
- `README.md`
- `requirements.txt`
- `ATUALIZAR_V5.bat`
- `ROTEIRO_ATUALIZACAO_V5.md`

## Passo 2 — Copiar os arquivos para a pasta local

Copie e substitua estes arquivos na pasta:

`C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola`

Arquivos a substituir:

- `app.py`
- `README.md`
- `requirements.txt`

## Passo 3 — Testar localmente

No CMD:

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Verifique:

- Campos de data em DD/MM/AAAA.
- Tabela de janelas em DD/MM/AAAA.
- CSV de janelas em DD/MM/AAAA.
- CSV de contatos em DD/MM/AAAA.
- Seção “Como as datas são calculadas”.
- Importação da planilha XLSX de contatos.

## Passo 4 — Subir para GitHub manualmente

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"

git status
git add app.py README.md requirements.txt
git commit -m "Padroniza datas no formato brasileiro e documenta cálculo"
git push
```

## Passo 5 — Alternativa automática

Depois de copiar os arquivos, execute:

```bat
ATUALIZAR_V5.bat
```

Esse BAT irá:

1. Ativar o ambiente virtual.
2. Instalar dependências.
3. Testar sintaxe do `app.py`.
4. Fazer commit.
5. Enviar para o GitHub.

## Passo 6 — Conferir no GitHub

Acesse:

`https://github.com/menandesneto51/calculadora-ebola`

Confirme que o README inicia com:

`# Calculadora Ebola — V5`

## Observação importante

O ZIP gerado não deve ser enviado ao GitHub. Ele é apenas pacote de atualização local.
