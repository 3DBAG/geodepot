from dataclasses import is_dataclass, asdict
from json import JSONEncoder
from logging import getLogger

logger = getLogger(__name__)


class DataClassEncoder(JSONEncoder):
    """Dataclass JSON serializer.
    If the dataclass is empty, it is serialized as an empty JSON object, without the
    dataclass members. The alternative is to serialize an empty dataclass with its
    members set to 'null'. In case of the configuration files, an empty local config is
    always created with the repository, and the local config overwrite the global
    config values, thus a 'null' value would overwrite a global value if it is set."""

    def default(self, o):
        if is_dataclass(o):
            payload = {k: v for k, v in asdict(o).items() if v is not None}
            logger.debug(
                "Encoding dataclass %s with %d populated field(s)",
                type(o).__name__,
                len(payload),
            )
            return payload
        else:
            logger.debug("Delegating JSON encoding for %s", type(o).__name__)
            return super().default(o)
