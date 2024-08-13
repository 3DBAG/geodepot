import dataclasses
import json
from pathlib import Path
from typing import Self
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

GEODEPOT_CONFIG_GLOBAL = ".geodepotconfig.json"


@dataclass(repr=True, frozen=True)
class User:
    name: str
    email: str

    def as_json_str(self) -> str:
        return json.dumps(self, cls=UserEncoder)


class UserEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        else:
            return super().default(o)


def as_user(dct: dict) -> User | dict:
    if "name" in dct and "email" in dct:
        return User(name=dct["name"], email=dct["email"])
    else:
        return dct


@dataclass(repr=True, frozen=True)
class Config:
    user: User

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


def as_config(dct: dict) -> Config | dict:
    if "user" in dct:
        return Config(user=as_user(dct["user"]))
    else:
        return dct


class ConfigEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        else:
            return super().default(0)


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


config_encoder = multiencoder_factory(ConfigEncoder, UserEncoder)


def get_global_config_path() -> Path | None:
    if (global_config_path := Path.home() / GEODEPOT_CONFIG_GLOBAL).exists():
        return global_config_path


def get_global_config() -> Config | None:
    if (global_config_path := get_global_config_path()) is not None:
        return Config.read_from_file(global_config_path)
