import pytest

from geodepot.config import *


@pytest.mark.parametrize(
    "config_dict,expected",
    (
        (dict(), dict()),
        (
            {"user": {"name": "myname", "email": "<EMAIL>"}},
            Config(user=User(name="myname", email="<EMAIL>")),
        ),
        (
            {
                "user": {"name": "myname", "email": "<EMAIL>"},
                "remotes": {"myremote": {"url": "myurl"}},
            },
            Config(
                user=User(name="myname", email="<EMAIL>"),
                remotes=[Remote(name="myremote", url="myurl")],
            ),
        ),
    ),
)
def test_as_config(config_dict: dict, expected: Config):
    """Can we decode a configuration JSON object?"""
    assert as_config(config_dict) == expected


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
            Config(
                user=User(name="name", email="email"),
                remotes=[Remote(name="remote-name", url="url")],
            ),
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
