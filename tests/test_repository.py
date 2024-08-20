from copy import deepcopy

import pytest

from geodepot.data_file import DataFileName
from geodepot.repository import *


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


def test_index_serialize(mock_temp_project, mock_user_home, wippolder_dir):
    """Can we serialize the index?"""
    repo = Repository()
    repo.init()
    repo.add(
        "wippolder",
        pathspec=str(wippolder_dir / "wippolder.gpkg"),
        description="wippolder case description",
        license="CC-0",
    )
    repo.index.serialize(repo.path.joinpath("index.geojson"))
    assert repo.path.joinpath("index.geojson").exists()


def test_index_load(data_dir):
    """Can we deserialize the index?"""
    index = Index.deserialize(data_dir / "test_index.geojson")
    assert CaseName("wippolder") in index.cases


def test_add_files(mock_temp_project, mock_user_home, wippolder_dir):
    """Can we add individaual files?"""
    repo = Repository()
    repo.init()

    repo.add(
        "wippolder",
        pathspec=str(wippolder_dir / "wippolder.gpkg"),
        description="wippolder case description",
        license="CC-0",
    )
    assert (
        repo.get_data_file(
            CaseSpec(CaseName("wippolder"), DataFileName("wippolder.gpkg"))
        )
        is not None
    )
    assert (repo.path_cases / "wippolder" / "wippolder.gpkg").exists()

    repo.add(
        "wippolder",
        pathspec=str(wippolder_dir / "wippolder.las"),
        description="wippolder case description",
        license="CC-0",
    )
    assert (
        repo.get_data_file(
            CaseSpec(CaseName("wippolder"), DataFileName("wippolder.las"))
        )
        is not None
    )
    assert (repo.path_cases / "wippolder" / "wippolder.las").exists()


def test_add_directory(mock_temp_project, mock_user_home, wippolder_dir):
    """Can we add a directory of data files?"""
    repo = Repository()
    repo.init()
    repo.add("wippolder", pathspec=str(wippolder_dir))
    case_wippolder = repo.get_case(CaseSpec(case_name="wippolder"))
    assert len(case_wippolder.data_files) == 5


def test_add_directory_as_data(mock_temp_project, mock_user_home, wippolder_dir):
    """Can we add a directory as a single data entry?"""
    repo = Repository()
    repo.init()
    repo.add("wippolder/wippolder_data_file", pathspec=str(wippolder_dir), as_data=True)
    case_wippolder = repo.get_case(CaseSpec(case_name="wippolder"))
    assert len(case_wippolder.data_files) == 1


def test_update_data(mock_temp_project, mock_user_home, wippolder_dir):
    """Can we update a single data entry, renaming the input file in the process?"""
    repo = Repository()
    repo.init()
    repo.add("wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    df_old = deepcopy(repo.get_data_file(CaseSpec("wippolder", "wippolder.gpkg")))
    repo.add(
        "wippolder/wippolder.gpkg",
        pathspec=str(wippolder_dir / "wippolder_changed.gpkg"),
    )
    df_updated = repo.get_data_file(CaseSpec("wippolder", "wippolder.gpkg"))
    assert df_old.sha1 == "b1ec6506eb7858b0667281580c4f5a5aff6894b2"
    assert df_updated.sha1 == "ed8b3ccbaf14970a402efd68f7bfa7db20a2543a"


def test_add_description_data(mock_temp_project, mock_user_home, wippolder_dir):
    """Can we add description of a single data entry?"""
    repo = Repository()
    repo.init()
    repo.add("wippolder/wippolder.gpkg", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    df_old = deepcopy(repo.get_data_file(CaseSpec("wippolder", "wippolder.gpkg")))
    assert df_old.description is None
    repo.add("wippolder/wippolder.gpkg", pathspec=None, description="data description")
    df_updated = repo.get_data_file(CaseSpec("wippolder", "wippolder.gpkg"))
    assert df_updated.description == "data description"


def test_add_description_case(mock_temp_project, mock_user_home, wippolder_dir):
    """Can we add description of a case?"""
    repo = Repository()
    repo.init()
    repo.add("wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    df_old = deepcopy(repo.get_data_file(CaseSpec("wippolder", "wippolder.gpkg")))
    assert df_old.description is None
    repo.add("wippolder/wippolder.gpkg", pathspec=None, description="case description")
    df_updated = repo.get_data_file(CaseSpec("wippolder", "wippolder.gpkg"))
    assert df_updated.description == "case description"


def test_add_license_data(mock_temp_project, mock_user_home, wippolder_dir):
    """Can we add license to a data entry?"""
    repo = Repository()
    repo.init()
    repo.add("wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    df_old = deepcopy(repo.get_data_file(CaseSpec("wippolder", "wippolder.gpkg")))
    repo.add(
        "wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"), license="CC-0"
    )
    df_updated = repo.get_data_file(CaseSpec("wippolder", "wippolder.gpkg"))
    assert df_old.license is None
    assert df_updated.license == "CC-0"
