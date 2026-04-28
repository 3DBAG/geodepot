from click.testing import CliRunner

from geodepot.cli import geodepot_grp


def test_cli_add_and_list(mock_user_home, mock_temp_project, wippolder_dir):
    """End-to-end: init → add → list shows the case."""
    runner = CliRunner()
    runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    result = runner.invoke(
        geodepot_grp,
        ["add", "wippolder", str(wippolder_dir / "wippolder.gpkg")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    result = runner.invoke(geodepot_grp, ["list"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "wippolder" in result.output


def test_cli_get_prints_plain_path(
    mock_user_home, mock_temp_project, wippolder_dir, tmp_path
):
    """`get` should emit only the resolved path on stdout."""
    runner = CliRunner()
    runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
    result = runner.invoke(
        geodepot_grp,
        ["add", "wippolder", str(wippolder_dir / "wippolder.gpkg")],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    result = runner.invoke(
        geodepot_grp,
        ["get", "wippolder/wippolder.gpkg"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    expected_path = tmp_path / ".geodepot" / "cases" / "wippolder" / "wippolder.gpkg"
    assert result.output == f"{expected_path}\n"
    assert "INFO:" not in result.output
