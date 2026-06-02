import json
import os
import tarfile
from pathlib import Path
from shutil import rmtree

import pytest
from click.testing import CliRunner

from geodepot.cli import geodepot_grp


REMOTE_HOST = os.environ.get("GEODEPOT_TEST_REMOTE_HOST", "localhost")
REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot/.geodepot"


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
    result = runner.invoke(geodepot_grp, ["pull", "-y", "ssh"], catch_exceptions=False)
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
def test_push_uploads_data_archive_only(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
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
        [
            "add",
            "wippolder",
            str(data_dir / "sources" / "wippolder" / "wippolder.gpkg"),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    result = runner.invoke(geodepot_grp, ["push", "-y", "ssh"], catch_exceptions=False)
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


# =============================================================================
# Empty Remote Repository Tests
# =============================================================================


@pytest.mark.integration
def test_init_from_empty_remote(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    """Initialize from empty remote repository."""
    server_repo = data_dir / "integration" / "server_empty" / ".geodepot"
    server_repo.mkdir(parents=True, exist_ok=True)
    _reset_server_repo(server_repo)

    REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot_empty/.geodepot"
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        geodepot_grp, ["init", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0
    # Verify empty repo was created locally
    assert (tmp_path / ".geodepot").exists()
    assert (tmp_path / ".geodepot" / "index.geojson").exists()

    result = runner.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert "Repository is empty" in result.output


@pytest.mark.integration
def test_push_to_empty_remote(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    """Push to empty remote repository."""
    server_repo = data_dir / "integration" / "server_empty" / ".geodepot"
    _reset_server_repo(server_repo)

    REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot_empty/.geodepot"
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["remote", "add", "origin", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp,
        ["add", "test", str(data_dir / "sources" / "wippolder" / "wippolder.gpkg")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Push to empty remote
    result = runner.invoke(geodepot_grp, ["push", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # Verify data exists on server
    remote_case_dir = server_repo / "cases" / "test"
    assert (remote_case_dir / "wippolder.gpkg.tar").is_file()


# =============================================================================
# Existing Remote with Data Tests
# =============================================================================


@pytest.mark.integration
def test_pull_from_populated_remote(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    """Pull from remote that has existing data."""
    server_repo = data_dir / "integration" / "server" / ".geodepot"
    _reset_server_repo(server_repo)

    # Seed server with multiple data items
    _seed_server_data_archive(
        server_repo=server_repo,
        source_index=data_dir / "mock_project" / ".geodepot" / "index.geojson",
        source_data=data_dir / "sources" / "wippolder" / "wippolder.gpkg",
        case_name="wippolder",
        data_name="wippolder.gpkg",
    )
    _seed_server_data_archive(
        server_repo=server_repo,
        source_index=data_dir / "mock_project" / ".geodepot" / "index.geojson",
        source_data=data_dir / "sources" / "wippolder" / "wippolder.las",
        case_name="wippolder",
        data_name="wippolder.las",
    )

    REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot/.geodepot"
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["remote", "add", "origin", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0

    # Pull from populated remote
    result = runner.invoke(geodepot_grp, ["pull", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # Verify both data items exist locally
    result = runner.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert "wippolder" in result.output
    assert "/wippolder.gpkg" in result.output
    assert "/wippolder.las" in result.output


@pytest.mark.integration
def test_push_to_existing_remote_with_data(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    """Push to an existing remote repository that already has data."""
    server_repo = data_dir / "integration" / "server" / ".geodepot"
    _reset_server_repo(server_repo)

    # Seed server with initial data
    _seed_server_data_archive(
        server_repo=server_repo,
        source_index=data_dir / "mock_project" / ".geodepot" / "index.geojson",
        source_data=data_dir / "sources" / "wippolder" / "wippolder.gpkg",
        case_name="existing_case",
        data_name="wippolder.gpkg",
    )

    REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot/.geodepot"
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["remote", "add", "origin", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0

    # Add new data to a new case
    result = runner.invoke(
        geodepot_grp,
        ["add", "new_case", str(data_dir / "sources" / "wippolder" / "wippolder.las")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Push to existing remote (should add new case and data)
    result = runner.invoke(geodepot_grp, ["push", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # Verify data exists on server
    remote_case_dir = server_repo / "cases" / "new_case"
    assert (remote_case_dir / "wippolder.las.tar").is_file()

    # Verify both cases exist on server
    server_index = json.loads((server_repo / "index.geojson").read_text())
    case_names = {f["properties"]["case_name"] for f in server_index["features"]}
    assert "existing_case" in case_names
    assert "new_case" in case_names

    # Verify both data items exist
    data_names = {f["properties"]["data_name"] for f in server_index["features"]}
    assert "wippolder.gpkg" in data_names
    assert "wippolder.las" in data_names


# =============================================================================
# Multi-User Collaboration Tests
# =============================================================================


@pytest.mark.integration
def test_two_users_contributing_to_same_remote(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    """Simulate two users pushing to the same remote."""
    import json as json_module

    server_repo = data_dir / "integration" / "server" / ".geodepot"
    _reset_server_repo(server_repo)

    REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot/.geodepot"

    # User 1: Create repo and push initial data
    user1_dir = tmp_path / "user1"
    user1_dir.mkdir()
    monkeypatch.setattr(Path, "cwd", lambda: user1_dir)
    runner = CliRunner()

    # Configure user1
    (user1_dir / ".geodepotconfig.json").write_text(
        json_module.dumps({"user": {"name": "User One", "email": "user1@example.com"}})
    )

    result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["remote", "add", "origin", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp,
        ["add", "case1", str(data_dir / "sources" / "wippolder" / "wippolder.gpkg")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    result = runner.invoke(geodepot_grp, ["push", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # User 2: Clone and add different data to same case
    user2_dir = tmp_path / "user2"
    user2_dir.mkdir()
    monkeypatch.setattr(Path, "cwd", lambda: user2_dir)
    runner2 = CliRunner()

    # Configure user2
    (user2_dir / ".geodepotconfig.json").write_text(
        json_module.dumps({"user": {"name": "User Two", "email": "user2@example.com"}})
    )

    result = runner2.invoke(
        geodepot_grp, ["init", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0
    result = runner2.invoke(
        geodepot_grp,
        ["add", "case1", str(data_dir / "sources" / "wippolder" / "wippolder.las")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # User 2 pushes - should succeed, adding their data
    result = runner2.invoke(geodepot_grp, ["push", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # User 1 pulls - should see new data from User 2
    monkeypatch.setattr(Path, "cwd", lambda: user1_dir)
    result = runner.invoke(geodepot_grp, ["fetch", "origin"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "User Two" in result.output  # Changed by other user

    result = runner.invoke(geodepot_grp, ["pull", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # Verify User 1 now has both data items
    result = runner.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert "case1" in result.output
    assert "/wippolder.gpkg" in result.output
    assert "/wippolder.las" in result.output


@pytest.mark.integration
def test_conflict_detection_modified_same_data(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    """Detect when two users modify the same data item."""
    import json as json_module

    server_repo = data_dir / "integration" / "server" / ".geodepot"
    _reset_server_repo(server_repo)

    REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot/.geodepot"

    # User 1: Create and push
    user1_dir = tmp_path / "user1"
    user1_dir.mkdir()
    monkeypatch.setattr(Path, "cwd", lambda: user1_dir)
    runner = CliRunner()

    (user1_dir / ".geodepotconfig.json").write_text(
        json_module.dumps({"user": {"name": "User One", "email": "user1@example.com"}})
    )

    result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    result = runner.invoke(
        geodepot_grp, ["remote", "add", "origin", REMOTE_URL], catch_exceptions=False
    )
    result = runner.invoke(
        geodepot_grp,
        ["add", "shared", str(data_dir / "sources" / "wippolder" / "wippolder.gpkg")],
        catch_exceptions=False,
    )
    result = runner.invoke(geodepot_grp, ["push", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # User 2: Clone, modify same data
    user2_dir = tmp_path / "user2"
    user2_dir.mkdir()
    monkeypatch.setattr(Path, "cwd", lambda: user2_dir)
    runner2 = CliRunner()

    (user2_dir / ".geodepotconfig.json").write_text(
        json_module.dumps({"user": {"name": "User Two", "email": "user2@example.com"}})
    )

    result = runner2.invoke(
        geodepot_grp, ["init", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0

    # User 2 modifies the description of the same data
    result = runner2.invoke(
        geodepot_grp,
        [
            "add", "shared/wippolder.gpkg",
            "--description", "Modified by User 2"
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # User 2 pushes - should work
    result = runner2.invoke(geodepot_grp, ["push", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # User 1 fetches - should see modification by User 2
    monkeypatch.setattr(Path, "cwd", lambda: user1_dir)
    result = runner.invoke(geodepot_grp, ["fetch", "origin"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "User Two" in result.output
    assert "Modified by User 2" in result.output or "MODIFY" in result.output


# =============================================================================
# HTTP Remote Tests
# =============================================================================


HTTP_REMOTE_URL = "http://localhost:8080/geodepot-test-data/mock_project/.geodepot"


@pytest.mark.integration
def test_push_to_existing_remote_updates_data(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    """Push to an existing remote repository and verify data is updated."""
    import json as json_module

    server_repo = data_dir / "integration" / "server" / ".geodepot"
    _reset_server_repo(server_repo)

    # Seed server with initial data
    _seed_server_data_archive(
        server_repo=server_repo,
        source_index=data_dir / "mock_project" / ".geodepot" / "index.geojson",
        source_data=data_dir / "sources" / "wippolder" / "wippolder.gpkg",
        case_name="shared_case",
        data_name="wippolder.gpkg",
    )

    REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot/.geodepot"

    # User 1: Clone the remote
    user1_dir = tmp_path / "user1"
    user1_dir.mkdir()
    monkeypatch.setattr(Path, "cwd", lambda: user1_dir)
    runner = CliRunner()

    (user1_dir / ".geodepotconfig.json").write_text(
        json_module.dumps({"user": {"name": "User One", "email": "user1@example.com"}})
    )

    result = runner.invoke(
        geodepot_grp, ["init", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0

    # User 1 adds another data item to the same case
    result = runner.invoke(
        geodepot_grp,
        ["add", "shared_case", str(data_dir / "sources" / "wippolder" / "wippolder.las")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # User 1 pushes the new data
    result = runner.invoke(geodepot_grp, ["push", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # Verify both data items exist on server
    server_index = json.loads((server_repo / "index.geojson").read_text())
    shared_case_data = [
        f for f in server_index["features"] 
        if f["properties"]["case_name"] == "shared_case"
    ]
    assert len(shared_case_data) == 2
    data_names = {f["properties"]["data_name"] for f in shared_case_data}
    assert "wippolder.gpkg" in data_names
    assert "wippolder.las" in data_names

    # User 2: Clone the updated remote
    user2_dir = tmp_path / "user2"
    user2_dir.mkdir()
    monkeypatch.setattr(Path, "cwd", lambda: user2_dir)
    runner2 = CliRunner()

    (user2_dir / ".geodepotconfig.json").write_text(
        json_module.dumps({"user": {"name": "User Two", "email": "user2@example.com"}})
    )

    result = runner2.invoke(
        geodepot_grp, ["init", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0

    # Verify User 2 has both data items
    result = runner2.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert "shared_case" in result.output
    assert "/wippolder.gpkg" in result.output
    assert "/wippolder.las" in result.output


@pytest.mark.integration
def test_pull_from_http_remote(
    tmp_path, monkeypatch, mock_user_home
):
    """Test pull from HTTP remote (nginx server)."""
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    result = runner.invoke(
        geodepot_grp, ["remote", "add", "http", HTTP_REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0

    # Note: HTTP is read-only, so only pull should work
    result = runner.invoke(geodepot_grp, ["fetch", "http"], catch_exceptions=False)
    assert result.exit_code == 0

    result = runner.invoke(geodepot_grp, ["pull", "-y", "http"], catch_exceptions=False)
    assert result.exit_code == 0

    # Verify data was pulled
    result = runner.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert "wippolder" in result.output


# =============================================================================
# Additional Test: Push to Existing Remote Repository
# =============================================================================


@pytest.mark.integration
def test_push_to_existing_remote_repo(
    tmp_path, monkeypatch, data_dir, mock_user_home
):
    """
    Test pushing data to an existing remote repository that already has data.
    
    This test specifically verifies that:
    1. A client can clone from an existing remote
    2. Add new data locally
    3. Push the new data to the existing remote
    4. The remote repository is updated with the new data
    5. Both old and new data coexist on the remote
    """
    server_repo = data_dir / "integration" / "server" / ".geodepot"
    _reset_server_repo(server_repo)

    # Seed the server with initial data
    _seed_server_data_archive(
        server_repo=server_repo,
        source_index=data_dir / "mock_project" / ".geodepot" / "index.geojson",
        source_data=data_dir / "sources" / "wippolder" / "wippolder.gpkg",
        case_name="initial_case",
        data_name="wippolder.gpkg",
    )

    REMOTE_URL = f"ssh://root@{REMOTE_HOST}:2222:/srv/geodepot/.geodepot"
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    runner = CliRunner()

    # Client initializes from the existing remote
    result = runner.invoke(
        geodepot_grp, ["init", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0

    # Verify the initial data is available locally
    result = runner.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert "initial_case" in result.output
    assert "/wippolder.gpkg" in result.output

    # Client adds new data to a new case
    result = runner.invoke(
        geodepot_grp,
        ["add", "new_case", str(data_dir / "sources" / "wippolder" / "wippolder.las")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Client pushes the new data to the existing remote
    result = runner.invoke(geodepot_grp, ["push", "-y", "origin"], catch_exceptions=False)
    assert result.exit_code == 0

    # Verify both cases exist on the server
    server_index = json.loads((server_repo / "index.geojson").read_text())
    case_names = {f["properties"]["case_name"] for f in server_index["features"]}
    assert "initial_case" in case_names
    assert "new_case" in case_names

    # Verify both data items exist on the server
    data_names = {f["properties"]["data_name"] for f in server_index["features"]}
    assert "wippolder.gpkg" in data_names
    assert "wippolder.las" in data_names

    # Verify the new data archive exists on the server
    remote_new_case_dir = server_repo / "cases" / "new_case"
    assert (remote_new_case_dir / "wippolder.las.tar").is_file()

    # Another client clones and verifies they get both old and new data
    client2_dir = tmp_path / "client2"
    client2_dir.mkdir()
    monkeypatch.setattr(Path, "cwd", lambda: client2_dir)
    runner2 = CliRunner()

    result = runner2.invoke(
        geodepot_grp, ["init", REMOTE_URL], catch_exceptions=False
    )
    assert result.exit_code == 0

    # Verify client2 has both cases
    result = runner2.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert "initial_case" in result.output
    assert "new_case" in result.output
