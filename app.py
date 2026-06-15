from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# Modelos, parâmetros e opções
# ============================================================

@dataclass(frozen=True)
class CalculatorParams:
    min_incubation_days: int = 4
    max_incubation_days: int = 17
    wet_symptom_offset_days: int = 4
    severe_alert_offset_days: int = 5
    death_offset_days: int = 10
    contact_monitoring_days: int = 21


@dataclass(frozen=True)
class CaseCalculation:
    last_exposure_date: date | None
    detection_date: date
    clinical_condition_at_detection: str
    case_status: str
    death_date: date | None
    death_after_symptoms: str
    body_manipulation: str
    funeral_or_wake: str
    body_transport: str
    post_mortem_contact: str
    safe_burial_or_post_mortem_end_date: date | None
    live_exposure_end_date: date
    operational_contact_search_end_date: date
    onset_known: bool
    symptom_onset_status: str
    symptom_onset_date: date
    onset_estimation_method: str
    estimate_confidence: str
    exposure_window_start: date
    exposure_window_end: date
    symptom_window_from_exposure_start: date | None
    symptom_window_from_exposure_end: date | None
    exposure_onset_compatibility: str
    wet_symptom_alert_date: date
    severe_alert_date: date
    transmission_start: date
    observation: str


CASE_STATUS_OPTIONS = ["Vivo/em acompanhamento", "Óbito", "Ignorado"]

DEATH_AFTER_SYMPTOMS_OPTIONS = ["Sim", "Não", "Desconhecido", "Não se aplica"]

YES_NO_UNKNOWN = ["Não", "Sim", "Desconhecido"]

EVOLUTION_OPTIONS = [
    "Em monitoramento",
    "Assintomático",
    "Sintomático",
    "Suspeito",
    "Confirmado",
    "Descartado",
    "Óbito",
    "Encerrado",
]

RISK_OPTIONS = ["Não classificado", "Baixo", "Moderado", "Alto"]

ONSET_STATUS_OPTIONS = [
    "Data real observada",
    "Data estimada pela investigação",
    "Data aproximada/informada indiretamente",
]

CLINICAL_CONDITION_OPTIONS = [
    "Sintomas secos/iniciais",
    "Sintomas úmidos/tardios",
    "Sinais de gravidade",
    "Sangramento observado",
    "Óbito",
    "Sem informação clínica suficiente",
]

EXPOSURE_TYPE_OPTIONS = [
    "",
    "Contato domiciliar",
    "Cuidado direto",
    "Serviço de saúde",
    "Laboratório",
    "Transporte do paciente",
    "Contato com fluidos",
    "Manipulação do corpo",
    "Velório/funeral",
    "Sepultamento",
    "Limpeza/desinfecção",
    "Comunidade/evento",
    "Outro",
]


# ============================================================
# Funções utilitárias
# ============================================================

def clean_text(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def coerce_date(value) -> date | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, date):
        return value
    try:
        return pd.to_datetime(value, dayfirst=True).date()
    except Exception:
        try:
            return pd.to_datetime(value).date()
        except Exception:
            return None


def fmt_br(value) -> str:
    dt = coerce_date(value)
    return dt.strftime("%d/%m/%Y") if dt else ""


