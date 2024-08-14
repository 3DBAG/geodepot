import dataclasses
import json


class DataClassEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return {k: v for k, v in dataclasses.asdict(o).items() if v is not None}
        else:
            return super().default(0)
