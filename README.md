# Calculadora Ebola — V16

## Atualização V16

Esta versão adiciona filtros avançados, agrupamento automático e exportação ao mapa de possível cadeia de transmissão.

### Novidades

- ocultar assintomáticos, encerrados e descartados;
- mostrar apenas sintomáticos, suspeitos, confirmados e óbitos;
- agrupar contatos numerosos de menor prioridade visual;
- definir limiar de agrupamento;
- exportar nós em CSV;
- exportar vínculos em CSV;
- exportar grafo em HTML interativo;
- exportar grafo em PNG quando houver suporte pelo pacote `kaleido`.

## Executar

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Subir ao GitHub

```bat
git status
git add app.py README.md requirements.txt
git commit -m "Adiciona filtros exportação e agrupamento ao grafo"
git push
```
