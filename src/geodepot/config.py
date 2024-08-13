import dataclasses
import json
from pathlib import Path
from typing import Self
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

GEODEPOT_CONFIG_GLOBAL = ".geodepotconfig.json"
GEODEPOT_CONFIG_LOCAL = "config.json"


class DataClassEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        else:
            return super().default(0)


@dataclass(repr=True)
class User:
    name: str
    email: str

    def as_json_str(self) -> str:
        return json.dumps(self, cls=DataClassEncoder)


def as_user(dct: dict) -> User | dict:
    if "name" in dct and "email" in dct:
        return User(name=dct["name"], email=dct["email"])
    else:
        return dct


@dataclass(repr=True)
class Remote:
    name: str
    url: str

    def as_json_str(self) -> str:
        return json.dumps(self, cls=DataClassEncoder)


def as_remote(dct: dict) -> Remote | dict:
    if "name" in dct and "url" in dct:
        return Remote(name=dct["name"], url=dct["url"])
    else:
        return dct


@dataclass(repr=True)
class Config:
    user: User | None = None
    remotes: list[Remote] | None = None

    @classmethod
    def read_from_file(cls, path: Path) -> Self:
        logger.debug(f"Reading config from file: {path}")
        with path.open() as f:
            return json.load(f, object_hook=as_config)

    def write_to_file(self, path: Path) -> None:
        logger.debug(f"Writing config to file: {path}")
        with path.open("w") as f:
            json.dump(self, f, cls=config_encoder)

    def as_json_str(self) -> str:
        return json.dumps(self, cls=config_encoder)

    def update(self, other: Self):
        """Updates the values of self with the values from another Config instance."""
        if other.user is not None:
            self.user = other.user
        if other.remotes is not None:
            self.remotes = other.remotes


def as_config(dct: dict) -> Config | dict:
    user = None
    remotes = None
    if (usr := dct.get("user")) is not None:
        user = as_user(usr)
    if (rmt := dct.get("remotes")) is not None:
        remotes = [
            as_remote({"name": remote_name, **remote})
            for remote_name, remote in rmt.items()
        ]
    if user is None and remotes is None:
        return dct
    else:
        return Config(user=user, remotes=remotes)


def multiencoder_factory(*encoders):
    """Required when using multiple JSONEncoders.
    https://stackoverflow.com/a/76931520/3717824
    """

    class MultipleJsonEncoders(json.JSONEncoder):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.encoders = [encoder(*args, **kwargs) for encoder in encoders]

        def default(self, o):
            for encoder in self.encoders:
                try:
                    return encoder.default(o)
                except TypeError:
                    pass
            return super().default(o)

    return MultipleJsonEncoders


# config_encoder = multiencoder_factory(ConfigEncoder, UserEncoder, ...)
config_encoder = multiencoder_factory(DataClassEncoder)


def get_global_config_path() -> Path | None:
    if (global_config_path := Path.home() / GEODEPOT_CONFIG_GLOBAL).exists():
        return global_config_path


def get_global_config() -> Config | None:
    if (global_config_path := get_global_config_path()) is not None:
        return Config.read_from_file(global_config_path)


def get_local_config_path() -> Path | None:
    if (local_config_path := Path.cwd() / ".geodepot" / GEODEPOT_CONFIG_LOCAL).exists():
        return local_config_path


def get_local_config() -> Config | None:
    if (local_config_path := get_local_config_path()) is not None:
        return Config.read_from_file(local_config_path)


def get_config() -> Config:
    config = get_global_config()
    local_config = get_local_config()
    config.update(local_config)
    return config
