from dataclasses import dataclass
from json import dumps, load, loads, JSONEncoder
from logging import getLogger
from pathlib import Path
from typing import Self, NewType

from geodepot import (
    GEODEPOT_CONFIG_GLOBAL,
    GEODEPOT_CONFIG_LOCAL,
    GEODEPOT_INDEX,
    GEODEPOT_CASES,
)
from geodepot.encode import DataClassEncoder
from geodepot.errors import GeodepotInvalidConfiguration

logger = getLogger(__name__)

JSON_INDENT = 2


@dataclass(repr=True)
class User:
    name: str | None = None
    email: str | None = None

    def to_json(self) -> str:
        return dumps(self, cls=DataClassEncoder, indent=JSON_INDENT)

    def to_pretty(self) -> str:
        return f"{self.name} <{self.email}>"

    @classmethod
    def from_pretty(cls, pretty: str) -> Self:
        name, e = pretty.split("<")
        name = name.strip()
        email = e.rstrip(">").strip()
        return cls(name, email)


def as_user(dct: dict) -> User | dict:
    if "name" in dct and "email" in dct:
        return User(name=dct["name"], email=dct["email"])
    else:
        return dct


RemoteName = NewType("RemoteName", str)


@dataclass(repr=True)
class Remote:
    """A remote repository."""
    name: str
    """The name of the remote repository."""
    url: str
    """The URL of the remote repository. If the remote is SSH, then this is the
    SSH connection string without the protocol and the path on the remote
    filesystem. If the remote is HTTP, then this is the URL as provided to the
    initializer."""

    def __post_init__(self):
        #: Set to True if the remote uses SSH/SFTP protocol
        self.is_ssh = False
        #: The path on the remote to the repository. Only set for SSH/SFTP connections.
        self.path = None
        #: The SSH user@host if the protocol is SSH/SFTP
        self.ssh_host = None

        ssh_parts = None
        if self.url.startswith("ssh://"):
            ssh_parts = self.url.removeprefix("ssh://").split(":")
        elif self.url.startswith("sftp://"):
            ssh_parts = self.url.removeprefix("sftp://").split(":")
        if ssh_parts is not None:
            if len(ssh_parts) == 2:
                self.ssh_host = ssh_parts[0]
                self.path = ssh_parts[1]
            elif len(ssh_parts) == 1:
                self.ssh_host = ssh_parts[0]
                logger.error(
                    f"Expected a remote URL in the form of ssh[sftp]://<url>:<path>, but did not find :<path> in {self.url}."
                )
            else:
                raise GeodepotInvalidConfiguration(
                    f"Expected a remote URL in the form of ssh[sftp]://<url>:<path>, but found {self.url}."
                )
            self.is_ssh = True
            if self.ssh_host is None:
                raise ValueError(f"Could not set Remote ssh_host from {self.url}")

    def __str__(self):
        return f"{self.name} {self.url}"

    @property
    def path_index(self):
        """Path to the remote index file. If the remote is SSH, then this is the path
        on the remote filesystem. If the remote is HTTP, then this is the URL with the
        index file name."""
        if self.is_ssh:
            # In case of SSH, we need the path to the index on the remote filesystem
            return (
                "/".join([self.path, GEODEPOT_INDEX])
                if self.path is not None
                else GEODEPOT_INDEX
            )
        else:
            return "/".join([self.url, GEODEPOT_INDEX])

    @property
    def path_cases(self):
        """Path to the remote cases directory. If the remote is SSH, then this is the
        path on the remote filesystem. If the remote is HTTP, then this is the URL with
        the cases directory name."""
        if self.is_ssh:
            # In case of SSH, we need the path to the index on the remote filesystem
            return (
                "/".join([self.path, GEODEPOT_CASES])
                if self.path is not None
                else GEODEPOT_CASES
            )
        else:
            return "/".join([self.url, GEODEPOT_CASES])

    def to_json(self) -> str:
        """Serialize the remote to a JSON string."""
        return dumps(self, cls=DataClassEncoder, indent=JSON_INDENT)


def as_remote(dct: dict) -> Remote | dict:
    if "name" in dct and "url" in dct:
        return Remote(name=dct["name"], url=dct["url"])
    else:
        return dct


