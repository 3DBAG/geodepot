import pytest

from geodepot.repository import Repository
from geodepot.config import (
    User,
    Config,
    Remote,
    get_global_config,
    get_local_config,
    as_config,
    get_global_config_path,
    configure,
)


@pytest.mark.parametrize(
    argnames="config_dict,expected_user_none,expected_user_name,expected_remote_none,expected_remote_name,expected_remote_url,expected_remote_path",
    argvalues=(
        (dict(), True, None, True, None, (None, None), None),
        (
            {"user": {"name": "myname", "email": "<EMAIL>"}},
            False,
            "myname",
            True,
            None,
            (None, None),
            None,
        ),
        (
            {
                "user": {"name": "myname", "email": "<EMAIL>"},
                "remotes": {"myremote": {"url": "http://myurl/.geodepot"}},
            },
            False,
            "myname",
            False,
            "myremote",
            ("http://myurl/.geodepot", None),
            None,
        ),
        (
            {
                "remotes": {
                    "remote-name": {"url": "ssh://some.server:/path/to/.geodepot"}
                }
            },
            True,
            None,
            False,
            "remote-name",
            ("ssh://some.server:/path/to/.geodepot", "some.server"),
            "/path/to/.geodepot",
        ),
    ),
    ids=("empty", "Remote None", "Remote Http", "User None, Remote SSH"),
)
def test_as_config(
    config_dict: dict,
    expected_user_none: str,
    expected_user_name: str,
    expected_remote_none: str,
    expected_remote_name: str,
    expected_remote_url: str,
    expected_remote_path: str,
):
    """Can we decode a configuration JSON object?"""
    config = as_config(config_dict)
    if isinstance(config, dict):
        # In case the config json is empty, it is deserialized into an empty dictionary
        assert config == config_dict
    else:
        if expected_user_none:
            assert config.user is None
        else:
            assert config.user.name == expected_user_name

        if expected_remote_none:
            assert config.remotes is None
        else:
            remote = config.remotes.get(expected_remote_name)
            assert remote.url == expected_remote_url[0]
            if remote.is_ssh:
                assert remote.ssh_host == expected_remote_url[1]
            assert remote.path == expected_remote_path


def test_read_global_config(mock_user_home):
    config = get_global_config()
    assert config.user.name == "Kovács János"


def test_read_local_config_ssh(mock_project_dir):
    """Can we load the configuration from the repository directory?"""
    config = get_local_config()
    remote = config.remotes["remote-name"]
    assert remote.name == "remote-name"
    assert remote.ssh_host == "some.server"
    assert remote.path == "/path/to/.geodepot"
    assert remote.is_ssh is True


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
                remotes={"remote-name": Remote(name="remote-name", url="http://url")}
            ),
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


@pytest.mark.parametrize(
    argnames="url_with_path,url,path,is_ssh",
    argvalues=(
        (
            "ssh://vagrant@192.168.56.5:/srv/geodepot/.geodepot",
            "vagrant@192.168.56.5",
            "/srv/geodepot/.geodepot",
            True,
        ),
        (
            "ssh://192.168.56.5:/srv/geodepot/.geodepot",
            "192.168.56.5",
            "/srv/geodepot/.geodepot",
            True,
        ),
        ("ssh://vagrant@192.168.56.5", "vagrant@192.168.56.5", "", True),
        (
            "https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot",
            "https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot",
            "",
            False,
        ),
        (
            "http://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot",
            "http://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot",
            "",
            False,
        ),
    ),
    ids=("ssh-with-user", "ssh-without-user", "ssh-with-user-no-path", "https", "http"),
)
def test_remote_create(url_with_path, url, path, is_ssh):
    """Can we instantiate a Remote object with the supported protocols and URL/path
    configurations?"""
    remote = Remote(name="myremote", url=url_with_path)
    assert remote.name == "myremote"
    if is_ssh:
        assert remote.is_ssh is True
        assert remote.ssh_host == url
        assert (
            remote.path_index == f"{path}/index.geojson"
            if path != ""
            else "index.geojson"
        )
    else:
        assert remote.is_ssh is False
        assert remote.url == url
        assert remote.path_index == f"{url}/index.geojson"
