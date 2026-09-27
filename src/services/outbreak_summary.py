"""Resumo agregado do evento para CIEVS/SIS."""
from dataclasses import dataclass

import pandas as pd

from src.domain.outbreak import OutbreakEvent

@dataclass(frozen=True)
class OutbreakSummary:
    event_id: str
    total_contacts: int
    active_monitoring: int
    symptomatic_or_suspected: int
    confirmed: int
    deaths: int
    closed_or_discarded: int
    missing_source_case: int
    post_mortem_exposures: int

def summarize_outbreak(event: OutbreakEvent, contacts: pd.DataFrame) -> OutbreakSummary:
    event.validate()
    if contacts.empty:
        return OutbreakSummary(event.event_id, 0, 0, 0, 0, 0, 0, 0, 0)

    evolution = contacts.get("evolucao", pd.Series("", index=contacts.index)).fillna("").astype(str)
    source = contacts.get("caso_origem", pd.Series("", index=contacts.index)).fillna("").astype(str).str.strip()
    exposure_type = contacts.get("tipo_contato", pd.Series("", index=contacts.index)).fillna("").astype(str)

    post_mortem_types = {"Manipulação do corpo", "Velório/funeral", "Sepultamento", "Limpeza/desinfecção"}

    return OutbreakSummary(
        event_id=event.event_id,
        total_contacts=len(contacts),
        active_monitoring=int(evolution.eq("Em monitoramento").sum()),
        symptomatic_or_suspected=int(evolution.isin(["Sintomático", "Suspeito"]).sum()),
        confirmed=int(evolution.eq("Confirmado").sum()),
        deaths=int(evolution.eq("Óbito").sum()),
        closed_or_discarded=int(evolution.isin(["Encerrado", "Descartado"]).sum()),
        missing_source_case=int(source.eq("").sum()),
        post_mortem_exposures=int(exposure_type.isin(post_mortem_types).sum()),
    )