@dataclass(repr=True)
class Config:
    user: User | None = None
    remotes: dict[str, Remote] | None = None

    @classmethod
    def load(cls, path: Path) -> Self:
        logger.debug(f"Reading config from file: {path}")
        with path.open() as f:
            c = load(f, object_hook=as_config)
            # An empty config is serialized as an empty JSON object '{}', so the
            # deserializer 'as_config' will return a dict and not an empty Config
            # instance.
            return c if not isinstance(c, dict) else Config(user=User(), remotes=dict())

    def write(self, path: Path) -> None:
        logger.debug(f"Writing config to file: {path}")
        path.write_text(self.to_json())

    @classmethod
    def from_json(cls, json_str) -> Self:
        return loads(json_str, object_hook=as_config)

    def to_json(self) -> str:
        return dumps(self, cls=config_encoder, indent=JSON_INDENT)

    def update(self, other: Self):
        """Updates the values of self with the values from another Config instance."""
        if other.user is not None:
            self.user = other.user
        if other.remotes is not None:
            self.remotes = other.remotes

    def add_remote(self, name: str, url: str):
        if self.remotes is None:
            self.remotes = {name: Remote(name=name, url=url)}
        else:
            self.remotes[name] = Remote(name=name, url=url)

    def remove_remote(self, name: str):
        del self.remotes[name]

    def to_pretty_lines(self) -> list[str]:
        """Format the configuration values to a list of pretty formatted strings."""
        pretty_strings = []
        if self.user is not None:
            if self.user.name is not None:
                pretty_strings.append(f"user.name={self.user.name}")
            if self.user.email is not None:
                pretty_strings.append(f"user.email={self.user.email}")
        if self.remotes is not None:
            for name in self.remotes:
                if self.remotes[name].url is not None:
                    pretty_strings.append(f"remote.{name}.url={self.remotes[name].url}")
        return pretty_strings


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
        remotes = {
            remote_name: as_remote({"name": remote_name, **remote})
            for remote_name, remote in rmt.items()
        }
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
        return Config.load(global_config_path)


def get_local_config_path() -> Path | None:
    if (local_config_path := Path.cwd() / ".geodepot" / GEODEPOT_CONFIG_LOCAL).exists():
        return local_config_path


def get_local_config(path: Path | None = None) -> Config | None:
    if path is None:
        if (local_config_path := get_local_config_path()) is not None:
            return Config.load(local_config_path)
    else:
        return Config.load(path)


def get_config(local_config: Path | None = None) -> Config:
    """Load the Geoflow configuration.

    The local configuration is merged into the global configuration, so that local
    values overwrite global values.
    """
    config = get_global_config()
    local_config = get_local_config(path=local_config)
    if config is None and local_config is None:
        logger.error(
            "Could not load the global nor a local configuration, using an empty config"
        )
        return Config()
    config = config if config is not None else Config()
    local_config = local_config if local_config is not None else Config()
    config.update(local_config)
    return config


def get_current_user() -> User | None:
    config = get_config()
    return config.user


def configure(
    key: str, value: str | None = None, global_config: bool = False
) -> str | None:
    """Get or set configuration values."""
    config = get_global_config() if global_config else get_local_config()
    section, variable = key.split(".", 1)
    try:
        sec_val = getattr(config, section)
        var_val = getattr(sec_val, variable)
    except AttributeError:
        logger.error(f"Invalid configuration key: {key}")
        return None
    if value is None:
        return var_val
    else:
        setattr(sec_val, variable, value)
        logger.debug(f"Set {key} to {value} (global={global_config})")
    config_path = get_global_config_path() if global_config else get_local_config_path()
    config.write(config_path)


def config_list() -> list[str]:
    output = []
    config_global = get_global_config()
    config_local = get_local_config()
    if config_global is not None:
        for line in config_global.to_pretty_lines():
            output.append(f"[global] {line}")
    if config_local is not None:
        for line in config_local.to_pretty_lines():
            output.append(f"[local] {line}")
    return output


def remote_list() -> list[str]:
    output = []
    config = get_config()
    if config is not None:
        for k, v in config.remotes.items():
            output.append(f"{k} {v.url}")
    return output


def remote_add(name: str, url: str):
    config = get_local_config()
    config.add_remote(name, url)
    config.write(get_local_config_path())


def remote_remove(name: str):
    config = get_local_config()
    config.remove_remote(name)
    config.write(get_local_config_path())
