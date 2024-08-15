from dataclasses import dataclass
from json import dumps, load, JSONEncoder
from logging import getLogger
from pathlib import Path
from typing import Self

from geodepot import GEODEPOT_CONFIG_GLOBAL, GEODEPOT_CONFIG_LOCAL
from geodepot.encode import DataClassEncoder

logger = getLogger(__name__)

JSON_INDENT = 2


@dataclass(repr=True)
class User:
    name: str
    email: str

    def to_json(self) -> str:
        return dumps(self, cls=DataClassEncoder, indent=JSON_INDENT)

    def to_pretty(self) -> str:
        return f"{self.name} <{self.email}>"


def as_user(dct: dict) -> User | dict:
    if "name" in dct and "email" in dct:
        return User(name=dct["name"], email=dct["email"])
    else:
        return dct


@dataclass(repr=True)
class Remote:
    name: str
    url: str

    def to_json(self) -> str:
        return dumps(self, cls=DataClassEncoder, indent=JSON_INDENT)


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
            c = load(f, object_hook=as_config)
            # An empty config is serialized as an empty JSON object '{}', so the
            # deserializer 'as_config' will return a dict and not an empty Config
            # instance.
            return c if not isinstance(c, dict) else cls()

    def write_to_file(self, path: Path) -> None:
        logger.debug(f"Writing config to file: {path}")
        path.write_text(self.to_json())

    def to_json(self) -> str:
        return dumps(self, cls=config_encoder, indent=JSON_INDENT)

    def update(self, other: Self):
        """Updates the values of self with the values from another Config instance."""
        if other.user is not None:
            self.user = other.user
        if other.remotes is not None:
            self.remotes = other.remotes


def as_config(dct: dict) -> Config | dict:
    """Deserialize a dict as a Config instance.
    If the input dict does not contain the expected members of Config
    (e.g. it is empty), it will return an empty dict and not an empty Config
    instance. This behaviour is required for the deserialization of nested objects.
    """
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
    """Required when using multiple JSONEncoders and/or nested dataclasses.
    Ref.: https://stackoverflow.com/a/76931520/3717824
    """

    class MultipleJsonEncoders(JSONEncoder):
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
    if config is None and local_config is None:
        logger.error("Could not load the global nor a local configuration, using an empty config")
        return Config()
    config = config if config is not None else Config()
    local_config = local_config if local_config is not None else Config()
    config.update(local_config)
    return config


def get_current_user() -> User:
    config = get_config()
    return config.user
