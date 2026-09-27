import pandas as pd
from src.domain.outbreak import OutbreakEvent
from src.services.outbreak_summary import summarize_outbreak

def test_outbreak_summary_counts_operational_categories():
    event = OutbreakEvent("EVT-001", "Evento teste", "MT")
    contacts = pd.DataFrame([
        {"evolucao":"Em monitoramento","caso_origem":"Caso índice","tipo_contato":"Contato domiciliar"},
        {"evolucao":"Sintomático","caso_origem":"Caso índice","tipo_contato":"Velório/funeral"},
        {"evolucao":"Confirmado","caso_origem":"","tipo_contato":"Cuidado direto"},
        {"evolucao":"Óbito","caso_origem":"C002","tipo_contato":"Manipulação do corpo"},
        {"evolucao":"Encerrado","caso_origem":"Caso índice","tipo_contato":"Contato domiciliar"},
    ])
    summary = summarize_outbreak(event, contacts)
    assert summary.total_contacts == 5
    assert summary.active_monitoring == 1
    assert summary.symptomatic_or_suspected == 1
    assert summary.confirmed == 1
    assert summary.deaths == 1
    assert summary.closed_or_discarded == 1
    assert summary.missing_source_case == 1
    assert summary.post_mortem_exposures == 2
