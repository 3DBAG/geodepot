import json
import tarfile
from pathlib import Path
from shutil import rmtree

import pytest

from geodepot.case import CaseSpec
from geodepot.config import RemoteName
from geodepot.repository import Repository, Status


@pytest.mark.integration
def test_pull_downloads_and_extracts_case_from_docker_ssh(
    tmp_path, monkeypatch, data_dir
):
    server_repo = data_dir / "integration" / "server" / ".geodepot"
    case_name = "wippolder"
    source_name = "wippolder.gpkg"
    _seed_server_case_archive(
        server_repo=server_repo,
        source_index=data_dir / "mock_project" / ".geodepot" / "index.geojson",
        source_data=data_dir / "sources" / case_name / source_name,
        case_name=case_name,
        source_name=source_name,
    )

    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    repo = Repository(create=True)
    repo.config.add_remote("ssh", "ssh://root@localhost:2222:/srv/geodepot/.geodepot")

    diff_all = repo.fetch(RemoteName("ssh"))

    assert len(diff_all) == 1
    assert diff_all[0].status == Status.ADD
    assert diff_all[0].casespec_other == CaseSpec(case_name)

    repo.pull(RemoteName("ssh"), diff_all)

    local_case_dir = repo.path_cases / case_name
    assert (local_case_dir / f"{case_name}.tar").is_file()
    assert (local_case_dir / source_name).is_file()


def _seed_server_case_archive(
    server_repo: Path,
    source_index: Path,
    source_data: Path,
    case_name: str,
    source_name: str,
) -> None:
    case_dir = server_repo / "cases" / case_name
    rmtree(case_dir, ignore_errors=True)
    case_dir.mkdir(parents=True)

    archive = case_dir / f"{case_name}.tar"
    with tarfile.TarFile(archive, mode="w") as tf:
        tf.add(source_data, arcname=source_name, recursive=False)

    index_data = json.loads(source_index.read_text())
    index_data["features"] = [
        feature
        for feature in index_data["features"]
        if feature["properties"]["case_name"] == case_name
        and feature["properties"]["data_name"] == source_name
    ]
    (server_repo / "index.geojson").write_text(json.dumps(index_data))