def format_date_columns_br(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    formatted = df.copy()
    for col in columns:
        if col in formatted.columns:
            formatted[col] = pd.to_datetime(formatted[col], errors="coerce").dt.strftime("%d/%m/%Y")
            formatted[col] = formatted[col].replace("NaT", "")
    return formatted


def date_or_none_to_iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def max_date_or_none(values: list[date | None]) -> date | None:
    valid = [v for v in values if v is not None]
    return max(valid) if valid else None


# ============================================================
# Cálculo do caso índice
# ============================================================

def validate_params(params: CalculatorParams) -> None:
    if params.min_incubation_days > params.max_incubation_days:
        raise ValueError("A incubação mínima não pode ser maior que a incubação máxima.")
    if params.contact_monitoring_days < params.max_incubation_days:
        st.warning(
            "Atenção: o período de monitoramento de contatos está menor que a incubação máxima usada no cálculo."
        )


def estimate_onset_from_detection(
    detection_date: date,
    clinical_condition: str,
    params: CalculatorParams,
) -> tuple[date, str, str]:
    if clinical_condition == "Sintomas secos/iniciais":
        return (
            detection_date,
            "Início dos sintomas estimado como a própria data de detecção, pois a condição observada foi de sintomas secos/iniciais.",
            "Moderada",
        )

    if clinical_condition == "Sintomas úmidos/tardios":
        return (
            detection_date - timedelta(days=params.wet_symptom_offset_days),
            "Início dos sintomas estimado retrospectivamente a partir da detecção com sintomas úmidos/tardios.",
            "Moderada",
        )

    if clinical_condition in ["Sinais de gravidade", "Sangramento observado"]:
        return (
            detection_date - timedelta(days=params.severe_alert_offset_days),
            "Início dos sintomas estimado retrospectivamente a partir da detecção com sinais de gravidade/sangramento observado.",
            "Baixa a moderada",
        )

    if clinical_condition == "Óbito":
        return (
            detection_date - timedelta(days=params.death_offset_days),
            "Início dos sintomas estimado retrospectivamente a partir da data de óbito.",
            "Baixa a moderada",
        )

    raise ValueError(
        "Informação clínica insuficiente para estimar o início dos sintomas. Informe a data de início dos sintomas ou selecione uma condição clínica válida."
    )


def calculate_operational_contact_search_end(
    case_status: str,
    live_exposure_end_date: date,
    death_date: date | None,
    safe_burial_or_post_mortem_end_date: date | None,
) -> date:
    if case_status == "Óbito":
        return max_date_or_none(
            [live_exposure_end_date, death_date, safe_burial_or_post_mortem_end_date]
        ) or live_exposure_end_date

    return live_exposure_end_date


def calculate_case(
    last_exposure_date: date | None,
    detection_date: date,
    clinical_condition_at_detection: str,
    case_status: str,
    death_date: date | None,
    death_after_symptoms: str,
    body_manipulation: str,
    funeral_or_wake: str,
    body_transport: str,
    post_mortem_contact: str,
    safe_burial_or_post_mortem_end_date: date | None,
    live_exposure_end_date: date,
    onset_known: bool,
    known_symptom_onset_date: date | None,
    symptom_onset_status: str,
    params: CalculatorParams,
) -> CaseCalculation:
    validate_params(params)

    if case_status == "Óbito" and death_date is None:
        raise ValueError("Informe a data do óbito quando a situação do caso for óbito.")

    operational_end = calculate_operational_contact_search_end(
        case_status=case_status,
        live_exposure_end_date=live_exposure_end_date,
        death_date=death_date,
        safe_burial_or_post_mortem_end_date=safe_burial_or_post_mortem_end_date,
    )

    if onset_known:
        if known_symptom_onset_date is None:
            raise ValueError("Informe a data de início dos sintomas quando marcar início conhecido.")
        symptom_onset_date = known_symptom_onset_date
        onset_estimation_method = (
            "Data de início dos sintomas informada diretamente como real, estimada ou aproximada pela investigação."
        )
        estimate_confidence = "Alta, se a data foi observada; moderada, se estimada/aproximada."
    else:
        if case_status == "Óbito" and death_after_symptoms in ["Sim", "Desconhecido"]:
            symptom_onset_date = death_date - timedelta(days=params.death_offset_days)  # type: ignore[operator]
            onset_estimation_method = (
                "Início dos sintomas estimado retrospectivamente pela data do óbito, pois o caso evoluiu a óbito com sintomas ou com informação sintomática desconhecida."
            )
            estimate_confidence = "Baixa a moderada"
            symptom_onset_status = "Estimado retrospectivamente pela data do óbito"
        elif case_status == "Óbito" and death_after_symptoms == "Não" and clinical_condition_at_detection == "Óbito":
            raise ValueError(
                "Óbito sem sintomas conhecidos não permite estimar início dos sintomas apenas pela data de óbito. Informe dados clínicos ou uma data estimada de início dos sintomas."
            )
        else:
            symptom_onset_date, onset_estimation_method, estimate_confidence = estimate_onset_from_detection(
                detection_date=detection_date,
                clinical_condition=clinical_condition_at_detection,
                params=params,
            )
            symptom_onset_status = "Estimado retrospectivamente pela condição clínica na detecção"

    exposure_window_start = symptom_onset_date - timedelta(days=params.max_incubation_days)
    exposure_window_end = symptom_onset_date - timedelta(days=params.min_incubation_days)

    symptom_window_from_exposure_start = None
    symptom_window_from_exposure_end = None
    compatibility = "Não avaliado: data da última exposição não informada."

    if last_exposure_date is not None:
        symptom_window_from_exposure_start = last_exposure_date + timedelta(days=params.min_incubation_days)
        symptom_window_from_exposure_end = last_exposure_date + timedelta(days=params.max_incubation_days)

        if symptom_window_from_exposure_start <= symptom_onset_date <= symptom_window_from_exposure_end:
            compatibility = "Compatível: início dos sintomas dentro da janela esperada após a última exposição."
        else:
            compatibility = "Fora da janela esperada: revisar data de exposição, data de sintomas ou parâmetros."

    wet_symptom_alert_date = symptom_onset_date + timedelta(days=params.wet_symptom_offset_days)
    severe_alert_date = symptom_onset_date + timedelta(days=params.severe_alert_offset_days)

    if operational_end < symptom_onset_date:
        observation = (
            "A data final operacional da busca de contatos está anterior ao início dos sintomas. "
            "Revisar a data final de exposição em vida ou pós-óbito."
        )
    elif case_status == "Óbito":
        observation = (
            "Óbito registrado como desfecho. Se houve manipulação do corpo, transporte, velório/funeral, sepultamento ou contato pós-óbito, "
            "a busca de contatos deve considerar exposições até a data de sepultamento seguro ou encerramento da exposição pós-óbito."
        )
    else:
        observation = (
            "Cálculo realizado a partir da data de início dos sintomas, quando conhecida, ou estimada retrospectivamente pela condição clínica na detecção. "
            "Os marcos evolutivos são alertas operacionais, não etapas obrigatórias."
        )

    return CaseCalculation(
        last_exposure_date=last_exposure_date,
        detection_date=detection_date,
        clinical_condition_at_detection=clinical_condition_at_detection,
        case_status=case_status,
        death_date=death_date,
        death_after_symptoms=death_after_symptoms,
        body_manipulation=body_manipulation,
        funeral_or_wake=funeral_or_wake,
        body_transport=body_transport,
        post_mortem_contact=post_mortem_contact,
        safe_burial_or_post_mortem_end_date=safe_burial_or_post_mortem_end_date,
        live_exposure_end_date=live_exposure_end_date,
        operational_contact_search_end_date=operational_end,
        onset_known=onset_known,
        symptom_onset_status=symptom_onset_status,
        symptom_onset_date=symptom_onset_date,
        onset_estimation_method=onset_estimation_method,
        estimate_confidence=estimate_confidence,
        exposure_window_start=exposure_window_start,
        exposure_window_end=exposure_window_end,
        symptom_window_from_exposure_start=symptom_window_from_exposure_start,
        symptom_window_from_exposure_end=symptom_window_from_exposure_end,
        exposure_onset_compatibility=compatibility,
        wet_symptom_alert_date=wet_symptom_alert_date,
        severe_alert_date=severe_alert_date,
        transmission_start=symptom_onset_date,
        observation=observation,
    )


def case_to_df(case: CaseCalculation) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "data da última exposição": case.last_exposure_date,
                "data da detecção/avaliação": case.detection_date,
                "condição clínica observada na detecção": case.clinical_condition_at_detection,
                "situação do caso": case.case_status,
                "data do óbito": case.death_date,
                "óbito ocorreu após sintomas?": case.death_after_symptoms,
                "manipulação do corpo": case.body_manipulation,
                "velório/funeral": case.funeral_or_wake,
                "transporte do corpo": case.body_transport,
                "contato pós-óbito identificado": case.post_mortem_contact,
                "data de sepultamento seguro/fim exposição pós-óbito": case.safe_burial_or_post_mortem_end_date,
                "data final da exposição em vida": case.live_exposure_end_date,
                "fim operacional da busca de contatos": case.operational_contact_search_end_date,
                "início dos sintomas conhecido?": "Sim" if case.onset_known else "Não",
                "início real/estimado dos sintomas": case.symptom_onset_date,
                "tipo da data de sintomas": case.symptom_onset_status,
                "método usado para definir início dos sintomas": case.onset_estimation_method,
                "confiança da estimativa": case.estimate_confidence,
                "início provável da exposição/infecção": case.exposure_window_start,
                "fim provável da exposição/infecção": case.exposure_window_end,
                "início possível de sintomas pela última exposição": case.symptom_window_from_exposure_start,
                "fim possível de sintomas pela última exposição": case.symptom_window_from_exposure_end,
                "compatibilidade exposição-sintomas": case.exposure_onset_compatibility,
                "alerta para sintomas úmidos/tardios": case.wet_symptom_alert_date,
                "alerta para sangramento/sinais de gravidade": case.severe_alert_date,
                "início da janela transmissível": case.transmission_start,
                "observação": case.observation,
            }
        ]
    )


