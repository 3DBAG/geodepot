from copy import deepcopy

import pytest

from geodepot.repository import Repository, Index
from geodepot.case import CaseSpec, CaseName
from geodepot.data import DataName
from geodepot.config import RemoteName


@pytest.fixture(scope="function")
def repo(mock_temp_project, mock_user_home):
    repo = Repository(create=True)
    return repo


def test_remove_case(repo, wippolder_dir):
    """Can we remove a case?"""
    repo.add(
        "wippolder",
        pathspec=str(wippolder_dir / "wippolder.gpkg"),
        description="wippolder case description",
        license="CC-0",
    )
    repo.remove(CaseSpec("wippolder"))
    assert repo.path_cases.joinpath("wippolder").exists() is False
    assert repo.get_case(CaseSpec("wippolder")) is None


def test_remove_data(repo, wippolder_dir):
    """Can we remove a data entry?"""
    repo.add(
        "wippolder",
        pathspec=str(wippolder_dir / "wippolder.gpkg"),
        description="wippolder case description",
        license="CC-0",
    )
    casespec = CaseSpec("wippolder", "wippolder.gpkg")
    repo.remove(casespec)
    assert repo.path_cases.joinpath(casespec.to_path()).exists() is False
    assert repo.get_data(casespec) is None


def test_empty(repo):
    """Can we create an empty repository?"""
    assert repo.path.exists()


def test_init_from_url(mock_temp_project):
    repo = Repository(
        path="https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot"
    )
    assert repo.path.exists()
    assert repo.path_index.exists()
    assert repo.path_cases.exists()
    assert repo.path_config_local.exists()
    assert repo.get_case(CaseSpec(case_name="wippolder", data_name=None)) is not None


def test_index_serialize(repo, wippolder_dir):
    """Can we serialize the index?"""
    repo.add(
        "wippolder",
        pathspec=str(wippolder_dir / "wippolder.gpkg"),
        description="wippolder case description",
        license="CC-0",
    )
    repo.index.write(repo.path.joinpath("index.geojson"))
    assert repo.path.joinpath("index.geojson").exists()


def test_index_load(data_dir):
    """Can we deserialize the index?"""
    index = Index.load(data_dir / "test_index.geojson")
    assert CaseName("wippolder") in index.cases


def test_index_load_remote(repo):
    repo.config.add_remote(
        "origin", "https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot"
    )
    repo.load_index(remote=RemoteName("origin"))
    assert repo.index_remote is not None
    assert CaseName("wippolder") in repo.index_remote.cases


def test_add_files(repo, wippolder_dir):
    """Can we add individaual files?"""
    repo.add(
        "wippolder",
        pathspec=str(wippolder_dir / "wippolder.gpkg"),
        description="wippolder case description",
        license="CC-0",
    )
    assert (
        repo.get_data(CaseSpec(CaseName("wippolder"), DataName("wippolder.gpkg")))
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
        repo.get_data(CaseSpec(CaseName("wippolder"), DataName("wippolder.las")))
        is not None
    )
    assert (repo.path_cases / "wippolder" / "wippolder.las").exists()


def test_add_directory(repo, wippolder_dir):
    """Can we add a directory of data files?"""
    repo.add("wippolder", pathspec=str(wippolder_dir))
    case_wippolder = repo.get_case(CaseSpec(case_name="wippolder"))
    assert len(case_wippolder.data) == 5


def test_add_directory_as_data(repo, wippolder_dir):
    """Can we add a directory as a single data entry?"""
    repo.add("wippolder/wippolder_data_file", pathspec=str(wippolder_dir), as_data=True)
    case_wippolder = repo.get_case(CaseSpec(case_name="wippolder"))
    assert len(case_wippolder.data) == 1


def test_update_data(repo, wippolder_dir):
    """Can we update a single data entry, renaming the input file in the process?"""
    repo.add("wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    df_old = deepcopy(repo.get_data(CaseSpec("wippolder", "wippolder.gpkg")))
    repo.add(
        "wippolder/wippolder.gpkg",
        pathspec=str(wippolder_dir / "wippolder_changed.gpkg"),
    )
    df_updated = repo.get_data(CaseSpec("wippolder", "wippolder.gpkg"))
    assert df_old.sha1 == "b1ec6506eb7858b0667281580c4f5a5aff6894b2"
    assert df_updated.sha1 == "ed8b3ccbaf14970a402efd68f7bfa7db20a2543a"


def test_add_description_data(repo, wippolder_dir):
    """Can we add description of a single data entry?"""
    repo.add("wippolder/wippolder.gpkg", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    df_old = deepcopy(repo.get_data(CaseSpec("wippolder", "wippolder.gpkg")))
    assert df_old.description is None
    repo.add("wippolder/wippolder.gpkg", pathspec=None, description="data description")
    df_updated = repo.get_data(CaseSpec("wippolder", "wippolder.gpkg"))
    assert df_updated.description == "data description"


def test_add_description_case(repo, wippolder_dir):
    """Can we add description of a case?"""
    repo.add("wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    df_old = deepcopy(repo.get_data(CaseSpec("wippolder", "wippolder.gpkg")))
    assert df_old.description is None
    repo.add("wippolder/wippolder.gpkg", pathspec=None, description="case description")
    df_updated = repo.get_data(CaseSpec("wippolder", "wippolder.gpkg"))
    assert df_updated.description == "case description"


def test_add_license_data(repo, wippolder_dir):
    """Can we add license to a data entry?"""
    repo.add("wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    df_old = deepcopy(repo.get_data(CaseSpec("wippolder", "wippolder.gpkg")))
    repo.add(
        "wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"), license="CC-0"
    )
    df_updated = repo.get_data(CaseSpec("wippolder", "wippolder.gpkg"))
    assert df_old.license is None
    assert df_updated.license == "CC-0"


def test_get_remote(mock_temp_project):
    """Can we get a data item from the remote repository?"""
    repo = Repository(
        path="https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot"
    )
    data_path = repo.get_data_path(CaseSpec("wippolder", "wippolder.gpkg"))
    assert data_path.exists()
