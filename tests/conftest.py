from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def data_dir():
    return Path(__file__).parent / 'data'

@pytest.fixture(scope='function')
def mock_user_home(monkeypatch, data_dir):
    def mockreturn():
        return data_dir / "mock_user_home"

    monkeypatch.setattr(Path, "home", mockreturn)


@pytest.fixture(scope='function')
def mock_project_dir(monkeypatch, data_dir):
    def mockreturn():
        return data_dir / "mock_project"

    monkeypatch.setattr(Path, "cwd", mockreturn)


@pytest.fixture(scope="session")
def monkeysession():
    with pytest.MonkeyPatch.context() as mp:
        yield mp

@pytest.fixture(scope="session", autouse=True)
def mock_proj_lib(monkeysession, data_dir):
    monkeysession.setenv("PROJ_LIB", data_dir)