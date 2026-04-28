from copy import deepcopy
from pathlib import Path

import pytest

from geodepot.repository import Repository, Index, IndexDiff, Status
from geodepot.case import Case, CaseSpec, CaseName
from geodepot.data import Data, DataName
from geodepot.config import RemoteName
from geodepot.errors import GeodepotIndexError, GeodepotRuntimeError
from geodepot.errors import GeodepotSyncError


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
    assert (repo.path_cases / "wippolder" / "wippolder.gpkg.tar").exists()

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
    assert (repo.path_cases / "wippolder" / "wippolder.las.tar").exists()


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


def test_get_local(mock_project_dir):
    """Can we retrieve the local path of a data item?"""
    repo = Repository()
    p = repo.get_data_path(CaseSpec("wippolder", "wippolder.gpkg"))
    assert p.exists()


def test_get_remote(mock_temp_project):
    """Can we get a data item from the remote repository?"""
    repo = Repository(
        path="https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot"
    )
    data_path = repo.get_data_path(CaseSpec("wippolder", "wippolder.gpkg"))
    assert data_path.exists()


def test_index_load_missing_raises(tmp_path):
    """Index.load() must raise GeodepotIndexError, not return None."""
    with pytest.raises(GeodepotIndexError):
        Index.load(tmp_path / "nonexistent.geojson")


def test_index_load_corrupt_raises(tmp_path):
    """Index.load() must raise GeodepotIndexError on corrupt GeoJSON."""
    p = tmp_path / "bad.geojson"
    p.write_text("not json {{{")
    with pytest.raises(GeodepotIndexError):
        Index.load(p)


def test_add_rollback_on_compress_failure(repo, wippolder_dir, monkeypatch):
    """If compression fails, the index must not be updated and no orphan file left."""
    monkeypatch.setattr(repo, "_compress_data", lambda p: Path("/nonexistent.tar"))
    with pytest.raises(GeodepotRuntimeError):
        repo.add("wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    case = repo.get_case(CaseSpec("wippolder"))
    assert case is None or len(case.data) == 0
    assert not (repo.path_cases / "wippolder" / "wippolder.gpkg").exists()


def test_remove_missing_archive_ok(repo, wippolder_dir):
    """remove() must succeed even when the .tar archive is already gone."""
    repo.add("wippolder", pathspec=str(wippolder_dir / "wippolder.gpkg"))
    (repo.path_cases / "wippolder" / "wippolder.gpkg.tar").unlink()
    repo.remove(CaseSpec("wippolder", "wippolder.gpkg"))  # must not raise
    assert repo.get_data(CaseSpec("wippolder", "wippolder.gpkg")) is None


def test_pull_reports_failed_download_context(repo, monkeypatch):
    """pull() should report which archive and operation failed."""
    repo.config.add_remote("ssh", "ssh://example.com:/srv/geodepot")
    diff_all = [
        IndexDiff(
            status=Status.ADD,
            casespec_other=CaseSpec("wippolder", "wippolder.gpkg"),
        )
    ]

    class FakeConnection:
        def __init__(self, host):
            self.host = host

        def get(self, local, remote):
            raise RuntimeError("sftp stat failed")

    monkeypatch.setattr("fabric.Connection", FakeConnection)

    with pytest.raises(GeodepotSyncError) as excinfo:
        repo.pull(RemoteName("ssh"), diff_all)

    message = str(excinfo.value)
    assert "download wippolder/wippolder.gpkg" in message
    assert "/srv/geodepot/cases/wippolder/wippolder.gpkg.tar" in message
    assert "RuntimeError: sftp stat failed" in message


def test_pull_reports_failed_download_context_for_case(repo, monkeypatch):
    """pull() should use the case directory for case archives."""
    repo.config.add_remote("ssh", "ssh://example.com:/srv/geodepot")
    diff_all = [
        IndexDiff(
            status=Status.ADD,
            casespec_other=CaseSpec("ams-up-large"),
        )
    ]

    class FakeConnection:
        def __init__(self, host):
            self.host = host

        def get(self, local, remote):
            raise RuntimeError("sftp stat failed")

    monkeypatch.setattr("fabric.Connection", FakeConnection)

    with pytest.raises(GeodepotSyncError) as excinfo:
        repo.pull(RemoteName("ssh"), diff_all)

    message = str(excinfo.value)
    assert "download ams-up-large" in message
    assert "/srv/geodepot/cases/ams-up-large/ams-up-large.tar" in message
    assert str(repo.path_cases / "ams-up-large" / "ams-up-large.tar") in message
    assert "RuntimeError: sftp stat failed" in message


def test_pull_falls_back_to_data_archives_for_missing_case_archive(repo, monkeypatch):
    """pull() should handle remotes that have per-data archives but no case archive."""
    repo.config.add_remote("ssh", "ssh://example.com:/srv/geodepot")
    remote_case = Case(name=CaseName("bvz-dh-coast-5"), description=None)
    remote_case.add_data(
        Data(Path("bvz_dh"), data_name=DataName("bvz_dh"), data_format="directory")
    )
    remote_case.add_data(
        Data(
            Path("profile-tyler.json"),
            data_name=DataName("profile-tyler.json"),
            data_format="JSON",
        )
    )
    repo.index_remote = Index(cases={remote_case.name: remote_case})
    diff_all = [
        IndexDiff(
            status=Status.ADD,
            casespec_other=CaseSpec(remote_case.name),
        )
    ]
    downloaded: list[str] = []
    decompressed: list[CaseSpec] = []

    class FakeConnection:
        def __init__(self, host):
            self.host = host

        def get(self, local, remote):
            downloaded.append(remote)
            if remote.endswith("/bvz-dh-coast-5/bvz-dh-coast-5.tar"):
                raise FileNotFoundError(2, "No such file")
            Path(local).parent.mkdir(parents=True, exist_ok=True)
            Path(local).touch()

    monkeypatch.setattr("fabric.Connection", FakeConnection)
    monkeypatch.setattr(
        repo,
        "_decompress_data",
        lambda _archive, casespec: decompressed.append(casespec) or True,
    )

    repo.pull(RemoteName("ssh"), diff_all)

    assert downloaded == [
        "/srv/geodepot/cases/bvz-dh-coast-5/bvz-dh-coast-5.tar",
        "/srv/geodepot/cases/bvz-dh-coast-5/bvz_dh.tar",
        "/srv/geodepot/cases/bvz-dh-coast-5/profile-tyler.json.tar",
        "/srv/geodepot/index.geojson",
    ]
    assert decompressed == [
        CaseSpec(remote_case.name, DataName("bvz_dh")),
        CaseSpec(remote_case.name, DataName("profile-tyler.json")),
    ]
