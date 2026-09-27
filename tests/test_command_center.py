from datetime import date
from src.services.command_center import build_command_center

def test_command_center_aggregates_existing_engines():
    rows=[
        {"identificador":"A","caso_origem":"Caso índice","data_ultimo_contato":date(2026,9,1),"tipo_contato":"Domiciliar","evolucao":"Confirmado","data_inicio_sintomas":date(2026,9,2)},
        {"identificador":"B","caso_origem":"A","data_ultimo_contato":date(2026,9,1),"tipo_contato":"Domiciliar","evolucao":"Sintomático","data_inicio_sintomas":date(2026,9,10)},
    ]
    s=build_command_center(rows,[],date(2026,9,26))
    assert s.contacts==2
    assert s.confirmed==1
    assert s.symptomatic_or_suspected==1
    assert s.monitoring_overdue==2
    assert s.incompatible_links==1


def test_command_center_blocks_promotion_on_structural_error():
    rows=[
        {"identificador":"A","caso_origem":"Caso índice","data_ultimo_contato":date(2026,9,1),"tipo_contato":"Domiciliar","evolucao":"Em monitoramento"},
        {"identificador":"A","caso_origem":"Caso índice","data_ultimo_contato":date(2026,9,2),"tipo_contato":"Domiciliar","evolucao":"Em monitoramento"},
    ]
    summary=build_command_center(rows,[],date(2026,9,3))
    assert summary.promotion_allowed is False
    assert summary.blocking_issues>=1
    assert "DUPLICATE_CONTACT" in summary.blocking_codes

def test_command_center_allows_promotion_without_blocking_errors():
    rows=[{"identificador":"A","caso_origem":"Caso índice","data_ultimo_contato":date(2026,9,1),"tipo_contato":"Domiciliar","evolucao":"Em monitoramento"}]
    summary=build_command_center(rows,[],date(2026,9,3))
    assert summary.promotion_allowed is True
    assert summary.blocking_issues==0
