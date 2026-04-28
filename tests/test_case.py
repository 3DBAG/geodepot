import logging

import pytest

from geodepot.case import CaseSpec, Case
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


def test_case_remove_missing_data_logs_context(caplog):
    case = Case("wippolder", "Some case description.")

    with caplog.at_level(logging.DEBUG, logger="geodepot.case"):
        assert case.remove_data("missing.gpkg") is None

    messages = [
        record.message
        for record in caplog.records
        if record.name == "geodepot.case" and record.levelno == logging.DEBUG
    ]
    assert any(
        "Removing data missing.gpkg from case wippolder" in message
        for message in messages
    )
    assert any(
        "No data missing.gpkg found in case wippolder" in message
        for message in messages
    )
