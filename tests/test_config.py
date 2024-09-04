import pytest

from geodepot.config import *
from geodepot.repository import Repository


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
                        "remotes": {"myremote": {"url": "http://myurl"}},
                    },
                    Config(
                        user=User(name="myname", email="<EMAIL>"),
                        remotes={"myremote": Remote(name="myremote", url="http://myurl")},
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
    assert config.remotes["remote-name"].name == "remote-name"


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
                    Config(
                        remotes={"remote-name": Remote(name="remote-name", url="http://url")}),
                    Config(
                        user=User(name="name", email="email"),
                        remotes={"remote-name": Remote(name="remote-name", url="http://url")},
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
    config_new.write(tmp_path / "config.json")
    config_new_from_file = Config.load(tmp_path / "config.json")
    assert config_new == config_new_from_file
    # Restore the original version
    config_original.write(get_global_config_path())


def test_user_from_pretty():
    user = User.from_pretty("Kovács János <janos@kovacs.me>")
    assert user.name == "Kovács János"
    assert user.email == "janos@kovacs.me"


def test_configure_set(mock_user_home, mock_project_dir):
    oldval = get_global_config().user.name
    configure(key="user.name", value="My Name", global_config=True)
    config = get_global_config()
    assert config.user.name == "My Name"
    configure(key="user.name", value=oldval, global_config=True)


def test_configure_set_new(mock_temp_project):
    Repository(create=True)
    configure(key="user.name", value="My Name")
    configure(key="user.email", value="email")
    config = get_local_config()
    assert config.user.name == "My Name"
    assert config.user.email == "email"


def test_configure_get(mock_user_home, mock_project_dir):
    val = configure(key="user.name", global_config=True)
    assert val == "Kovács János"
    config = get_global_config()
    assert config.user.name == "Kovács János"


def test_remote_url():
    remote = Remote(name="myremote",
                    url="ssh://vagrant@192.168.56.5:/srv/geodepot/.geodepot")
    assert remote.name == "myremote"
    assert remote.url == "vagrant@192.168.56.5"
    assert remote.path_index == "/srv/geodepot/.geodepot/index.geojson"
