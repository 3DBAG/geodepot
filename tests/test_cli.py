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