def make_case_timeline(case: CaseCalculation) -> pd.DataFrame:
    rows = [
        {
            "item": "Caso índice",
            "fase": "Janela provável de exposição/infecção",
            "início": case.exposure_window_start,
            "fim": case.exposure_window_end + timedelta(days=1),
        },
        {
            "item": "Caso índice",
            "fase": "Janela operacional de transmissibilidade/busca de contatos",
            "início": case.transmission_start,
            "fim": case.operational_contact_search_end_date + timedelta(days=1),
        },
        {
            "item": "Marcos clínicos/operacionais",
            "fase": "Data da detecção/avaliação",
            "início": case.detection_date,
            "fim": case.detection_date + timedelta(days=1),
        },
        {
            "item": "Marcos clínicos/operacionais",
            "fase": "Início real/estimado dos sintomas",
            "início": case.symptom_onset_date,
            "fim": case.symptom_onset_date + timedelta(days=1),
        },
        {
            "item": "Marcos clínicos/operacionais",
            "fase": "Alerta para sintomas úmidos/tardios",
            "início": case.wet_symptom_alert_date,
            "fim": case.wet_symptom_alert_date + timedelta(days=1),
        },
        {
            "item": "Marcos clínicos/operacionais",
            "fase": "Alerta para sangramento/sinais de gravidade",
            "início": case.severe_alert_date,
            "fim": case.severe_alert_date + timedelta(days=1),
        },
        {
            "item": "Exposição em vida",
            "fase": "Data final da exposição em vida",
            "início": case.live_exposure_end_date,
            "fim": case.live_exposure_end_date + timedelta(days=1),
        },
    ]

    if case.last_exposure_date is not None:
        rows.append(
            {
                "item": "Exposição informada",
                "fase": "Data da última exposição",
                "início": case.last_exposure_date,
                "fim": case.last_exposure_date + timedelta(days=1),
            }
        )

    if case.symptom_window_from_exposure_start is not None and case.symptom_window_from_exposure_end is not None:
        rows.append(
            {
                "item": "Exposição informada",
                "fase": "Janela possível de início de sintomas pela última exposição",
                "início": case.symptom_window_from_exposure_start,
                "fim": case.symptom_window_from_exposure_end + timedelta(days=1),
            }
        )

    if case.case_status == "Óbito" and case.death_date is not None:
        rows.append(
            {
                "item": "Óbito e pós-óbito",
                "fase": "Data do óbito",
                "início": case.death_date,
                "fim": case.death_date + timedelta(days=1),
            }
        )

    if case.case_status == "Óbito" and case.safe_burial_or_post_mortem_end_date is not None:
        rows.append(
            {
                "item": "Óbito e pós-óbito",
                "fase": "Sepultamento seguro/fim exposição pós-óbito",
                "início": case.safe_burial_or_post_mortem_end_date,
                "fim": case.safe_burial_or_post_mortem_end_date + timedelta(days=1),
            }
        )

    return pd.DataFrame(rows)


def case_to_iso_payload(case: CaseCalculation, params: CalculatorParams) -> dict:
    return {
        "params": asdict(params),
        "case": {
            "last_exposure_date": date_or_none_to_iso(case.last_exposure_date),
            "detection_date": case.detection_date.isoformat(),
            "clinical_condition_at_detection": case.clinical_condition_at_detection,
            "case_status": case.case_status,
            "death_date": date_or_none_to_iso(case.death_date),
            "death_after_symptoms": case.death_after_symptoms,
            "body_manipulation": case.body_manipulation,
            "funeral_or_wake": case.funeral_or_wake,
            "body_transport": case.body_transport,
            "post_mortem_contact": case.post_mortem_contact,
            "safe_burial_or_post_mortem_end_date": date_or_none_to_iso(case.safe_burial_or_post_mortem_end_date),
            "live_exposure_end_date": case.live_exposure_end_date.isoformat(),
            "operational_contact_search_end_date": case.operational_contact_search_end_date.isoformat(),
            "onset_known": case.onset_known,
            "symptom_onset_status": case.symptom_onset_status,
            "symptom_onset_date": case.symptom_onset_date.isoformat(),
            "onset_estimation_method": case.onset_estimation_method,
            "estimate_confidence": case.estimate_confidence,
            "exposure_window_start": case.exposure_window_start.isoformat(),
            "exposure_window_end": case.exposure_window_end.isoformat(),
            "symptom_window_from_exposure_start": date_or_none_to_iso(case.symptom_window_from_exposure_start),
            "symptom_window_from_exposure_end": date_or_none_to_iso(case.symptom_window_from_exposure_end),
            "exposure_onset_compatibility": case.exposure_onset_compatibility,
            "wet_symptom_alert_date": case.wet_symptom_alert_date.isoformat(),
            "severe_alert_date": case.severe_alert_date.isoformat(),
            "transmission_start": case.transmission_start.isoformat(),
            "observation": case.observation,
        },
    }


# ============================================================
# Contatos e cadeia de transmissão
# ============================================================

def default_contacts_df() -> pd.DataFrame:
    today = date.today()
    return pd.DataFrame(
        [
            {
                "identificador": "Contato 1",
                "nome_codigo": "",
                "caso_origem": "Caso índice",
                "data_ultimo_contato": today,
                "tipo_contato": "Contato domiciliar",
                "municipio": "",
                "risco": "Não classificado",
                "evolucao": "Em monitoramento",
                "data_inicio_sintomas": None,
                "data_fim_transmissibilidade": None,
                "data_ultima_avaliacao": today,
                "observacao": "",
            },
            {
                "identificador": "Contato 2",
                "nome_codigo": "",
                "caso_origem": "Caso índice",
                "data_ultimo_contato": today,
                "tipo_contato": "Velório/funeral",
                "municipio": "",
                "risco": "Não classificado",
                "evolucao": "Em monitoramento",
                "data_inicio_sintomas": None,
                "data_fim_transmissibilidade": None,
                "data_ultima_avaliacao": today,
                "observacao": "",
            },
        ]
    )


