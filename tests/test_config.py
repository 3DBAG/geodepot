import pytest

from geodepot.config import *


@pytest.fixture
def mock_user_home(monkeypatch, data_dir):
    def mockreturn():
        return data_dir / "mock_user_home"

    monkeypatch.setattr(Path, "home", mockreturn)


@pytest.fixture
def mock_project_dir(monkeypatch, data_dir):
    def mockreturn():
        return data_dir / "mock_project"

    monkeypatch.setattr(Path, "cwd", mockreturn)


def test_read_global_config(mock_user_home):
    config = get_global_config()
    assert config.user.name == "Kovács János"


def test_read_local_config(mock_project_dir):
    config = get_local_config()
    assert config.remotes[0].name == "remote-name"


@pytest.mark.parametrize(
    "config_global,config_local,expected",
    (
        (
            Config(user=User(name="name", email="email")),
            Config(),
            Config(user=User(name="name", email="email")),
        ),
        (
            Config(user=User(name="name", email="email")),
            Config(remotes=[Remote(name="remote-name", url="url")]),
            Config(user=User(name="name", email="email"), remotes=[Remote(name="remote-name", url="url")]),
        ),
    ),
)
def test_update(config_global, config_local, expected):
    config_global.update(config_local)
    assert config_global == expected


def test_write_config(mock_user_home, tmp_path):
    config_original = get_global_config()
    config_new = Config(
        user=User(
            name="<NAME>",
            email="<EMAIL>",
        )
    )
    config_new.write_to_file(tmp_path / "config.json")
    config_new_from_file = Config.read_from_file(tmp_path / "config.json")
    assert config_new == config_new_from_file
    # Restore the original version
    config_original.write_to_file(get_global_config_path())
