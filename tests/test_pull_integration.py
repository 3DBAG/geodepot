import json
import tarfile
from pathlib import Path
from shutil import rmtree

import pytest
from click.testing import CliRunner

from geodepot.cli import geodepot_grp


REMOTE_URL = "ssh://root@localhost:2222:/srv/geodepot/.geodepot"


@pytest.mark.integration
def test_pull_downloads_and_extracts_data_from_docker_ssh(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    server_repo = data_dir / "integration" / "server" / ".geodepot"
    _reset_server_repo(server_repo)
    _seed_server_data_archive(
        server_repo=server_repo,
        source_index=data_dir / "mock_project" / ".geodepot" / "index.geojson",
        source_data=data_dir / "sources" / "wippolder" / "wippolder.gpkg",
        case_name="wippolder",
        data_name="wippolder.gpkg",
    )

    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["remote", "add", "ssh", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["pull", "-y", "ssh"], catch_exceptions=False
    )
    assert result.exit_code == 0

    local_case_dir = tmp_path / ".geodepot" / "cases" / "wippolder"
    assert (local_case_dir / "wippolder.gpkg.tar").is_file()
    assert (local_case_dir / "wippolder.gpkg").is_file()
    assert not (local_case_dir / "wippolder.tar").exists()

    result = runner.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "wippolder" in result.output
    assert "/wippolder.gpkg" in result.output

    result = runner.invoke(
        geodepot_grp, ["get", "wippolder/wippolder.gpkg"], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert result.output == f"{local_case_dir / 'wippolder.gpkg'}\n"


@pytest.mark.integration
def test_push_uploads_data_archive_only(tmp_path, monkeypatch, data_dir, mock_user_home):
    server_repo = data_dir / "integration" / "server" / ".geodepot"
    _reset_server_repo(server_repo)

    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["remote", "add", "ssh", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp,
        ["add", "wippolder", str(data_dir / "sources" / "wippolder" / "wippolder.gpkg")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["push", "-y", "ssh"], catch_exceptions=False
    )
    assert result.exit_code == 0

    remote_case_dir = server_repo / "cases" / "wippolder"
    assert (remote_case_dir / "wippolder.gpkg.tar").is_file()
    assert not (remote_case_dir / "wippolder.tar").exists()
    assert (server_repo / "index.geojson").is_file()


def _reset_server_repo(server_repo: Path) -> None:
    rmtree(server_repo / "cases", ignore_errors=True)
    (server_repo / "cases").mkdir(parents=True, exist_ok=True)
    (server_repo / "index.geojson").write_text(
        '{"type":"FeatureCollection","name":"index","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:EPSG::3857"}},"features":[]}'
    )


def _seed_server_data_archive(
    server_repo: Path,
    source_index: Path,
    source_data: Path,
    case_name: str,
    data_name: str,
) -> None:
    case_dir = server_repo / "cases" / case_name
    rmtree(case_dir, ignore_errors=True)
    case_dir.mkdir(parents=True, exist_ok=True)

    archive = case_dir / f"{data_name}.tar"
    with tarfile.TarFile(archive, mode="w") as tf:
        tf.add(source_data, arcname=data_name, recursive=False)

    index_data = json.loads(source_index.read_text())
    index_data["features"] = [
        feature
        for feature in index_data["features"]
        if feature["properties"]["case_name"] == case_name
        and feature["properties"]["data_name"] == data_name
    ]
    (server_repo / "index.geojson").write_text(json.dumps(index_data))