def normalize_contacts_df(df: pd.DataFrame) -> pd.DataFrame:
    expected_columns = list(default_contacts_df().columns)
    normalized = df.copy()

    for col in expected_columns:
        if col not in normalized.columns:
            normalized[col] = None

    normalized = normalized[expected_columns]

    for col in [
        "identificador",
        "nome_codigo",
        "caso_origem",
        "tipo_contato",
        "municipio",
        "risco",
        "evolucao",
        "observacao",
    ]:
        normalized[col] = normalized[col].apply(clean_text)

    normalized["risco"] = normalized["risco"].replace("", "Não classificado")
    normalized["evolucao"] = normalized["evolucao"].replace("", "Em monitoramento")
    normalized["caso_origem"] = normalized["caso_origem"].replace("", "Caso índice")

    for col in [
        "data_ultimo_contato",
        "data_inicio_sintomas",
        "data_fim_transmissibilidade",
        "data_ultima_avaliacao",
    ]:
        normalized[col] = normalized[col].apply(coerce_date)

    normalized = normalized[normalized["identificador"] != ""].copy()
    normalized = normalized.drop_duplicates(subset=["identificador"], keep="first").reset_index(drop=True)
    return normalized


def read_uploaded_contacts(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return default_contacts_df()

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return normalize_contacts_df(pd.read_csv(uploaded_file))

    if file_name.endswith((".xlsx", ".xls")):
        try:
            return normalize_contacts_df(pd.read_excel(uploaded_file, sheet_name="Contatos_Importar"))
        except Exception:
            return normalize_contacts_df(pd.read_excel(uploaded_file))

    raise ValueError("Formato não suportado. Use CSV ou XLSX.")


def calculate_contact_generation(contacts: pd.DataFrame) -> dict[str, int]:
    nodes = {"Caso índice"}
    edges = []

    for _, row in contacts.iterrows():
        child = clean_text(row.get("identificador"))
        parent = clean_text(row.get("caso_origem")) or "Caso índice"
        if not child:
            continue
        nodes.add(parent)
        nodes.add(child)
        edges.append((parent, child))

    generation = {"Caso índice": 0}
    changed = True
    while changed:
        changed = False
        for parent, child in edges:
            if parent in generation and child not in generation:
                generation[child] = generation[parent] + 1
                changed = True

    for node in nodes:
        if node not in generation:
            generation[node] = 1

    return generation


def is_contact_compatible_with_source(
    source_id: str,
    last_contact: date,
    contacts_by_id: dict[str, dict],
    case: CaseCalculation,
) -> tuple[str, str]:
    source_id = clean_text(source_id) or "Caso índice"

    if source_id == "Caso índice":
        if case.transmission_start <= last_contact <= case.operational_contact_search_end_date:
            return "Sim", f"{fmt_br(case.transmission_start)} a {fmt_br(case.operational_contact_search_end_date)}"
        return "Não", "-"

    source = contacts_by_id.get(source_id)
    if source is None:
        return "Não avaliado", "Caso-origem não localizado"

    source_onset = coerce_date(source.get("data_inicio_sintomas"))
    source_end = coerce_date(source.get("data_fim_transmissibilidade"))

    if source_onset is None or source_end is None:
        return "Não avaliado", "Informe início de sintomas e fim de transmissibilidade do caso-origem"

    if source_onset <= last_contact <= source_end:
        return "Sim", f"{fmt_br(source_onset)} a {fmt_br(source_end)}"

    return "Não", "-"


def evaluate_contacts(
    contacts_df: pd.DataFrame,
    case: CaseCalculation,
    params: CalculatorParams,
) -> pd.DataFrame:
    contacts = normalize_contacts_df(contacts_df)
    contacts_by_id = contacts.set_index("identificador").to_dict(orient="index") if not contacts.empty else {}
    generations = calculate_contact_generation(contacts)
    evaluated_rows = []
    today = date.today()

    for _, row in contacts.iterrows():
        identifier = clean_text(row.get("identificador"))
        source = clean_text(row.get("caso_origem")) or "Caso índice"
        last_contact = coerce_date(row.get("data_ultimo_contato"))
        onset = coerce_date(row.get("data_inicio_sintomas"))
        evolution = clean_text(row.get("evolucao")) or "Em monitoramento"

        base_row = {
            "geração": generations.get(identifier, 1),
            "identificador": identifier,
            "nome/código": clean_text(row.get("nome_codigo")),
            "caso-origem": source,
            "data do último contato": last_contact,
            "tipo de contato": clean_text(row.get("tipo_contato")),
            "município": clean_text(row.get("municipio")),
            "risco": clean_text(row.get("risco")) or "Não classificado",
            "evolução": evolution,
            "data de início dos sintomas": onset,
            "data da última avaliação": coerce_date(row.get("data_ultima_avaliacao")),
            "observação": clean_text(row.get("observacao")),
        }

        if last_contact is None:
            evaluated_rows.append(
                {
                    **base_row,
                    "compatível com janela transmissível?": "Data inválida/ausente",
                    "hipóteses/janela compatível": "-",
                    "possível início de sintomas": "-",
                    "monitorar até": "-",
                    "situação do prazo": "Não avaliado",
                }
            )
            continue

        compatible_label, compatible_detail = is_contact_compatible_with_source(
            source_id=source,
            last_contact=last_contact,
            contacts_by_id=contacts_by_id,
            case=case,
        )

        symptom_window_start = last_contact + timedelta(days=params.min_incubation_days)
        symptom_window_end = last_contact + timedelta(days=params.max_incubation_days)
        monitoring_end = last_contact + timedelta(days=params.contact_monitoring_days)

        if evolution in ["Encerrado", "Descartado"]:
            deadline_status = "Encerrado"
        elif evolution in ["Sintomático", "Suspeito", "Confirmado", "Óbito"]:
            deadline_status = "Requer avaliação/ação"
        elif today > monitoring_end:
            deadline_status = "Prazo concluído"
        else:
            days_left = (monitoring_end - today).days
            deadline_status = f"Em monitoramento: faltam {days_left} dia(s)"

        if onset is not None:
            onset_compatible = symptom_window_start <= onset <= symptom_window_end
            onset_text = (
                f"{fmt_br(symptom_window_start)} a {fmt_br(symptom_window_end)} "
                f"({'compatível' if onset_compatible else 'fora da janela'})"
            )
        else:
            onset_text = f"{fmt_br(symptom_window_start)} a {fmt_br(symptom_window_end)}"

        evaluated_rows.append(
            {
                **base_row,
                "compatível com janela transmissível?": compatible_label,
                "hipóteses/janela compatível": compatible_detail,
                "possível início de sintomas": onset_text,
                "monitorar até": monitoring_end,
                "situação do prazo": deadline_status,
            }
        )

    return pd.DataFrame(evaluated_rows)


def make_contacts_timeline(evaluated_contacts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if evaluated_contacts.empty:
        return pd.DataFrame(columns=["identificador", "fase", "início", "fim"])

    for _, row in evaluated_contacts.iterrows():
        contact_date = coerce_date(row.get("data do último contato"))
        monitoring_end = coerce_date(row.get("monitorar até"))
        if contact_date is None or monitoring_end is None:
            continue

        possible_text = clean_text(row.get("possível início de sintomas")).split(" (")[0]
        try:
            start_text, end_text = possible_text.split(" a ")
            symptom_start = pd.to_datetime(start_text, dayfirst=True).date()
            symptom_end = pd.to_datetime(end_text, dayfirst=True).date()
        except Exception:
            continue

        rows.extend(
            [
                {
                    "identificador": row.get("identificador"),
                    "fase": "Possível início de sintomas",
                    "início": symptom_start,
                    "fim": symptom_end + timedelta(days=1),
                },
                {
                    "identificador": row.get("identificador"),
                    "fase": "Monitoramento operacional",
                    "início": contact_date,
                    "fim": monitoring_end + timedelta(days=1),
                },
            ]
        )

    return pd.DataFrame(rows)


def make_chain_edges(contacts_df: pd.DataFrame) -> pd.DataFrame:
    contacts = normalize_contacts_df(contacts_df)
    rows = []
    for _, row in contacts.iterrows():
        child = clean_text(row.get("identificador"))
        parent = clean_text(row.get("caso_origem")) or "Caso índice"
        if not child:
            continue
        rows.append(
            {
                "caso-origem": parent,
                "contato/caso exposto": child,
                "data do contato": coerce_date(row.get("data_ultimo_contato")),
                "tipo de contato": clean_text(row.get("tipo_contato")),
                "município": clean_text(row.get("municipio")),
                "evolução": clean_text(row.get("evolucao")),
            }
        )
    return pd.DataFrame(rows)


# ============================================================
# Interface Streamlit
# ============================================================

def configure_page() -> None:
    st.set_page_config(page_title="Calculadora Ebola", page_icon="🦠", layout="wide")
    st.title("Calculadora Ebola")
    st.caption(
        "Janela provável de exposição, óbito, exposição pós-óbito, início dos sintomas, marcos evolutivos, contatos e cadeia provável."
    )


def sidebar_params() -> CalculatorParams:
    with st.sidebar:
        st.header("Parâmetros editáveis")

        use_classic = st.toggle(
            "Usar incubação clássica 2–21 dias",
            value=False,
            help="Guias técnicos costumam citar 2–21 dias. O padrão operacional 4–17 dias permanece ajustável.",
        )

        if use_classic:
            min_inc = 2
            max_inc = 21
            st.info("Incubação configurada como 2–21 dias.")
        else:
            min_inc = st.number_input("Incubação mínima, em dias", min_value=1, max_value=60, value=4)
            max_inc = st.number_input("Incubação máxima, em dias", min_value=1, max_value=60, value=17)

        wet_offset = st.number_input(
            "Dias após início dos sintomas para alerta de sintomas úmidos/tardios",
            min_value=0,
            max_value=30,
            value=4,
        )

        severe_offset = st.number_input(
            "Dias após início dos sintomas para alerta de sangramento/sinais de gravidade",
            min_value=0,
            max_value=30,
            value=5,
            help="Alerta operacional. Não significa que sangramento ocorrerá obrigatoriamente.",
        )

        death_offset = st.number_input(
            "Dias entre início dos sintomas e óbito, quando o início é desconhecido",
            min_value=0,
            max_value=60,
            value=10,
        )

        monitoring_days = st.number_input(
            "Dias de monitoramento após último contato",
            min_value=1,
            max_value=60,
            value=21,
        )

        st.divider()
        st.markdown(
            "**Nota técnica:** óbito é tratado como desfecho quando o início dos sintomas é conhecido, "
            "e como base retrospectiva apenas quando o início dos sintomas é desconhecido."
        )

    return CalculatorParams(
        min_incubation_days=int(min_inc),
        max_incubation_days=int(max_inc),
        wet_symptom_offset_days=int(wet_offset),
        severe_alert_offset_days=int(severe_offset),
        death_offset_days=int(death_offset),
        contact_monitoring_days=int(monitoring_days),
    )


def render_inputs() -> tuple:
    st.subheader("1. Dados do caso índice")

    c1, c2, c3 = st.columns([0.30, 0.35, 0.35])

    with c1:
        has_last_exposure = st.checkbox(
            "Informar data da última exposição",
            value=True,
            help="Use quando houver uma data conhecida ou estimada de última exposição de risco.",
        )
        last_exposure_date = None
        if has_last_exposure:
            last_exposure_date = st.date_input(
                "Data da última exposição",
                value=date.today(),
                format="DD/MM/YYYY",
            )

        detection_date = st.date_input(
            "Data da detecção/avaliação",
            value=date.today(),
            format="DD/MM/YYYY",
            help="Data em que o caso foi identificado, avaliado ou detectado.",
        )

    with c2:
        clinical_condition = st.selectbox(
            "Condição clínica observada na detecção",
            options=CLINICAL_CONDITION_OPTIONS,
            index=0,
            help="Use esta opção quando o início dos sintomas não for conhecido e o paciente já for detectado em fase posterior.",
        )

        case_status = st.selectbox(
            "Situação/desfecho do caso",
            options=CASE_STATUS_OPTIONS,
            index=0,
        )

        death_date = None
        death_after_symptoms = "Não se aplica"
        body_manipulation = "Não"
        funeral_or_wake = "Não"
        body_transport = "Não"
        post_mortem_contact = "Não"
        safe_burial_or_post_mortem_end_date = None

        if case_status == "Óbito":
            death_date = st.date_input("Data do óbito", value=date.today(), format="DD/MM/YYYY")
            death_after_symptoms = st.selectbox(
                "Óbito ocorreu após sintomas?",
                options=["Sim", "Não", "Desconhecido"],
                index=0,
            )
            body_manipulation = st.selectbox("Houve manipulação do corpo?", YES_NO_UNKNOWN, index=0)
            funeral_or_wake = st.selectbox("Houve velório/funeral?", YES_NO_UNKNOWN, index=0)
            body_transport = st.selectbox("Houve transporte do corpo?", YES_NO_UNKNOWN, index=0)
            post_mortem_contact = st.selectbox("Contato pós-óbito identificado?", YES_NO_UNKNOWN, index=0)

            has_safe_burial = st.checkbox(
                "Informar sepultamento seguro/fim da exposição pós-óbito",
                value=True,
            )
            if has_safe_burial:
                safe_burial_or_post_mortem_end_date = st.date_input(
                    "Data de sepultamento seguro/fim exposição pós-óbito",
                    value=date.today(),
                    format="DD/MM/YYYY",
                )

    with c3:
        onset_known = st.checkbox(
            "Data de início dos sintomas é conhecida?",
            value=True,
            help="Marque quando houver data real, estimada ou aproximada de início dos sintomas.",
        )

        known_onset_date = None
        symptom_onset_status = "Estimado retrospectivamente"

        if onset_known:
            known_onset_date = st.date_input(
                "Data real/estimada de início dos sintomas",
                value=date.today(),
                format="DD/MM/YYYY",
            )
            symptom_onset_status = st.selectbox(
                "Tipo da data de sintomas",
                options=ONSET_STATUS_OPTIONS,
                index=0,
            )

        live_exposure_end_date = st.date_input(
            "Data final da exposição em vida",
            value=date.today(),
            format="DD/MM/YYYY",
            help="Use isolamento, último contato possível em vida, transferência segura, óbito ou encerramento da exposição em vida.",
        )

    return (
        last_exposure_date,
        detection_date,
        clinical_condition,
        case_status,
        death_date,
        death_after_symptoms,
        body_manipulation,
        funeral_or_wake,
        body_transport,
        post_mortem_contact,
        safe_burial_or_post_mortem_end_date,
        live_exposure_end_date,
        onset_known,
        known_onset_date,
        symptom_onset_status,
    )


def render_case_results(case: CaseCalculation, params: CalculatorParams) -> None:
    st.subheader("2. Exposição, óbito, pós-óbito, sintomas e marcos evolutivos")

    st.info(
        "A ferramenta trata óbito como desfecho quando a data de início dos sintomas é conhecida. "
        "Quando o início dos sintomas é desconhecido, a data de óbito pode ser usada para estimativa retrospectiva. "
        "A busca de contatos considera exposição em vida e, quando aplicável, exposição pós-óbito até sepultamento seguro ou encerramento operacional."
    )

    df = case_to_df(case)

    date_cols = [
        "data da última exposição",
        "data da detecção/avaliação",
        "data do óbito",
        "data de sepultamento seguro/fim exposição pós-óbito",
        "data final da exposição em vida",
        "fim operacional da busca de contatos",
        "início real/estimado dos sintomas",
        "início provável da exposição/infecção",
        "fim provável da exposição/infecção",
        "início possível de sintomas pela última exposição",
        "fim possível de sintomas pela última exposição",
        "alerta para sintomas úmidos/tardios",
        "alerta para sangramento/sinais de gravidade",
        "início da janela transmissível",
    ]

    display_df = format_date_columns_br(df, date_cols)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    timeline = make_case_timeline(case)
    fig = px.timeline(
        timeline,
        x_start="início",
        x_end="fim",
        y="item",
        color="fase",
        hover_data={"fase": True, "início": True, "fim": True},
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=520, margin=dict(l=20, r=20, t=35, b=20), legend_title_text="Fase/marco")
    st.plotly_chart(fig, use_container_width=True)

    payload = case_to_iso_payload(case, params)
    csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
    json_data = json.dumps(payload, ensure_ascii=False, indent=2)

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Baixar cálculo do caso índice em CSV",
            data=csv_data,
            file_name="calculadora_ebola_caso_indice.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "Baixar cálculo do caso índice em JSON técnico",
            data=json_data,
            file_name="calculadora_ebola_caso_indice.json",
            mime="application/json",
            help="O JSON permanece em formato ISO AAAA-MM-DD para interoperabilidade técnica.",
            use_container_width=True,
        )


def render_contact_editor() -> pd.DataFrame:
    st.subheader("3. Cadastro de contatos e evolução")

    st.info(
        "Para dados reais, prefira identificadores ou códigos internos em vez de CPF, nome completo ou outros dados pessoais sensíveis. "
        "Inclua contatos em vida e pós-óbito, como manipulação do corpo, transporte, velório/funeral, sepultamento e limpeza/desinfecção."
    )

    uploaded = st.file_uploader(
        "Opcional: importar lista de contatos em CSV ou XLSX",
        type=["csv", "xlsx", "xls"],
        help="A planilha modelo pode ser importada diretamente se contiver a aba Contatos_Importar.",
    )

    try:
        default_df = read_uploaded_contacts(uploaded)
    except Exception as exc:
        st.error(f"Não foi possível ler o arquivo importado: {exc}")
        default_df = default_contacts_df()

    contacts_df = st.data_editor(
        default_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "identificador": st.column_config.TextColumn(
                "Identificador do contato",
                help="Ex.: Contato 1, C001, familiar 01, profissional 02.",
                required=True,
            ),
            "nome_codigo": st.column_config.TextColumn("Nome/código"),
            "caso_origem": st.column_config.TextColumn(
                "Caso-origem",
                help="Use 'Caso índice' ou o identificador de outro contato/caso já cadastrado.",
            ),
            "data_ultimo_contato": st.column_config.DateColumn("Data do último contato de risco", format="DD/MM/YYYY"),
            "tipo_contato": st.column_config.SelectboxColumn("Tipo de contato/exposição", options=EXPOSURE_TYPE_OPTIONS),
            "municipio": st.column_config.TextColumn("Município/local"),
            "risco": st.column_config.SelectboxColumn("Risco", options=RISK_OPTIONS),
            "evolucao": st.column_config.SelectboxColumn("Evolução", options=EVOLUTION_OPTIONS),
            "data_inicio_sintomas": st.column_config.DateColumn(
                "Data de início dos sintomas",
                format="DD/MM/YYYY",
                help="Preencher se o contato evoluir com sintomas.",
            ),
            "data_fim_transmissibilidade": st.column_config.DateColumn(
                "Fim de transmissibilidade/isolamento",
                format="DD/MM/YYYY",
                help="Preencher quando este contato também funcionar como possível caso-origem de outros contatos.",
            ),
            "data_ultima_avaliacao": st.column_config.DateColumn("Última avaliação", format="DD/MM/YYYY"),
            "observacao": st.column_config.TextColumn("Observação/evolução clínica"),
        },
    )

    return normalize_contacts_df(contacts_df)


