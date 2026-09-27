from datetime import date
from src.domain.exposure import Exposure
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
    assert b.infectiousness_compatibility=="compatible"
    assert b.incubation_compatibility=="compatible"
    assert b.generation==2
    assert b.serial_interval_days==9
    assert c.compatibility=="incompatible"
    assert c.infectiousness_compatibility=="incompatible"
    assert c.generation==3

def test_missing_source_is_indeterminate():
    links=analyze_temporal_chain([{"identificador":"X","caso_origem":"UNKNOWN"}])
    assert links[0].compatibility=="indeterminate"
    assert links[0].generation is None

def test_structured_exposure_interval_is_used_for_incubation():
    rows=[
        {"identificador":"A","caso_origem":"Caso índice","data_inicio_sintomas":date(2026,9,1)},
        {"identificador":"B","caso_origem":"A","data_ultimo_contato":date(2026,8,1),"data_inicio_sintomas":date(2026,9,10)},
    ]
    exposures=[Exposure("E1","EV","B","A",date(2026,9,3),date(2026,9,5),"Domiciliar")]
    link=analyze_temporal_chain(rows,exposures)[0]
    assert link.exposure_start==date(2026,9,3)
    assert link.exposure_end==date(2026,9,5)
    assert link.incubation_min_days==5
    assert link.incubation_max_days==7
    assert link.compatibility=="compatible"

def test_incubation_outside_protocol_makes_link_incompatible():
    rows=[
        {"identificador":"A","caso_origem":"Caso índice","data_inicio_sintomas":date(2026,9,1)},
        {"identificador":"B","caso_origem":"A","data_ultimo_contato":date(2026,9,2),"data_inicio_sintomas":date(2026,9,25)},
    ]
    link=analyze_temporal_chain(rows)[0]
    assert link.infectiousness_compatibility=="compatible"
    assert link.incubation_compatibility=="incompatible"
    assert link.compatibility=="incompatible"

def test_missing_target_onset_keeps_incubation_indeterminate():
    rows=[
        {"identificador":"A","caso_origem":"Caso índice","data_inicio_sintomas":date(2026,9,1)},
        {"identificador":"B","caso_origem":"A","data_ultimo_contato":date(2026,9,3)},
    ]
    link=analyze_temporal_chain(rows)[0]
    assert link.infectiousness_compatibility=="compatible"
    assert link.incubation_compatibility=="indeterminate"
    assert link.compatibility=="indeterminate"
