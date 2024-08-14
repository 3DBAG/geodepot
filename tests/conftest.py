from pathlib import Path

import pytest


@pytest.fixture
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
