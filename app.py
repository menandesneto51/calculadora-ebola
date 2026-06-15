from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
import json
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# Modelos e parâmetros
# ============================================================

@dataclass(frozen=True)
class CalculatorParams:
    min_incubation_days: int = 4
    max_incubation_days: int = 17
    wet_symptom_offset_days: int = 4
    hemorrhagic_symptom_offset_days: int = 7
    death_offset_days: int = 10
    contact_monitoring_days: int = 21


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    basis: str
    reported_date: date
    estimated_symptom_onset: date
    exposure_start: date
    exposure_end: date
    transmission_start: date
    transmission_end: date
    observation: str


SYMPTOM_SCENARIOS = [
    {
        "scenario": "Sintomas secos",
        "basis": "Data informada considerada como início dos sintomas",
        "offset_attr": None,
        "observation": "Febre, fadiga, cefaleia, mialgia, fraqueza, dor de garganta ou quadro inicial inespecífico.",
    },
    {
        "scenario": "Sintomas úmidos",
        "basis": "Data informada ajustada para trás pelo intervalo médio até sintomas úmidos",
        "offset_attr": "wet_symptom_offset_days",
        "observation": "Diarreia, vômitos ou outros sinais de maior eliminação de fluidos corporais.",
    },
    {
        "scenario": "Sintomas hemorrágicos",
        "basis": "Data informada ajustada para trás pelo intervalo médio até manifestações hemorrágicas",
        "offset_attr": "hemorrhagic_symptom_offset_days",
        "observation": "Sangramentos ou manifestações hemorrágicas não explicadas, geralmente mais tardias.",
    },
]

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


# ============================================================
# Cálculo de janelas do caso índice
# ============================================================

def validate_params(params: CalculatorParams) -> None:
    if params.min_incubation_days > params.max_incubation_days:
        raise ValueError("A incubação mínima não pode ser maior que a incubação máxima.")
    if params.contact_monitoring_days < params.max_incubation_days:
        st.warning(
            "Atenção: o período de monitoramento de contatos está menor que a incubação máxima usada no cálculo."
        )


def estimate_onset_from_symptom_date(
    reported_date: date,
    scenario_config: dict,
    params: CalculatorParams,
) -> date:
    offset_attr = scenario_config["offset_attr"]
    if offset_attr is None:
        return reported_date
    offset_days = getattr(params, offset_attr)
    return reported_date - timedelta(days=offset_days)


def calculate_scenario(
    scenario: str,
    basis: str,
    reported_date: date,
    estimated_onset: date,
    transmission_end: date,
    observation: str,
    params: CalculatorParams,
) -> ScenarioResult:
    exposure_start = estimated_onset - timedelta(days=params.max_incubation_days)
    exposure_end = estimated_onset - timedelta(days=params.min_incubation_days)

    return ScenarioResult(
        scenario=scenario,
        basis=basis,
        reported_date=reported_date,
        estimated_symptom_onset=estimated_onset,
        exposure_start=exposure_start,
        exposure_end=exposure_end,
        transmission_start=estimated_onset,
        transmission_end=transmission_end,
        observation=observation,
    )


def calculate_all_scenarios(
    symptom_report_date: date,
    transmission_end: date,
    params: CalculatorParams,
    include_death_scenario: bool = False,
    death_date: date | None = None,
) -> list[ScenarioResult]:
    validate_params(params)

    results: list[ScenarioResult] = []
    for cfg in SYMPTOM_SCENARIOS:
        estimated_onset = estimate_onset_from_symptom_date(symptom_report_date, cfg, params)
        results.append(
            calculate_scenario(
                scenario=cfg["scenario"],
                basis=cfg["basis"],
                reported_date=symptom_report_date,
                estimated_onset=estimated_onset,
                transmission_end=transmission_end,
                observation=cfg["observation"],
                params=params,
            )
        )

    if include_death_scenario and death_date is not None:
        estimated_onset = death_date - timedelta(days=params.death_offset_days)
        results.append(
            calculate_scenario(
                scenario="Data de óbito",
                basis="Data de óbito ajustada para trás pelo intervalo médio entre início dos sintomas e óbito",
                reported_date=death_date,
                estimated_onset=estimated_onset,
                transmission_end=transmission_end,
                observation="Útil quando a data de início dos sintomas é ausente, imprecisa ou conflitante.",
                params=params,
            )
        )

    return results


