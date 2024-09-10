import json

from geodepot.config import Config, User, config_encoder, Remote, JSON_INDENT
from geodepot.encode import DataClassEncoder


def test_encode_dataclass_empty():
    """Can we encode an empty dataclass as an empty JSON object?"""
    config = Config()
    assert config.user is None
    assert config.remotes is None
    json_str = json.dumps(config, cls=DataClassEncoder)
    assert json_str == "{}"


def test_encode_with_single_member():
    """Can we encode a dataclass that has another dataclass as a member?"""
    config = Config(
        user=User(
            name="<NAME>",
            email="<EMAIL>",
        )
    )
    json_str = json.dumps(config, cls=DataClassEncoder)
    assert json_str == '{"user": {"name": "<NAME>", "email": "<EMAIL>"}}'


def test_encode_remote():
    """Can we encode a Remote?"""
    remote = Remote(name="origin", url="ssh://user@server.com:/path/to/.geodepot")
    json_str = json.dumps(remote, cls=DataClassEncoder)
    expected = {
        "name": "origin",
        "url": "ssh://user@server.com:/path/to/.geodepot",
    }
    assert json.loads(json_str) == expected


def test_encode_with_multiple_members():
    """Can we encode a dataclass that has several members?"""
    config = Config(
        user=User(
            name="<NAME>",
            email="<EMAIL>",
        ),
        remotes={
            "origin": Remote(
                name="origin", url="ssh://user@server.com:/path/to/.geodepot"
            ),
            "remote-1": Remote(name="remote-1", url="http://example.com/.geodepot"),
        },
    )
    json_str = json.dumps(config, cls=config_encoder, indent=JSON_INDENT)
    expected = {
        "user": {"name": "<NAME>", "email": "<EMAIL>"},
        "remotes": {
            "origin": {
                "name": "origin",
                "url": "ssh://user@server.com:/path/to/.geodepot",
            },
            "remote-1": {
                "name": "remote-1",
                "url": "http://example.com/.geodepot",
            },
        },
    }
    assert json.loads(json_str) == expected