def render_contacts_analysis(
    contacts_df: pd.DataFrame,
    case: CaseCalculation,
    params: CalculatorParams,
) -> pd.DataFrame:
    st.subheader("4. Monitoramento de contatos")

    evaluated = evaluate_contacts(contacts_df, case, params)

    if evaluated.empty:
        st.info("Inclua ao menos um contato com identificador para calcular o monitoramento.")
        return evaluated

    total = len(evaluated)
    active = evaluated["situação do prazo"].astype(str).str.contains("Em monitoramento", na=False).sum()
    action = evaluated["situação do prazo"].astype(str).str.contains("Requer avaliação/ação", na=False).sum()
    completed = evaluated["situação do prazo"].astype(str).str.contains("Prazo concluído|Encerrado", regex=True, na=False).sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Contatos cadastrados", total)
    m2.metric("Em monitoramento", int(active))
    m3.metric("Requer avaliação/ação", int(action))
    m4.metric("Concluídos/encerrados", int(completed))

    date_cols = [
        "data do último contato",
        "monitorar até",
        "data de início dos sintomas",
        "data da última avaliação",
    ]
    display = format_date_columns_br(evaluated, date_cols)
    st.dataframe(display, use_container_width=True, hide_index=True)

    timeline = make_contacts_timeline(evaluated)
    if not timeline.empty:
        fig = px.timeline(
            timeline,
            x_start="início",
            x_end="fim",
            y="identificador",
            color="fase",
            hover_data={"fase": True, "início": True, "fim": True},
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=35, b=20), legend_title_text="Fase")
        st.plotly_chart(fig, use_container_width=True)

    export_df = display.copy()
    st.download_button(
        "Baixar relação de contatos monitorados em CSV",
        data=export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="calculadora_ebola_contatos_monitoramento.csv",
        mime="text/csv",
        use_container_width=True,
    )

    return evaluated


