import pytest

from geodepot.repository import *
from geodepot.data_file import DataFile


@pytest.fixture
def mock_temp_project(tmp_path, monkeypatch):
    def mockreturn():
        return tmp_path

    monkeypatch.setattr(Path, "cwd", mockreturn)


def test_empty(mock_temp_project):
    """Can we create an empty repository?"""
    repo = Repository()
    repo.init()
    print(repo)


def test_with_cases(mock_temp_project, data_dir):
    repo = Repository()
    repo.init()

    case = Case("wippolder", "Some case description.\nMultiline.\nText")
    for df in ("wippolder.gpkg", "wippolder.las", "3dbag_one.city.json"):
        case.add_data_file(DataFile(data_dir / df))
    repo.index.add_case(case)

    # fishy
    repo.index.serialize(repo.path.joinpath("index.geojson"))
    print(repo)
