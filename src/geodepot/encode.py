import dataclasses
import json


class DataClassEncoder(json.JSONEncoder):
    """Dataclass JSON serializer.
    If the dataclass is empty, it is serialized as an empty JSON object, without the
    dataclass members. The alternative is to serialize an empty dataclass with its
    members set to 'null'. In case of the configuration files, an empty local config is
    always created with the repository, and the local config overwrite the global
    config values, thus a 'null' value would overwrite a global value if it is set."""
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return {k: v for k, v in dataclasses.asdict(o).items() if v is not None}
        else:
            return super().default(0)
