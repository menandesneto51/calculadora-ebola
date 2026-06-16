# Calculadora Ebola — V11

Ferramenta em Python/Streamlit para apoio à investigação epidemiológica de janela provável de exposição, transmissibilidade, óbito, exposição pós-óbito, monitoramento de contatos e possível cadeia de transmissão.

## Atualização V11

Esta versão revisa as informações técnicas da ferramenta para alinhamento com:

- Nota Técnica Conjunta nº 160/2026-DEMSP/SVSA/MS e DAHU/SAES/MS.
- Nota Técnica da Bahia sobre vigilância epidemiológica da DVE — espécie Bundibugyo.
- Nota Técnica de Minas Gerais sobre FHV/Ebola Bundibugyo.
- Nota Técnica DAV nº 12/2026 do Paraná — fluxo de atendimento de casos suspeitos de Ebola.

## Principais ajustes

- Incubação padrão alterada para **2–21 dias**, conforme notas técnicas.
- Janela **4–17 dias** mantida apenas como ajuste operacional local.
- Definição de caso suspeito alinhada ao critério de 21 dias antes do início dos sintomas + febre e/ou calafrios com manifestações compatíveis.
- Caso confirmado definido por PCR/RT-PCR ou sequenciamento em laboratório de referência.
- Caso descartado inclui regra de segunda amostra quando a primeira coleta ocorrer antes de 72 horas do início dos sintomas.
- Contactante/comunicante definido como assintomático com contato direto ou indireto durante período sintomático, inclusive após óbito.
- Transmissibilidade reforçada como, em geral, após início dos sintomas; a nota do Paraná explicita que apenas pacientes sintomáticos transmitem.
- Sangramento mantido como alerta de gravidade, não etapa obrigatória.
- Exposição em voo incluída: mesma fileira, fileira imediatamente à frente e fileira imediatamente atrás.
- Notificação imediata em até 24h, SINAN CID A98.4 e comunicação ao CIEVS.
- Monitoramento diário dos contatos por 21 dias após última exposição.
- Coleta laboratorial apenas conforme fluxo nacional e em serviço de referência na fase de mobilização.

## Observação

As definições incluídas são operacionais e servem para apoiar o uso da ferramenta. A classificação oficial deve seguir a nota técnica, guia, protocolo ou definição de caso vigente da autoridade sanitária responsável pelo evento.

## Executar localmente

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Atualizar no GitHub manualmente

```bat
cd /d "C:\Users\Menandesneto\OneDrive\Área de Trabalho\calculadora Ebola"
git status
git add app.py README.md requirements.txt
git commit -m "Alinha definições técnicas às notas oficiais"
git push
```

## Observação final

Ferramenta de apoio técnico. Não substitui definição de caso oficial, investigação de campo, exames laboratoriais, protocolos oficiais, sistema de notificação ou comunicação imediata às autoridades sanitárias.