def render_chain_graph(contacts_df: pd.DataFrame) -> None:
    contacts = normalize_contacts_df(contacts_df)
    if contacts.empty:
        st.info("Inclua contatos para gerar o mapa da cadeia de transmissão.")
        return

    edges = make_chain_edges(contacts)
    generations = calculate_contact_generation(contacts)

    nodes = {"Caso índice"}
    for _, row in contacts.iterrows():
        nodes.add(clean_text(row.get("identificador")))
        nodes.add(clean_text(row.get("caso_origem")) or "Caso índice")
    nodes = {n for n in nodes if n}

    meta = {
        "Caso índice": {
            "label": "Caso índice",
            "evolucao": "Caso índice",
            "municipio": "",
            "risco": "",
        }
    }

    for _, row in contacts.iterrows():
        ident = clean_text(row.get("identificador"))
        if not ident:
            continue
        meta[ident] = {
            "label": f"{ident}<br>{clean_text(row.get('evolucao')) or 'Em monitoramento'}",
            "evolucao": clean_text(row.get("evolucao")),
            "municipio": clean_text(row.get("municipio")),
            "risco": clean_text(row.get("risco")),
        }

    max_gen = max(generations.values()) if generations else 1
    positions = {}
    for gen in range(max_gen + 1):
        gen_nodes = sorted([n for n in nodes if generations.get(n, 1) == gen])
        for idx, node in enumerate(gen_nodes):
            positions[node] = (gen, len(gen_nodes) - idx)

    for idx, node in enumerate(sorted(nodes)):
        if node not in positions:
            positions[node] = (generations.get(node, 1), idx + 1)

    fig = go.Figure()

    edge_x = []
    edge_y = []
    for _, row in edges.iterrows():
        parent = row["caso-origem"]
        child = row["contato/caso exposto"]
        if parent not in positions or child not in positions:
            continue
        x0, y0 = positions[parent]
        x1, y1 = positions[child]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    status_symbol = {
        "Caso índice": "star",
        "Em monitoramento": "circle",
        "Assintomático": "circle",
        "Sintomático": "diamond",
        "Suspeito": "diamond",
        "Confirmado": "square",
        "Descartado": "x",
        "Óbito": "cross",
        "Encerrado": "circle",
    }

    node_x, node_y, texts, hovers, symbols, sizes = [], [], [], [], [], []
    for node in sorted(nodes, key=lambda n: (positions[n][0], positions[n][1], n)):
        x, y = positions[node]
        item = meta.get(node, {"label": node, "evolucao": "Origem externa", "municipio": "", "risco": ""})
        evolution = item.get("evolucao") or "Em monitoramento"
        node_x.append(x)
        node_y.append(y)
        texts.append(item.get("label", node))
        hovers.append(
            f"<b>{node}</b><br>"
            f"Evolução: {evolution}<br>"
            f"Município: {item.get('municipio', '')}<br>"
            f"Risco: {item.get('risco', '')}<br>"
            f"Geração: {generations.get(node, '-')}"
        )
        symbols.append(status_symbol.get(evolution, "circle"))
        sizes.append(28 if node == "Caso índice" else 20)

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=texts,
            textposition="bottom center",
            hovertext=hovers,
            hoverinfo="text",
            marker=dict(size=sizes, symbol=symbols, line=dict(width=1)),
            showlegend=False,
        )
    )

    for _, row in edges.iterrows():
        parent = row["caso-origem"]
        child = row["contato/caso exposto"]
        if parent not in positions or child not in positions:
            continue
        x0, y0 = positions[parent]
        x1, y1 = positions[child]
        fig.add_annotation(
            x=x1,
            y=y1,
            ax=x0,
            ay=y0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1,
            arrowwidth=1,
            opacity=0.45,
        )

    fig.update_layout(
        height=520,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(
            title="Geração epidemiológica possível",
            tickmode="array",
            tickvals=list(range(max_gen + 1)),
            ticktext=[f"Geração {i}" if i > 0 else "Caso índice" for i in range(max_gen + 1)],
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_chain_section(contacts_df: pd.DataFrame) -> None:
    st.subheader("5. Mapa de possível cadeia de transmissão")
    st.markdown(
        "O mapa usa o campo **caso-origem** para montar vínculos entre o caso índice, contatos e possíveis casos secundários. "
        "Quando um contato também se tornar suspeito, confirmado ou sintomático, ele pode ser usado como caso-origem de novos contatos."
    )

    render_chain_graph(contacts_df)

    edges = make_chain_edges(contacts_df)
    st.markdown("#### Relação de vínculos da cadeia")
    display_edges = format_date_columns_br(edges, ["data do contato"])
    if not display_edges.empty:
        st.dataframe(display_edges, use_container_width=True, hide_index=True)

        st.download_button(
            "Baixar vínculos da cadeia em CSV",
            data=display_edges.to_csv(index=False).encode("utf-8-sig"),
            file_name="calculadora_ebola_cadeia_transmissao.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_interpretation() -> None:
    st.subheader("6. Interpretação operacional")
    st.markdown(
        """
        **1. Óbito como desfecho:** se o início dos sintomas é conhecido, a data do óbito é registrada como desfecho e não deve recalcular o início dos sintomas.

        **2. Óbito como base retrospectiva:** se o início dos sintomas é desconhecido e o óbito ocorreu após sintomas ou com informação sintomática desconhecida, a ferramenta pode estimar retrospectivamente o início dos sintomas a partir da data do óbito.

        **3. Óbito sem sintomas conhecidos:** se não há início de sintomas conhecido nem informação clínica suficiente, a ferramenta não deve gerar uma data forte de início dos sintomas apenas pelo óbito.

        **4. Exposição pós-óbito:** quando houver manipulação do corpo, transporte, velório/funeral, sepultamento ou contato pós-óbito, a busca de contatos deve considerar a data de sepultamento seguro ou o encerramento da exposição pós-óbito.

        **5. Sangramento:** não é tratado como etapa obrigatória. Permanece como alerta operacional para sangramento/sinais de gravidade.

        **6. Limite da ferramenta:** compatibilidade temporal não confirma transmissão. A interpretação final depende de investigação epidemiológica, clínica, laboratório, contexto do surto, exposição real e validação da equipe responsável.
        """
    )

    st.markdown(
        """
        ### Como as datas são calculadas

        **Quando o paciente foi a óbito com início dos sintomas conhecido**

        - Início dos sintomas = data informada.
        - Óbito = desfecho.
        - Fim operacional da busca de contatos = maior data entre exposição em vida, óbito e fim da exposição pós-óbito/sepultamento seguro.

        **Quando o paciente foi a óbito e o início dos sintomas é desconhecido**

        - Início estimado dos sintomas = data do óbito - dias configurados entre início dos sintomas e óbito.
        - Janela provável de exposição/infecção = início estimado dos sintomas - incubação máxima até início estimado dos sintomas - incubação mínima.

        **Quando não há sintomas conhecidos**

        - A ferramenta solicita revisão dos dados e não gera uma estimativa forte apenas pela data de óbito.

        **Contatos**

        - Possível início de sintomas do contato = data do último contato + incubação mínima até incubação máxima.
        - Monitorar até = data do último contato + número de dias de monitoramento.
        - Contatos pós-óbito podem incluir manipulação do corpo, transporte, velório/funeral, sepultamento e limpeza/desinfecção.

        **Padrão de datas**

        - A interface, as tabelas e os CSVs usam o padrão brasileiro **DD/MM/AAAA**.
        - O arquivo JSON técnico permanece em **AAAA-MM-DD** para interoperabilidade entre sistemas.
        """
    )

    st.warning(
        "Ferramenta de apoio técnico. Não substitui definição de caso, investigação de campo, exames laboratoriais, protocolos oficiais, sistema de notificação ou comunicação imediata às autoridades sanitárias."
    )


def main() -> None:
    configure_page()
    params = sidebar_params()

    (
        last_exposure_date,
        detection_date,
        clinical_condition,
        case_status,
        death_date,
        death_after_symptoms,
        body_manipulation,
        funeral_or_wake,
        body_transport,
        post_mortem_contact,
        safe_burial_or_post_mortem_end_date,
        live_exposure_end_date,
        onset_known,
        known_onset_date,
        symptom_onset_status,
    ) = render_inputs()

    try:
        case = calculate_case(
            last_exposure_date=last_exposure_date,
            detection_date=detection_date,
            clinical_condition_at_detection=clinical_condition,
            case_status=case_status,
            death_date=death_date,
            death_after_symptoms=death_after_symptoms,
            body_manipulation=body_manipulation,
            funeral_or_wake=funeral_or_wake,
            body_transport=body_transport,
            post_mortem_contact=post_mortem_contact,
            safe_burial_or_post_mortem_end_date=safe_burial_or_post_mortem_end_date,
            live_exposure_end_date=live_exposure_end_date,
            onset_known=onset_known,
            known_symptom_onset_date=known_onset_date,
            symptom_onset_status=symptom_onset_status,
            params=params,
        )

        if case.operational_contact_search_end_date < case.transmission_start:
            st.warning(
                "A data final operacional da busca de contatos está anterior ao início dos sintomas. "
                "Revisar datas informadas."
            )

        render_case_results(case, params)
        st.divider()

        contacts_df = render_contact_editor()
        st.divider()

        render_contacts_analysis(contacts_df, case, params)
        st.divider()

        render_chain_section(contacts_df)
        st.divider()

        render_interpretation()

    except Exception as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
