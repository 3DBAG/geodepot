import pytest

from geodepot.case import *
from geodepot.data import Data


@pytest.mark.parametrize(
    "casespec,expected",
    (
        (
            "wippolder/wippolder.gpkg",
            CaseSpec(case_name="wippolder", data_name="wippolder.gpkg"),
        ),
        ("wippolder", CaseSpec(case_name="wippolder")),
    ),
)
def test_casespec_from_str(casespec, expected):
    """Can we parse the case specifier?"""
    assert CaseSpec.from_str(casespec) == expected


def test_case(data_dir):
    case = Case("wippolder", "Some case description.\nMultiline.\nText")
    for df in ("wippolder.gpkg", "wippolder.las", "3dbag_one.city.json"):
        case.add_data(Data(data_dir / df))
    print(case)
