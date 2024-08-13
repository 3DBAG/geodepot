import pytest

from geodepot.user import *


@pytest.fixture
def mock_env_config(monkeypatch, data_dir):
    monkeypatch.setenv(GEODEPOT_CONFIG_ENV_VAR, data_dir / "geodepot_config")


def test_read_system_config(mock_env_config):
    user = User.read_system_config()
    assert user.name == "Kovács János"


def test_write_system_config(mock_env_config):
    user_original = User.read_system_config()
    User("Test", "email").write_system_config()
    user = User.read_system_config()
    assert user.name == "Test"
    # Restore the original values
    user_original.write_system_config()
