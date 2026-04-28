import io
import logging

from click.testing import CliRunner

from geodepot.cli import geodepot_grp, setup_logging


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


def test_setup_logging_updates_root_logger_levels():
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_handlers = list(root_logger.handlers)
    custom_handler = logging.StreamHandler(io.StringIO())
    root_logger.handlers[:] = [custom_handler]

    try:
        setup_logging(True)
        assert root_logger.level == logging.DEBUG
        assert custom_handler.level == logging.DEBUG

        setup_logging(False)
        assert root_logger.level == logging.INFO
        assert custom_handler.level == logging.INFO
    finally:
        root_logger.handlers[:] = original_handlers
        root_logger.setLevel(original_level)


def test_cli_verbose_enables_debug_logs(
    mock_user_home, mock_temp_project, wippolder_dir, caplog
):
    runner = CliRunner()

    with caplog.at_level(logging.DEBUG):
        result = runner.invoke(geodepot_grp, ["-v", "init"], catch_exceptions=False)
        assert result.exit_code == 0
        result = runner.invoke(
            geodepot_grp,
            ["-v", "add", "wippolder", str(wippolder_dir / "wippolder.gpkg")],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

    debug_messages = [
        record.message
        for record in caplog.records
        if record.name.startswith("geodepot") and record.levelno == logging.DEBUG
    ]
    assert any("CLI invoked" in message for message in debug_messages)
    assert any("Initializing repository" in message for message in debug_messages)
    assert any("Adding entry" in message for message in debug_messages)
    assert any("Computing sha1" in message for message in debug_messages)
    assert any("Attached data" in message for message in debug_messages)


def test_cli_show_case_verbose_emits_case_debug_logs(caplog, monkeypatch):
    runner = CliRunner()

    from geodepot.case import Case
    from geodepot.config import User

    fake_case = Case(
        "wippolder",
        "case description",
        changed_by=User(name="u", email="u@example.com"),
    )
    fake_repo = type("FakeRepository", (), {"get_case": lambda self, cs: fake_case})()
    monkeypatch.setattr("geodepot.cli.Repository", lambda *args, **kwargs: fake_repo)
    with caplog.at_level(logging.DEBUG):
        result = runner.invoke(
            geodepot_grp, ["-v", "show", "wippolder"], catch_exceptions=False
        )
        assert result.exit_code == 0

    debug_messages = [
        record.message
        for record in caplog.records
        if record.name.startswith("geodepot") and record.levelno == logging.DEBUG
    ]
    assert any(
        "Parsing case specifier wippolder" in message for message in debug_messages
    )
    assert any(
        "Serializing case wippolder for display" in message
        for message in debug_messages
    )


def test_cli_default_keeps_debug_logs_off(
    mock_user_home, mock_temp_project, wippolder_dir, caplog
):
    runner = CliRunner()

    with caplog.at_level(logging.DEBUG):
        result = runner.invoke(geodepot_grp, ["init"], catch_exceptions=False)
        assert result.exit_code == 0
        result = runner.invoke(
            geodepot_grp,
            ["add", "wippolder", str(wippolder_dir / "wippolder.gpkg")],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

    debug_messages = [
        record.message
        for record in caplog.records
        if record.name.startswith("geodepot") and record.levelno == logging.DEBUG
    ]
    assert debug_messages == []
