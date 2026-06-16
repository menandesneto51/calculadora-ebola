# Calculadora Ebola — V14

Ferramenta em Python/Streamlit para apoio à investigação epidemiológica de janela provável de exposição, transmissibilidade, óbito, exposição pós-óbito, monitoramento de contatos e possível cadeia de transmissão.

## Atualização V14

Esta versão corrige o comportamento do painel de contatos.

## Problema corrigido

Nas versões anteriores, a função `default_contacts_df()` criava automaticamente dois registros fictícios:

- Contato 1
- Contato 2

Isso fazia o painel exibir contatos mesmo quando nenhuma planilha havia sido importada e nenhum contato real havia sido digitado.

## Correção aplicada

A V14 remove os contatos automáticos.

Agora:

- sem planilha importada;
- sem contato digitado manualmente;

o painel permanece zerado e exibe mensagem orientando o usuário a importar a planilha ou inserir contatos.

## Resultado esperado

Ao abrir a ferramenta pela primeira vez:

- contatos cadastrados = 0;
- não há painel com contagens artificiais;
- os dados aparecem somente após upload da planilha ou digitação manual.

## Mantido da V13

- Correção de datas Excel/Streamlit.
- Incubação padrão: **2–21 dias**.
- Janela 4–17 dias apenas como ajuste operacional local.
- Definições técnicas alinhadas às notas oficiais.
- Óbito e exposição pós-óbito.
- Monitoramento diário por 21 dias após última exposição.

## Executar localmente

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Atualizar no GitHub

```bat
git status
git add app.py README.md requirements.txt
git commit -m "Remove contatos padrão do painel inicial"
git push
```

## Observação final

Ferramenta de apoio técnico. Não substitui definição de caso oficial, investigação de campo, exames laboratoriais, protocolos oficiais, sistema de notificação ou comunicação imediata às autoridades sanitárias.
