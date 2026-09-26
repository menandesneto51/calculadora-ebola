from datetime import date
from src.services.temporal_chain import analyze_temporal_chain

def test_temporal_chain_compatibility_generation_and_serial_interval():
    rows=[
        {"identificador":"A","caso_origem":"Caso índice","data_inicio_sintomas":date(2026,9,1)},
        {"identificador":"B","caso_origem":"A","data_ultimo_contato":date(2026,9,3),"data_inicio_sintomas":date(2026,9,10)},
        {"identificador":"C","caso_origem":"B","data_ultimo_contato":date(2026,9,5),"data_inicio_sintomas":date(2026,9,15)},
    ]
    links=analyze_temporal_chain(rows)
    b=next(x for x in links if x.target_id=="B")
    c=next(x for x in links if x.target_id=="C")
    assert b.compatibility=="compatible"
    assert b.generation==2
    assert b.serial_interval_days==9
    assert c.compatibility=="incompatible"
    assert c.generation==3

def test_missing_source_is_indeterminate():
    links=analyze_temporal_chain([{"identificador":"X","caso_origem":"UNKNOWN"}])
    assert links[0].compatibility=="indeterminate"
    assert links[0].generation is None
