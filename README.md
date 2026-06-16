# Calculadora Ebola — V15

Ferramenta em Python/Streamlit para apoio à investigação epidemiológica de janela provável de exposição, transmissibilidade, óbito, exposição pós-óbito, monitoramento de contatos e possível cadeia de transmissão.

## Atualização V15

Esta versão melhora a visualização do **mapa de possível cadeia de transmissão**.

## Melhorias visuais aplicadas

- distribuição hierárquica por geração epidemiológica;
- melhor espaçamento vertical entre os nós;
- rótulos curtos no gráfico (somente identificador);
- detalhes completos apenas no hover;
- cores por evolução;
- formas diferentes para tipos de evolução;
- legenda automática;
- destaque visual opcional para contatos pós-óbito;
- filtros por geração e por evolução;
- opção para destacar apenas sintomáticos/suspeitos/confirmados/óbito.

## Resultado esperado

O grafo fica mais limpo e legível, reduzindo sobreposição de rótulos e o efeito de “leque” a partir do caso índice.

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
git commit -m "Melhora visualização da cadeia de transmissão"
git push
```
