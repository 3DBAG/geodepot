import json

from geodepot.config import Config, User
from geodepot.encode import DataClassEncoder


def test_encode_dataclass_empty():
    """Can we encode an empty dataclass as an empty JSON object?"""
    config = Config()
    assert config.user is None
    assert config.remotes is None
    json_str = json.dumps(config, cls=DataClassEncoder)
    assert json_str == "{}"


def test_encode_with_member():
    """Can we encode a dataclass that has another dataclass as a member?"""
    config = Config(
        user=User(
            name="<NAME>",
            email="<EMAIL>",
        )
    )
    json_str = json.dumps(config, cls=DataClassEncoder)
    assert json_str == '{"user": {"name": "<NAME>", "email": "<EMAIL>"}}'