def scenario_results_to_df(results: Iterable[ScenarioResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "cenário": result.scenario,
                "base do cálculo": result.basis,
                "data informada": result.reported_date,
                "início estimado dos sintomas": result.estimated_symptom_onset,
                "início provável da exposição": result.exposure_start,
                "fim provável da exposição": result.exposure_end,
                "início da janela transmissível": result.transmission_start,
                "fim operacional da janela transmissível": result.transmission_end,
                "observação": result.observation,
            }
        )
    return pd.DataFrame(rows)


def make_timeline_df(results: Iterable[ScenarioResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.extend(
            [
                {
                    "cenário": result.scenario,
                    "fase": "Janela provável de exposição do caso índice",
                    "início": result.exposure_start,
                    "fim": result.exposure_end + timedelta(days=1),
                },
                {
                    "cenário": result.scenario,
                    "fase": "Janela operacional de transmissibilidade do caso índice",
                    "início": result.transmission_start,
                    "fim": result.transmission_end + timedelta(days=1),
                },
                {
                    "cenário": result.scenario,
                    "fase": "Data informada",
                    "início": result.reported_date,
                    "fim": result.reported_date + timedelta(days=1),
                },
            ]
        )
    return pd.DataFrame(rows)


def to_iso_payload(results: list[ScenarioResult], params: CalculatorParams) -> dict:
    payload = {
        "params": asdict(params),
        "scenarios": [],
    }
    for result in results:
        item = asdict(result)
        for field in [
            "reported_date",
            "estimated_symptom_onset",
            "exposure_start",
            "exposure_end",
            "transmission_start",
            "transmission_end",
        ]:
            item[field] = item[field].isoformat()
        payload["scenarios"].append(item)
    return payload


# ============================================================
# Utilitários para contatos
# ============================================================

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


def clean_text(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def default_contacts_df() -> pd.DataFrame:
    today = date.today()
    return pd.DataFrame(
        [
            {
                "identificador": "Contato 1",
                "nome_codigo": "",
                "caso_origem": "Caso índice",
                "data_ultimo_contato": today,
                "tipo_contato": "domiciliar / cuidado / funeral / serviço de saúde / outro",
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
                "tipo_contato": "",
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


def get_source_window_for_contact(
    source_id: str,
    contacts_by_id: dict[str, dict],
    index_scenarios: list[ScenarioResult],
) -> tuple[str, str]:
    source_id = clean_text(source_id) or "Caso índice"

    if source_id == "Caso índice":
        windows = [
            s.scenario
            for s in index_scenarios
        ]
        if not windows:
            return "Não avaliado", "-"
        return "Caso índice", ", ".join(windows)

    source = contacts_by_id.get(source_id)
    if source is None:
        return "Origem não encontrada", "-"

    source_onset = coerce_date(source.get("data_inicio_sintomas"))
    source_end = coerce_date(source.get("data_fim_transmissibilidade"))
    if source_onset is None or source_end is None:
        return "Origem sem janela transmissível informada", "-"

    return "Contato/caso secundário", f"{source_onset.strftime('%d/%m/%Y')} a {source_end.strftime('%d/%m/%Y')}"


def is_contact_compatible_with_source(
    source_id: str,
    last_contact: date,
    contacts_by_id: dict[str, dict],
    index_scenarios: list[ScenarioResult],
) -> tuple[str, str]:
    source_id = clean_text(source_id) or "Caso índice"

    if source_id == "Caso índice":
        compatible = [
            s.scenario
            for s in index_scenarios
            if s.transmission_start <= last_contact <= s.transmission_end
        ]
        if compatible:
            return "Sim", ", ".join(compatible)
        return "Não", "-"

    source = contacts_by_id.get(source_id)
    if source is None:
        return "Não avaliado", "Caso-origem não localizado"

    source_onset = coerce_date(source.get("data_inicio_sintomas"))
    source_end = coerce_date(source.get("data_fim_transmissibilidade"))

    if source_onset is None or source_end is None:
        return "Não avaliado", "Informe início de sintomas e fim de transmissibilidade do caso-origem"

    if source_onset <= last_contact <= source_end:
        return "Sim", f"{source_onset.strftime('%d/%m/%Y')} a {source_end.strftime('%d/%m/%Y')}"
    return "Não", "-"


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

    # Itens desconectados ficam em geração 1 para aparecerem no mapa.
    for node in nodes:
        if node not in generation:
            generation[node] = 1

    return generation


def evaluate_contacts(
    contacts_df: pd.DataFrame,
    scenario_results: list[ScenarioResult],
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

        if last_contact is None:
            evaluated_rows.append(
                {
                    "geração": generations.get(identifier, 1),
                    "identificador": identifier,
                    "nome/código": clean_text(row.get("nome_codigo")),
                    "caso-origem": source,
                    "data do último contato": None,
                    "tipo de contato": clean_text(row.get("tipo_contato")),
                    "município": clean_text(row.get("municipio")),
                    "risco": clean_text(row.get("risco")) or "Não classificado",
                    "evolução": evolution,
                    "compatível com janela transmissível?": "Data inválida/ausente",
                    "hipóteses/janela compatível": "-",
                    "possível início de sintomas": "-",
                    "monitorar até": "-",
                    "situação do prazo": "Não avaliado",
                    "data de início dos sintomas": onset,
                    "data da última avaliação": coerce_date(row.get("data_ultima_avaliacao")),
                    "observação": clean_text(row.get("observacao")),
                }
            )
            continue

        compatible_label, compatible_detail = is_contact_compatible_with_source(
            source_id=source,
            last_contact=last_contact,
            contacts_by_id=contacts_by_id,
            index_scenarios=scenario_results,
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
                f"{symptom_window_start.strftime('%d/%m/%Y')} a {symptom_window_end.strftime('%d/%m/%Y')} "
                f"({'compatível' if onset_compatible else 'fora da janela'})"
            )
        else:
            onset_text = f"{symptom_window_start.strftime('%d/%m/%Y')} a {symptom_window_end.strftime('%d/%m/%Y')}"

        evaluated_rows.append(
            {
                "geração": generations.get(identifier, 1),
                "identificador": identifier,
                "nome/código": clean_text(row.get("nome_codigo")),
                "caso-origem": source,
                "data do último contato": last_contact,
                "tipo de contato": clean_text(row.get("tipo_contato")),
                "município": clean_text(row.get("municipio")),
                "risco": clean_text(row.get("risco")) or "Não classificado",
                "evolução": evolution,
                "compatível com janela transmissível?": compatible_label,
                "hipóteses/janela compatível": compatible_detail,
                "possível início de sintomas": onset_text,
                "monitorar até": monitoring_end,
                "situação do prazo": deadline_status,
                "data de início dos sintomas": onset,
                "data da última avaliação": coerce_date(row.get("data_ultima_avaliacao")),
                "observação": clean_text(row.get("observacao")),
            }
        )

    return pd.DataFrame(evaluated_rows)


def make_contacts_timeline(evaluated_contacts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if evaluated_contacts.empty:
        return pd.DataFrame(columns=["identificador", "fase", "início", "fim"])

    for _, row in evaluated_contacts.iterrows():
        contact_date = coerce_date(row.get("data do último contato"))
        if contact_date is None:
            continue

        monitoring_end = coerce_date(row.get("monitorar até"))
        if monitoring_end is None:
            continue

        possible_text = clean_text(row.get("possível início de sintomas"))
        # Remove anotação "(compatível)" se existir.
        possible_text = possible_text.split(" (")[0]
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


def render_chain_graph(contacts_df: pd.DataFrame, evaluated: pd.DataFrame) -> None:
    contacts = normalize_contacts_df(contacts_df)
    if contacts.empty:
        st.info("Inclua contatos para gerar o mapa da cadeia de transmissão.")
        return

    edges = make_chain_edges(contacts)
    generations = calculate_contact_generation(contacts)

    nodes = set(["Caso índice"])
    for _, row in contacts.iterrows():
        nodes.add(clean_text(row.get("identificador")))
        nodes.add(clean_text(row.get("caso_origem")) or "Caso índice")
    nodes = {n for n in nodes if n}

    # Metadados de cada nó
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
        if not gen_nodes:
            continue
        count = len(gen_nodes)
        for idx, node in enumerate(gen_nodes):
            y = count - idx
            positions[node] = (gen, y)

    # Garante posição para eventual nó sem geração definida
    for idx, node in enumerate(sorted(nodes)):
        if node not in positions:
            positions[node] = (generations.get(node, 1), idx + 1)

    fig = go.Figure()

    # Linhas das arestas
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

    # Setas
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

    st.markdown("#### Relação de vínculos da cadeia")
    display_edges = edges.copy()
    if not display_edges.empty:
        display_edges["data do contato"] = pd.to_datetime(display_edges["data do contato"]).dt.strftime("%d/%m/%Y")
    st.dataframe(display_edges, use_container_width=True, hide_index=True)


# ============================================================
# Interface Streamlit
# ============================================================

def configure_page() -> None:
    st.set_page_config(
        page_title="Calculadora Ebola",
        page_icon="🦠",
        layout="wide",
    )

    st.title("Calculadora Ebola")
    st.caption(
        "Janela provável de exposição, transmissibilidade, contatos, prazos de monitoramento, evolução e mapa de possível cadeia de transmissão."
    )


def sidebar_params() -> CalculatorParams:
    with st.sidebar:
        st.header("Parâmetros editáveis")

        use_classic = st.toggle(
            "Usar incubação clássica 2–21 dias",
            value=False,
            help="Guias técnicos costumam citar 2–21 dias. O cálculo operacional original da ferramenta de exposição usa 4–17 dias como padrão ajustável.",
        )

        if use_classic:
            min_inc = 2
            max_inc = 21
            st.info("Incubação configurada como 2–21 dias.")
        else:
            min_inc = st.number_input("Incubação mínima, em dias", min_value=1, max_value=60, value=4)
            max_inc = st.number_input("Incubação máxima, em dias", min_value=1, max_value=60, value=17)

        wet_offset = st.number_input(
            "Dias entre início dos sintomas e sintomas úmidos",
            min_value=0,
            max_value=30,
            value=4,
        )
        hemorr_offset = st.number_input(
            "Dias entre início dos sintomas e sintomas hemorrágicos",
            min_value=0,
            max_value=30,
            value=7,
        )
        death_offset = st.number_input(
            "Dias entre início dos sintomas e óbito",
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
            "**Nota técnica:** ajuste os parâmetros conforme protocolo oficial, linhagem viral, contexto do surto e validação da equipe de investigação."
        )

    return CalculatorParams(
        min_incubation_days=int(min_inc),
        max_incubation_days=int(max_inc),
        wet_symptom_offset_days=int(wet_offset),
        hemorrhagic_symptom_offset_days=int(hemorr_offset),
        death_offset_days=int(death_offset),
        contact_monitoring_days=int(monitoring_days),
    )


def render_inputs() -> tuple[date, date, bool, date | None]:
    st.subheader("1. Dados do caso índice")

    c1, c2, c3 = st.columns([0.33, 0.33, 0.34])
    with c1:
        symptom_report_date = st.date_input(
            "Data informada relacionada aos sintomas",
            value=date.today(),
            help="O sistema calculará automaticamente três cenários: sintomas secos, sintomas úmidos e sintomas hemorrágicos.",
        )
    with c2:
        transmission_end = st.date_input(
            "Data final para busca de contatos",
            value=date.today(),
            help="Use a data de isolamento, óbito, sepultamento seguro, último contato possível ou data de encerramento da investigação.",
        )
    with c3:
        include_death = st.checkbox(
            "Incluir cenário por data de óbito",
            value=False,
            help="Útil quando a data de início dos sintomas é desconhecida, conflitante ou pouco confiável.",
        )
        death_date = None
        if include_death:
            death_date = st.date_input("Data de óbito", value=date.today())

    return symptom_report_date, transmission_end, include_death, death_date


def render_scenarios(results: list[ScenarioResult], params: CalculatorParams) -> None:
    st.subheader("2. Janelas calculadas automaticamente")

    df = scenario_results_to_df(results)

    display_df = df.copy()
    date_cols = [
        "data informada",
        "início estimado dos sintomas",
        "início provável da exposição",
        "fim provável da exposição",
        "início da janela transmissível",
        "fim operacional da janela transmissível",
    ]
    for col in date_cols:
        display_df[col] = pd.to_datetime(display_df[col]).dt.strftime("%d/%m/%Y")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    timeline = make_timeline_df(results)
    fig = px.timeline(
        timeline,
        x_start="início",
        x_end="fim",
        y="cenário",
        color="fase",
        hover_data={"fase": True, "início": True, "fim": True},
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=430, margin=dict(l=20, r=20, t=35, b=20), legend_title_text="Fase")
    st.plotly_chart(fig, use_container_width=True)

    payload = to_iso_payload(results, params)
    csv_data = df.to_csv(index=False).encode("utf-8-sig")
    json_data = json.dumps(payload, ensure_ascii=False, indent=2)

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Baixar janelas em CSV",
            data=csv_data,
            file_name="calculadora_ebola_janelas.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "Baixar janelas em JSON",
            data=json_data,
            file_name="calculadora_ebola_janelas.json",
            mime="application/json",
            use_container_width=True,
        )


def render_contact_editor() -> pd.DataFrame:
    st.subheader("3. Cadastro de contatos e evolução")

    st.info(
        "Para dados reais, prefira identificadores ou códigos internos em vez de CPF, nome completo ou outros dados pessoais sensíveis. "
        "Este protótipo não substitui sistema oficial de notificação, investigação ou prontuário."
    )

    uploaded = st.file_uploader(
        "Opcional: importar lista de contatos em CSV",
        type=["csv"],
        help="Use as colunas do modelo exportado pela própria ferramenta para reimportar os dados.",
    )

    if uploaded is not None:
        try:
            default_df = pd.read_csv(uploaded)
            default_df = normalize_contacts_df(default_df)
            if default_df.empty:
                st.warning("O CSV foi lido, mas nenhum contato válido foi identificado.")
                default_df = default_contacts_df()
        except Exception as exc:
            st.error(f"Não foi possível ler o CSV: {exc}")
            default_df = default_contacts_df()
    else:
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
            "tipo_contato": st.column_config.TextColumn("Tipo de contato/exposição"),
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


def render_contacts_analysis(contacts_df: pd.DataFrame, results: list[ScenarioResult], params: CalculatorParams) -> pd.DataFrame:
    st.subheader("4. Monitoramento de contatos")

    evaluated = evaluate_contacts(contacts_df, results, params)

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

    display = evaluated.copy()
    date_cols = [
        "data do último contato",
        "monitorar até",
        "data de início dos sintomas",
        "data da última avaliação",
    ]
    for col in date_cols:
        if col in display.columns:
            display[col] = pd.to_datetime(display[col], errors="coerce").dt.strftime("%d/%m/%Y")
            display[col] = display[col].replace("NaT", "")

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

    st.download_button(
        "Baixar relação de contatos monitorados em CSV",
        data=evaluated.to_csv(index=False).encode("utf-8-sig"),
        file_name="calculadora_ebola_contatos_monitoramento.csv",
        mime="text/csv",
        use_container_width=True,
    )

    return evaluated


def render_chain_section(contacts_df: pd.DataFrame, evaluated: pd.DataFrame) -> None:
    st.subheader("5. Mapa de possível cadeia de transmissão")

    st.markdown(
        "O mapa usa o campo **caso-origem** para montar vínculos entre o caso índice, contatos e possíveis casos secundários. "
        "Quando um contato também se tornar suspeito, confirmado ou sintomático, ele pode ser usado como caso-origem de novos contatos."
    )

    render_chain_graph(contacts_df, evaluated)

    edges = make_chain_edges(contacts_df)
    if not edges.empty:
        st.download_button(
            "Baixar vínculos da cadeia em CSV",
            data=edges.to_csv(index=False).encode("utf-8-sig"),
            file_name="calculadora_ebola_cadeia_transmissao.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_interpretation() -> None:
    st.subheader("6. Interpretação operacional")
    st.markdown(
        """
        **1. Caso índice:** a ferramenta calcula automaticamente hipóteses de exposição e transmissibilidade a partir da data informada.

        **2. Contatos reais:** cada linha representa um contato ou possível caso secundário. Use identificadores internos, data do último contato, tipo de exposição, município, risco e evolução.

        **3. Prazo de monitoramento:** a data limite é calculada a partir do último contato de risco, conforme o número de dias definido na barra lateral.

        **4. Evolução:** o campo permite acompanhar se o contato permanece assintomático, evoluiu com sintomas, tornou-se suspeito/confirmado, foi descartado, evoluiu a óbito ou teve monitoramento encerrado.

        **5. Cadeia de transmissão:** o campo “caso-origem” permite desenhar a cadeia provável. Se o contato C002 teve contato com C001, informe C001 como caso-origem de C002.

        **6. Limite da ferramenta:** compatibilidade temporal não confirma transmissão. A interpretação final depende de investigação epidemiológica, clínica, laboratório, contexto do surto, exposição real e validação da equipe responsável.
        """
    )

    st.warning(
        "Ferramenta de apoio técnico. Não substitui definição de caso, investigação de campo, exames laboratoriais, protocolos oficiais, sistema de notificação ou comunicação imediata às autoridades sanitárias."
    )


def main() -> None:
    configure_page()
    params = sidebar_params()

    symptom_report_date, transmission_end, include_death, death_date = render_inputs()

    try:
        results = calculate_all_scenarios(
            symptom_report_date=symptom_report_date,
            transmission_end=transmission_end,
            params=params,
            include_death_scenario=include_death,
            death_date=death_date,
        )

        invalid_transmission = [r for r in results if r.transmission_end < r.transmission_start]
        if invalid_transmission:
            st.warning(
                "A data final para busca de contatos está anterior ao início estimado dos sintomas em pelo menos um cenário. "
                "Isso pode acontecer quando a data informada de sintomas é tardia ou quando a data final precisa ser ajustada."
            )

        render_scenarios(results, params)
        st.divider()

        contacts_df = render_contact_editor()
        st.divider()

        evaluated = render_contacts_analysis(contacts_df, results, params)
        st.divider()

        render_chain_section(contacts_df, evaluated)
        st.divider()

        render_interpretation()

    except Exception as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
