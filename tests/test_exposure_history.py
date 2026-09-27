from datetime import date
import pytest
from src.domain.exposure import Exposure
from src.services.exposure_history import effective_last_exposure, summarize_exposures

def exp(i,start,end,source="Caso índice"):
    return Exposure(i,"EVT","C1",source,start,end,"Contato domiciliar")

def test_multiple_exposures_derive_true_last_exposure():
    xs=[exp("E1",date(2026,9,1),date(2026,9,1)),exp("E2",date(2026,9,3),date(2026,9,5),"C2")]
    s=summarize_exposures("C1",xs)
    assert s.exposure_count==2
    assert s.first_exposure==date(2026,9,1)
    assert s.last_exposure==date(2026,9,5)
    assert effective_last_exposure("C1",xs,date(2026,8,30))==date(2026,9,5)

def test_legacy_date_is_fallback_only():
    assert effective_last_exposure("C1",[],date(2026,9,2))==date(2026,9,2)

def test_invalid_exposure_period_is_rejected():
    x=exp("E1",date(2026,9,5),date(2026,9,1))
    with pytest.raises(ValueError): x.validate()
