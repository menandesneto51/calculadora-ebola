from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
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

    # pandas.Timestamp herda de datetime/date, por isso precisa vir ANTES
    # de isinstance(value, date). Caso contrário, comparações entre
    # Timestamp e datetime.date podem falhar no monitoramento de contatos.
    if isinstance(value, pd.Timestamp):
        return value.date()

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
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
    # A ferramenta não deve criar contatos fictícios automaticamente.
    # Sem planilha importada ou digitação manual, o painel deve permanecer zerado.
    columns = [
        "identificador",
        "nome_codigo",
        "caso_origem",
        "data_ultimo_contato",
        "tipo_contato",
        "municipio",
        "risco",
        "evolucao",
        "data_inicio_sintomas",
        "data_fim_transmissibilidade",
        "data_ultima_avaliacao",
        "observacao",
    ]
    return pd.DataFrame(columns=columns)


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
        normalized[col] = normalized[col].apply(coerce_date).astype("object")

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
    last_contact = coerce_date(last_contact)
    if last_contact is None:
        return "Data inválida/ausente", "-"

    if source_id == "Caso índice":
        transmission_start = coerce_date(case.transmission_start)
        operational_end = coerce_date(case.operational_contact_search_end_date)
        if transmission_start is not None and operational_end is not None and transmission_start <= last_contact <= operational_end:
            return "Sim", f"{fmt_br(transmission_start)} a {fmt_br(operational_end)}"
        return "Não", "-"

    source = contacts_by_id.get(source_id)
    if source is None:
        return "Não avaliado", "Caso-origem não localizado"

    source_onset = coerce_date(source.get("data_inicio_sintomas"))
    source_end = coerce_date(source.get("data_fim_transmissibilidade"))

    if source_onset is None or source_end is None:
        return "Não avaliado", "Informe início de sintomas e fim de transmissibilidade do caso-origem"

    source_onset = coerce_date(source_onset)
    source_end = coerce_date(source_end)
    if source_onset is not None and source_end is not None and source_onset <= last_contact <= source_end:
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

        last_contact = coerce_date(last_contact)
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
        "Nenhum contato é criado automaticamente. O painel ficará zerado até que uma planilha seja importada "
        "ou contatos sejam inseridos manualmente. Para dados reais, prefira identificadores ou códigos internos "
        "em vez de CPF, nome completo ou outros dados pessoais sensíveis. Inclua contatos em vida e pós-óbito, "
        "como manipulação do corpo, transporte, velório/funeral, sepultamento e limpeza/desinfecção."
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
        st.info("Nenhum contato carregado. Importe uma planilha ou inclua contatos manualmente para gerar o painel de monitoramento.")
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
    post_mortem_types = {"Manipulação do corpo", "Velório/funeral", "Sepultamento", "Limpeza/desinfecção"}
    relevant_statuses = {"Sintomático", "Suspeito", "Confirmado", "Óbito"}

    nodes = {"Caso índice"}
    for _, row in contacts.iterrows():
        ident = clean_text(row.get("identificador"))
        parent = clean_text(row.get("caso_origem")) or "Caso índice"
        if ident:
            nodes.add(ident)
        if parent:
            nodes.add(parent)
    nodes = {n for n in nodes if n}

    meta = {
        "Caso índice": {
            "label_short": "Caso índice",
            "evolucao": "Caso índice",
            "municipio": "",
            "risco": "",
            "tipo_contato": "",
            "data_ultimo_contato": None,
            "caso_origem": "",
            "pos_obito": False,
            "is_group": False,
            "members": [],
        }
    }

    for _, row in contacts.iterrows():
        ident = clean_text(row.get("identificador"))
        if not ident:
            continue
        tipo_contato = clean_text(row.get("tipo_contato"))
        meta[ident] = {
            "label_short": ident,
            "evolucao": clean_text(row.get("evolucao")) or "Em monitoramento",
            "municipio": clean_text(row.get("municipio")),
            "risco": clean_text(row.get("risco")),
            "tipo_contato": tipo_contato,
            "data_ultimo_contato": coerce_date(row.get("data_ultimo_contato")),
            "caso_origem": clean_text(row.get("caso_origem")) or "Caso índice",
            "pos_obito": tipo_contato in post_mortem_types,
            "is_group": False,
            "members": [],
        }

    children_by_parent = {}
    parent_lookup = {}
    for _, row in edges.iterrows():
        parent = clean_text(row.get("caso-origem")) or "Caso índice"
        child = clean_text(row.get("contato/caso exposto"))
        if child:
            parent_lookup[child] = parent
            children_by_parent.setdefault(parent, set()).add(child)

    all_generations = sorted(set(generations.values())) if generations else [0]
    all_statuses = sorted({meta.get(n, {}).get("evolucao", "Origem externa") for n in nodes})
    if "Caso índice" in all_statuses:
        all_statuses = ["Caso índice"] + [s for s in all_statuses if s != "Caso índice"]

    c1, c2, c3 = st.columns([1.2, 1.4, 1.3])
    with c1:
        selected_generations = st.multiselect(
            "Gerações visíveis",
            options=all_generations,
            default=all_generations,
            help="Filtre a visualização por geração epidemiológica.",
        )
        hide_low_priority = st.checkbox(
            "Ocultar assintomáticos/encerrados/descartados",
            value=False,
            help="Remove nós com menor prioridade visual, preservando os pais necessários para leitura da cadeia.",
        )

    with c2:
        selected_statuses = st.multiselect(
            "Evoluções visíveis",
            options=all_statuses,
            default=all_statuses,
            help="Filtre quais evoluções devem permanecer no grafo.",
        )
        show_only_relevant = st.checkbox(
            "Mostrar apenas sintomáticos/suspeitos/confirmados/óbito",
            value=False,
            help="Mantém no grafo apenas nós com maior relevância clínica, além do caso índice e pais necessários.",
        )

    with c3:
        highlight_post_mortem = st.checkbox(
            "Destacar pós-óbito",
            value=True,
            help="Aplica borda reforçada aos contatos relacionados a manipulação do corpo, velório/funeral, sepultamento ou limpeza pós-óbito.",
        )
        auto_group = st.checkbox(
            "Agrupar contatos numerosos",
            value=len(contacts) >= 18,
            help="Agrupa contatos de menor prioridade que tenham o mesmo caso-origem, geração, evolução e tipo de exposição.",
        )
        group_threshold = st.slider(
            "Agrupar a partir de quantos contatos",
            min_value=3,
            max_value=20,
            value=5,
            step=1,
            help="Número mínimo de contatos semelhantes para criar um nó agrupado.",
        )

    low_priority_statuses = {"Em monitoramento", "Assintomático", "Encerrado", "Descartado"}
    hidden_statuses = {"Assintomático", "Encerrado", "Descartado"}

    visible_nodes = set()
    for node in nodes:
        generation = generations.get(node, 1)
        item = meta.get(node, {})
        evolution = item.get("evolucao", "Origem externa")

        if selected_generations and generation not in selected_generations:
            continue
        if selected_statuses and evolution not in selected_statuses:
            continue
        if hide_low_priority and node != "Caso índice" and evolution in hidden_statuses:
            continue
        if show_only_relevant and node != "Caso índice" and evolution not in relevant_statuses:
            continue
        visible_nodes.add(node)

    expanded = True
    while expanded:
        expanded = False
        for node in list(visible_nodes):
            parent = parent_lookup.get(node)
            if parent and parent not in visible_nodes:
                visible_nodes.add(parent)
                expanded = True

    if not visible_nodes:
        st.info("Os filtros atuais não exibem nenhum nó.")
        return

    visible_edges = edges[
        edges["caso-origem"].isin(visible_nodes)
        & edges["contato/caso exposto"].isin(visible_nodes)
    ].copy()

    final_nodes = set(visible_nodes)
    final_edges = []

    if auto_group:
        group_candidates = {}
        for node in list(visible_nodes):
            item = meta.get(node, {})
            if node == "Caso índice":
                continue
            if item.get("evolucao") not in low_priority_statuses:
                continue
            if item.get("pos_obito"):
                continue
            if node in children_by_parent and children_by_parent.get(node):
                continue

            parent = parent_lookup.get(node, item.get("caso_origem") or "Caso índice")
            if not parent or parent not in visible_nodes:
                continue

            key = (
                parent,
                generations.get(node, 1),
                item.get("evolucao", "Origem externa"),
                item.get("tipo_contato", "") or "Sem tipo informado",
            )
            group_candidates.setdefault(key, []).append(node)

        grouped_nodes = set()
        group_index = 1
        for key, members in group_candidates.items():
            if len(members) < group_threshold:
                continue
            parent, generation, evolution, tipo = key
            group_id = f"Grupo {group_index:02d} — {evolution} ({len(members)})"
            group_index += 1

            meta[group_id] = {
                "label_short": f"Grupo n={len(members)}",
                "evolucao": evolution,
                "municipio": "Múltiplos",
                "risco": "Múltiplos",
                "tipo_contato": tipo,
                "data_ultimo_contato": None,
                "caso_origem": parent,
                "pos_obito": False,
                "is_group": True,
                "members": sorted(members),
            }
            generations[group_id] = generation
            final_nodes.add(group_id)
            final_edges.append(
                {
                    "caso-origem": parent,
                    "contato/caso exposto": group_id,
                    "data do contato": None,
                    "tipo de contato": tipo,
                    "município": "Múltiplos",
                    "evolução": evolution,
                    "agrupado": True,
                }
            )

            for member in members:
                grouped_nodes.add(member)
                final_nodes.discard(member)

        for _, row in visible_edges.iterrows():
            child = clean_text(row.get("contato/caso exposto"))
            parent = clean_text(row.get("caso-origem"))
            if child in grouped_nodes or parent in grouped_nodes:
                continue
            final_edges.append({**row.to_dict(), "agrupado": False})
    else:
        final_edges = [{**row.to_dict(), "agrupado": False} for _, row in visible_edges.iterrows()]

    final_edges = [
        e for e in final_edges
        if e.get("caso-origem") in final_nodes and e.get("contato/caso exposto") in final_nodes
    ]

    if not final_nodes:
        st.info("Os filtros atuais não exibem nenhum nó após agrupamento.")
        return

    visible_generations = sorted({generations.get(n, 1) for n in final_nodes})
    positions = {}
    max_nodes_in_col = 1

    for gen in visible_generations:
        gen_nodes = sorted(
            [n for n in final_nodes if generations.get(n, 1) == gen],
            key=lambda n: (
                0 if n == "Caso índice" else 1,
                meta.get(n, {}).get("evolucao", ""),
                meta.get(n, {}).get("tipo_contato", ""),
                n,
            ),
        )
        if not gen_nodes:
            continue
        max_nodes_in_col = max(max_nodes_in_col, len(gen_nodes))
        spacing = 1.8
        center = (len(gen_nodes) - 1) / 2
        for idx, node in enumerate(gen_nodes):
            x = gen * 4.2
            y = (center - idx) * spacing
            positions[node] = (x, y)

    for idx, node in enumerate(sorted(final_nodes)):
        if node not in positions:
            positions[node] = (generations.get(node, 1) * 4.2, -idx * 1.8)

    status_styles = {
        "Caso índice": {"color": "#1F4E79", "symbol": "star", "size": 30},
        "Em monitoramento": {"color": "#5DADE2", "symbol": "circle", "size": 18},
        "Assintomático": {"color": "#A6ACAF", "symbol": "circle", "size": 18},
        "Sintomático": {"color": "#E67E22", "symbol": "diamond", "size": 20},
        "Suspeito": {"color": "#F1C40F", "symbol": "diamond", "size": 22},
        "Confirmado": {"color": "#C0392B", "symbol": "square", "size": 22},
        "Descartado": {"color": "#27AE60", "symbol": "x", "size": 20},
        "Óbito": {"color": "#7B241C", "symbol": "cross", "size": 24},
        "Encerrado": {"color": "#58D68D", "symbol": "circle", "size": 18},
        "Origem externa": {"color": "#7F8C8D", "symbol": "circle", "size": 18},
    }

    fig = go.Figure()
    y_extent = max(3.0, max_nodes_in_col * 1.25)
    for gen in visible_generations:
        x = gen * 4.2
        fig.add_vline(x=x, line_width=1, line_dash="dot", line_color="rgba(120,120,120,0.25)")
        fig.add_annotation(
            x=x,
            y=y_extent + 1.2,
            text=f"<b>Geração {gen}</b>" if gen > 0 else "<b>Caso índice</b>",
            showarrow=False,
            font=dict(size=13, color="#566573"),
        )

    for edge in final_edges:
        parent = edge["caso-origem"]
        child = edge["contato/caso exposto"]
        if parent not in positions or child not in positions:
            continue

        x0, y0 = positions[parent]
        x1, y1 = positions[child]
        grouped = bool(edge.get("agrupado", False))

        edge_hover = (
            f"<b>{parent}</b> ➜ <b>{child}</b><br>"
            f"Tipo de contato: {clean_text(edge.get('tipo de contato')) or '-'}<br>"
            f"Data do contato: {fmt_br(coerce_date(edge.get('data do contato')))}<br>"
            f"Município: {clean_text(edge.get('município')) or '-'}<br>"
            f"Evolução do nó exposto: {clean_text(edge.get('evolução')) or '-'}<br>"
            f"Agrupado: {'Sim' if grouped else 'Não'}"
        )

        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(
                    width=2.2 if grouped else 1.2,
                    color="rgba(52, 152, 219, 0.45)" if not grouped else "rgba(127, 140, 141, 0.55)",
                    dash="dot" if grouped else "solid",
                ),
                hoverinfo="text",
                text=[edge_hover, edge_hover],
                showlegend=False,
            )
        )

    ordered_statuses = [
        "Caso índice", "Em monitoramento", "Assintomático", "Sintomático", "Suspeito",
        "Confirmado", "Descartado", "Óbito", "Encerrado", "Origem externa"
    ]

    for status in ordered_statuses:
        node_subset = [
            n for n in sorted(final_nodes, key=lambda n: (generations.get(n, 1), -positions[n][1], n))
            if meta.get(n, {}).get("evolucao", "Origem externa") == status
        ]
        if not node_subset:
            continue

        style = status_styles.get(status, status_styles["Origem externa"])
        xs, ys, texts, hovers, sizes, line_colors, line_widths, symbols = [], [], [], [], [], [], [], []

        for node in node_subset:
            item = meta.get(node, {})
            xs.append(positions[node][0])
            ys.append(positions[node][1])
            texts.append(item.get("label_short", node))

            is_group = bool(item.get("is_group", False))
            is_post_mortem = bool(item.get("pos_obito", False))

            sizes.append(max(style["size"], 24) if is_group else style["size"])
            symbols.append("square" if is_group else style["symbol"])
            line_colors.append("#C0392B" if highlight_post_mortem and is_post_mortem else "#FFFFFF")
            line_widths.append(3.2 if highlight_post_mortem and is_post_mortem else (2.2 if is_group else 1.2))

            members = item.get("members", [])
            members_text = ", ".join(members[:12])
            if len(members) > 12:
                members_text += f" ... (+{len(members)-12})"

            hovers.append(
                f"<b>{node}</b><br>"
                f"Evolução: {item.get('evolucao', '-') or '-'}<br>"
                f"Risco: {item.get('risco', '-') or '-'}<br>"
                f"Município: {item.get('municipio', '-') or '-'}<br>"
                f"Tipo de contato: {item.get('tipo_contato', '-') or '-'}<br>"
                f"Caso-origem: {item.get('caso_origem', '-') or '-'}<br>"
                f"Data do último contato: {fmt_br(item.get('data_ultimo_contato'))}<br>"
                f"Geração: {generations.get(node, '-')}<br>"
                f"Pós-óbito: {'Sim' if is_post_mortem else 'Não'}<br>"
                f"Agrupado: {'Sim' if is_group else 'Não'}"
                + (f"<br>Integrantes: {members_text}" if is_group else "")
            )

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                text=texts,
                textposition="middle right",
                textfont=dict(size=12, color="#2C3E50"),
                hovertext=hovers,
                hoverinfo="text",
                name=status,
                marker=dict(
                    size=sizes,
                    color=style["color"],
                    symbol=symbols,
                    line=dict(color=line_colors, width=line_widths),
                ),
            )
        )

    figure_height = max(460, 180 + max_nodes_in_col * 46)

    fig.update_layout(
        height=figure_height,
        margin=dict(l=30, r=30, t=60, b=35),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title_text="Evolução",
        ),
        xaxis=dict(
            title="Geração epidemiológica possível",
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[min(visible_generations) * 4.2 - 1.0, max(visible_generations) * 4.2 + 2.5],
        ),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Exportar cadeia visualizada")

    node_export_rows = []
    for node in sorted(final_nodes, key=lambda n: (generations.get(n, 1), n)):
        item = meta.get(node, {})
        node_export_rows.append(
            {
                "id": node,
                "geração": generations.get(node, ""),
                "evolução": item.get("evolucao", ""),
                "risco": item.get("risco", ""),
                "município": item.get("municipio", ""),
                "tipo_contato": item.get("tipo_contato", ""),
                "caso_origem": item.get("caso_origem", ""),
                "data_ultimo_contato": fmt_br(item.get("data_ultimo_contato")),
                "pós_óbito": "Sim" if item.get("pos_obito") else "Não",
                "agrupado": "Sim" if item.get("is_group") else "Não",
                "integrantes": ", ".join(item.get("members", [])),
            }
        )

    edge_export_rows = []
    for edge in final_edges:
        edge_export_rows.append(
            {
                "caso_origem": edge.get("caso-origem"),
                "contato_caso_exposto": edge.get("contato/caso exposto"),
                "tipo_contato": edge.get("tipo de contato"),
                "data_contato": fmt_br(edge.get("data do contato")),
                "município": edge.get("município"),
                "evolução": edge.get("evolução"),
                "agrupado": "Sim" if edge.get("agrupado") else "Não",
            }
        )

    nodes_df = pd.DataFrame(node_export_rows)
    edges_df = pd.DataFrame(edge_export_rows)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.download_button(
            "Baixar nós CSV",
            data=nodes_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="cadeia_transmissao_nos.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "Baixar vínculos CSV",
            data=edges_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="cadeia_transmissao_vinculos.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d3:
        st.download_button(
            "Baixar HTML interativo",
            data=fig.to_html(include_plotlyjs="cdn").encode("utf-8"),
            file_name="cadeia_transmissao_interativa.html",
            mime="text/html",
            use_container_width=True,
        )
    with d4:
        try:
            png_bytes = fig.to_image(format="png", scale=2)
            st.download_button(
                "Baixar PNG",
                data=png_bytes,
                file_name="cadeia_transmissao.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception:
            st.caption("Exportação PNG indisponível neste ambiente. Use o HTML interativo ou instale/atualize o pacote kaleido.")

    st.caption(
        "V16: filtros avançados, agrupamento automático, hover completo, destaque pós-óbito "
        "e exportação da cadeia em CSV/HTML/PNG quando disponível."
    )


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



def render_definitions_section() -> None:
    st.subheader("6. Definições operacionais")

    st.info(
        "Estas definições são operacionais para apoiar a investigação e a organização da ferramenta. "
        "A classificação oficial deve seguir a nota técnica, guia ou protocolo vigente da autoridade sanitária responsável pelo evento."
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Classificação de caso",
            "Sintomas e gravidade",
            "Exposição e contatos",
            "Janelas e datas",
        ]
    )

    with tab1:
        st.markdown(
            """
            ### Caso suspeito

            Pessoa com quadro clínico compatível com doença pelo vírus Ebola e vínculo epidemiológico possível, especialmente:

            - febre, fadiga, fraqueza intensa, cefaleia, dor muscular/articular, dor de garganta ou perda de apetite; **e/ou**
            - evolução para vômitos, diarreia, dor abdominal, sinais de desidratação, sinais de gravidade ou sangramento inexplicado; **e**
            - história de exposição, viagem, permanência em área com transmissão, contato com caso suspeito/confirmado, contato com fluidos corporais, assistência em saúde, manipulação de corpo, funeral/sepultamento ou exposição laboratorial no período compatível de incubação.

            **Uso na ferramenta:** classificar como suspeito quando houver combinação de sintomas e exposição compatível, ainda sem confirmação laboratorial.
            """
        )

        st.markdown(
            """
            ### Caso provável

            Caso suspeito com forte vínculo epidemiológico ou clínico, especialmente quando:

            - houve contato direto com caso confirmado ou provável;
            - houve exposição de alto risco a fluidos corporais, corpo, funeral/sepultamento ou ambiente contaminado;
            - o quadro clínico é fortemente compatível, mas ainda não há confirmação laboratorial disponível.

            **Uso na ferramenta:** útil para priorizar investigação, isolamento, rastreamento de contatos e resposta operacional enquanto se aguarda laboratório.
            """
        )

        st.markdown(
            """
            ### Caso confirmado

            Caso com confirmação laboratorial de infecção por ortoebolavírus/Ebola por método específico, como RT-PCR, teste de detecção de antígeno, isolamento viral ou outro método validado pelo laboratório de referência.

            **Uso na ferramenta:** classificar como confirmado quando houver resultado laboratorial compatível validado pela rede oficial.
            """
        )

        st.markdown(
            """
            ### Caso descartado

            Caso inicialmente suspeito que, após investigação clínica, epidemiológica e/ou laboratorial, não atende mais à definição operacional de caso.

            Situações comuns:

            - resultado laboratorial negativo em amostra adequada, conforme algoritmo vigente;
            - identificação de diagnóstico alternativo que explique o quadro;
            - ausência de vínculo epidemiológico e inconsistência clínica após investigação;
            - reclassificação oficial pela vigilância responsável.

            **Uso na ferramenta:** manter o histórico, mas retirar da contagem ativa de suspeitos/confirmados e encerrar ou revisar contatos conforme orientação da equipe responsável.
            """
        )

        st.warning(
            "A definição de caso pode mudar conforme país, surto, espécie viral envolvida, capacidade laboratorial e protocolo vigente. "
            "Use este bloco como apoio operacional, não como substituto da definição oficial do evento."
        )

    with tab2:
        st.markdown(
            """
            ### Sintomas secos/iniciais

            Sintomas iniciais inespecíficos, geralmente antes da fase com maior perda de fluidos:

            - febre;
            - dores musculares e articulares;
            - cefaleia intensa;
            - fraqueza e fadiga;
            - dor de garganta;
            - perda de apetite;
            - mal-estar.

            **Uso na ferramenta:** usar como marco clínico inicial quando a primeira data disponível for o começo do quadro sistêmico.
            """
        )

        st.markdown(
            """
            ### Sintomas úmidos/tardios

            Manifestações posteriores associadas a perda de fluidos corporais e maior gravidade clínica:

            - náusea;
            - dor abdominal;
            - diarreia;
            - vômitos;
            - desidratação;
            - piora do estado geral;
            - sangramento inexplicado, quando presente.

            **Uso na ferramenta:** se o paciente só foi detectado nesta fase e o início dos sintomas é desconhecido, o sistema pode estimar retrospectivamente o início provável dos sintomas.
            """
        )

        st.markdown(
            """
            ### Alerta para sangramento/sinais de gravidade

            Sangramento **não é manifestação universal** e não deve ser tratado como etapa obrigatória. Na ferramenta, este campo é apenas um alerta operacional para gravidade, incluindo:

            - sangramento inexplicado;
            - sinais de choque ou desidratação importante;
            - piora rápida do estado geral;
            - confusão, irritabilidade ou alteração neurológica;
            - dispneia, dor torácica ou sinais de disfunção orgânica;
            - necessidade de manejo intensivo, isolamento rigoroso e comunicação imediata à vigilância.

            **Uso na ferramenta:** marcar como alerta para priorização assistencial, biossegurança, investigação e rastreamento de contatos.
            """
        )

        st.markdown(
            """
            ### Outros sintomas possíveis

            Podem ocorrer erupção cutânea, olhos vermelhos, soluços, dor torácica, falta de ar, confusão e convulsões. O quadro inicial pode ser confundido com malária, influenza, febre tifoide, meningococcemia, pneumonias, dengue, leptospirose, sepse e outras febres hemorrágicas.
            """
        )

    with tab3:
        st.markdown(
            """
            ### Exposição de risco

            Situação em que a pessoa teve contato possível com fonte de infecção no período compatível:

            - contato direto com sangue, secreções, vômito, fezes, urina, saliva ou outros fluidos corporais de caso suspeito/confirmado;
            - contato com superfícies, objetos, roupas, lençóis, agulhas ou materiais contaminados;
            - cuidado direto ao paciente sem proteção adequada;
            - exposição ocupacional em saúde, laboratório, transporte ou limpeza/desinfecção;
            - manipulação de corpo, velório/funeral ou sepultamento com contato;
            - exposição a animais silvestres doentes ou mortos em área de risco.

            **Uso na ferramenta:** registrar como data de última exposição ou como contato na planilha.
            """
        )

        st.markdown(
            """
            ### Contato

            Pessoa que teve exposição de risco a um caso suspeito, provável ou confirmado durante a janela operacional de transmissibilidade.

            **Tipos úteis na planilha:**

            - contato domiciliar;
            - cuidado direto;
            - serviço de saúde;
            - laboratório;
            - transporte do paciente;
            - contato com fluidos;
            - manipulação do corpo;
            - velório/funeral;
            - sepultamento;
            - limpeza/desinfecção;
            - comunidade/evento;
            - outro.
            """
        )

        st.markdown(
            """
            ### Exposição pós-óbito

            Exposição que ocorre após a morte, principalmente durante manipulação do corpo, transporte, velório, funeral, sepultamento ou limpeza/desinfecção de ambientes e objetos.

            **Uso na ferramenta:** em caso de óbito, considerar a busca de contatos até a data de sepultamento seguro ou encerramento da exposição pós-óbito.
            """
        )

    with tab4:
        st.markdown(
            """
            ### Data da última exposição

            Última data conhecida ou estimada em que a pessoa teve contato de risco com fonte provável de infecção.

            ### Data real/estimada de início dos sintomas

            Data em que surgiram os primeiros sintomas compatíveis. Pode ser observada, estimada pela investigação ou inferida retrospectivamente pela fase clínica no momento da detecção.

            ### Janela provável de exposição/infecção

            Intervalo retrospectivo calculado a partir do início dos sintomas:

            - início provável = início dos sintomas - incubação máxima;
            - fim provável = início dos sintomas - incubação mínima.

            ### Janela possível de início de sintomas pela última exposição

            Intervalo prospectivo calculado a partir da última exposição:

            - início possível = última exposição + incubação mínima;
            - fim possível = última exposição + incubação máxima.

            ### Janela operacional de transmissibilidade/busca de contatos

            Intervalo operacional usado para investigação de contatos. Na ferramenta, começa no início dos sintomas e termina na maior data operacional aplicável: isolamento, fim da exposição em vida, óbito, sepultamento seguro ou encerramento da exposição pós-óbito.

            ### Monitoramento de contatos

            Período de acompanhamento após o último contato de risco. A ferramenta usa o parâmetro configurável de monitoramento, por padrão 21 dias.
            """
        )

    st.markdown(
        """
        **Referências técnicas usadas para orientar este bloco:** CDC — sinais e sintomas da doença por Ebola; OMS — ficha técnica sobre Ebola disease, transmissão, sintomas, diagnóstico, vigilância, rastreamento de contatos e sepultamento seguro.
        """
    )

def render_interpretation() -> None:
    st.subheader("7. Interpretação operacional")
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

        render_definitions_section()
        st.divider()

        render_interpretation()

    except Exception as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
