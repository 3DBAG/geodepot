import json
from pathlib import Path
from typing import Self
import os
import logging

logger = logging.getLogger(__name__)

USER_CONFIG_FILE = "user.json"
GEODEPOT_CONFIG_ENV_VAR = "GEODEPOT_CONFIG_FILE"
GEODEPOT_SYSTEM_CONFIG_DIR = ".geodepot"


def get_system_geodepot_dir() -> Path:
    return Path(os.getenv(GEODEPOT_CONFIG_ENV_VAR, Path.home() / GEODEPOT_SYSTEM_CONFIG_DIR))


class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    @classmethod
    def read_system_config(cls) -> Self:
        """Deserialize the geodepot user from system-wide config file."""
        geodepot_dir = get_system_geodepot_dir()
        user_file = geodepot_dir.joinpath(USER_CONFIG_FILE)
        logger.debug(f"Reading user from config: {user_file}")
        try:
            with user_file.open("r") as f:
                try:
                    return json.load(f, object_hook=as_user)
                except json.JSONDecodeError as e:
                    logger.error(f"Cannot decode user config file: {e}")
                    return cls("none", "none")
        except FileNotFoundError as e:
            logger.error(f"Cannot find user config file: {e}")
            raise e

    def write_system_config(self):
        """Write the user to the system-wide config file."""
        geodepot_dir = get_system_geodepot_dir()
        user_file = geodepot_dir.joinpath(USER_CONFIG_FILE)
        with user_file.open("w") as f:
            logger.debug(f"Writing user to config: {user_file}")
            json.dump(self, f, cls=UserEncoder)


class UserEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, User):
            return o.__dict__
        else:
            return super().default(o)


def as_user(dct: dict) -> User:
    return User(dct["name"], dct["email"])
