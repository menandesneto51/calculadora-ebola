from datetime import date
from src.services.investigation_quality import assess_investigation_quality

def row(cid,source="Caso índice",exposure=date(2026,9,1),onset=None):
    return {"identificador":cid,"caso_origem":source,"data_ultimo_contato":exposure,
            "tipo_contato":"Contato domiciliar","evolucao":"Em monitoramento","data_inicio_sintomas":onset}

def test_detects_duplicate_orphan_self_link_and_cycle():
    rows=[row("A","B"),row("B","A"),row("C","C"),row("D","X"),row("D")]
    q=assess_investigation_quality(rows)
    codes={x.code for x in q.issues}
    assert "DUPLICATE_CONTACT" in codes
    assert "ORPHAN_SOURCE" in codes
    assert "SELF_LINK" in codes
    assert "TRANSMISSION_CYCLE" in codes
    assert q.score < 100

def test_detects_onset_before_exposure():
    q=assess_investigation_quality([row("A",exposure=date(2026,9,10),onset=date(2026,9,9))])
    assert any(x.code=="ONSET_BEFORE_EXPOSURE" for x in q.issues)

def test_complete_clean_investigation_scores_100():
    q=assess_investigation_quality([row("A"),row("B","A")])
    assert q.score==100
    assert q.complete_records==2
    assert not q.issues


def test_structured_exposure_quality_checks():
    from src.domain.exposure import Exposure
    rows=[
        row("A",onset=date(2026,9,5)),
        row("B","A",exposure=date(2026,9,10),onset=date(2026,9,8)),
    ]
    exposures=[
        Exposure("E1","EV","B","A",date(2026,9,9),date(2026,9,9),"Domiciliar"),
        Exposure("E1","EV","B","A",date(2026,9,9),date(2026,9,9),"Domiciliar"),
        Exposure("E2","EV","UNKNOWN","A",date(2026,9,6),date(2026,9,6),"Domiciliar"),
        Exposure("E3","EV","B","UNKNOWN",date(2026,9,6),date(2026,9,6),"Domiciliar"),
    ]
    q=assess_investigation_quality(rows,exposures)
    codes={x.code for x in q.issues}
    assert "DUPLICATE_EXPOSURE" in codes
    assert "EXPOSURE_UNKNOWN_CONTACT" in codes
    assert "EXPOSURE_UNKNOWN_SOURCE" in codes
    assert "ONSET_BEFORE_STRUCTURED_EXPOSURE" in codes
    assert "LEGACY_EXPOSURE_MISMATCH" in codes

def test_exposure_before_known_source_onset_is_review_warning():
    from src.domain.exposure import Exposure
    rows=[row("A",onset=date(2026,9,10)),row("B","A",exposure=date(2026,9,5))]
    exposures=[Exposure("E1","EV","B","A",date(2026,9,4),date(2026,9,5),"Domiciliar")]
    q=assess_investigation_quality(rows,exposures)
    issue=next(x for x in q.issues if x.code=="EXPOSURE_BEFORE_SOURCE_ONSET")
    assert issue.severity=="warning"
