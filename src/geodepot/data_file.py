import json
from enum import Enum, auto
import hashlib
from pathlib import Path

import pdal
from osgeo import ogr, gdal

gdal.UseExceptions()
ogr.UseExceptions()

pdal_filter_stats = {"type": "filters.stats", "dimensions": "X,Y"}


class Drivers(Enum):
    CITYJSON = auto()
    GDAL = auto()
    OGR = auto()
    PDAL = auto()


class DataFile:
    """A data file in the repository."""

    def __init__(self, path: Path, data_license: str = None):
        self.name = path.name
        self.license = data_license
        self.sha1 = self.__compute_sha1(path)
        self.driver, self.format = self.__infer_format(path)
        self.bbox = self.__compute_bbox(path)

    @staticmethod
    def __compute_sha1(path: Path) -> str:
        with path.open("rb") as f:
            return hashlib.file_digest(f, "sha1").hexdigest()

    @staticmethod
    def __infer_format(path: Path) -> tuple[Drivers, str]:
        """Try opening the file with different readers to determine its format."""
        if is_cityjson(path.suffixes):
            return Drivers.CITYJSON, "cityjson"
        elif is_cityjson_seq(path.suffixes):
            return Drivers.CITYJSON, "cityjsonseq"
        if (ogr_format := try_ogr(path)) is not None:
            return Drivers.OGR, ogr_format
        if (gdal_format := try_gdal(path)) is not None:
            return Drivers.GDAL, gdal_format
        if (pdal_format := try_pdal(path)) is not None:
            return Drivers.PDAL, pdal_format
        raise ValueError(f"Cannot determine format of {path}")

    def __compute_bbox(self, path: Path) -> tuple[float, float, float, float]:
        if self.driver == Drivers.CITYJSON:
            with path.open() as f:
                cj = json.load(f)
                if "vertices" in cj:
                    t = cj.get(
                        "transform",
                        {"scale": [1.0, 1.0, 1.0], "translate": [0.0, 0.0, 0.0]},
                    )
                    v = cj["vertices"][0]
                    minx = (v[0] * t["scale"][0]) + t["translate"][0]
                    maxx = minx
                    miny = (v[1] * t["scale"][1]) + t["translate"][1]
                    maxy = miny
                    for v in cj["vertices"]:
                        real_x = (v[0] * t["scale"][0]) + t["translate"][0]
                        real_y = (v[1] * t["scale"][1]) + t["translate"][1]
                        if real_x < minx:
                            minx = real_x
                        elif real_x > maxx:
                            maxx = real_x
                        if real_y < miny:
                            miny = real_y
                        elif real_y > maxy:
                            maxy = real_y
                    return minx, maxx, miny, maxy
                else:
                    raise ValueError(
                        f"Cannot compute bounding box for {path}, file does not contain a 'vertices' member"
                    )
        elif self.driver == Drivers.GDAL:
            raise NotImplementedError
        elif self.driver == Drivers.OGR:
            with ogr.Open(path) as ogr_dataset:
                lyr = ogr_dataset.GetLayer(0)
                return lyr.GetExtent(force=True)
                # lyr.GetSpatialRef().ExportToWkt()
        elif self.driver == Drivers.PDAL:
            pdal_pipeline = pdal.Pipeline(json.dumps([str(path), pdal_filter_stats]))
            pdal_pipeline.execute()
            stats = pdal_pipeline.metadata["metadata"]["filters.stats"]["statistic"]
            x_max = stats[0]["maximum"]
            x_min = stats[0]["minimum"]
            y_max = stats[1]["maximum"]
            y_min = stats[1]["minimum"]
            # pdal_pipeline.srswkt2
            return x_min, x_max, y_min, y_max
        else:
            raise ValueError(f"Unknown driver: {self.driver}")


def try_pdal(path: Path) -> str | None:
    try:
        reader = pdal.Reader(path)
        if reader.type is not None and reader.type != "":
            return reader.type.replace("readers.", "")
        else:
            return None
    except RuntimeError:
        return None


def try_ogr(path: Path) -> str | None:
    try:
        with ogr.Open(path) as ogr_dataset:
            return ogr_dataset.GetDriver().GetName()
    except RuntimeError:
        return None


def try_gdal(path: Path) -> str | None:
    try:
        with gdal.Open(path) as gdal_dataset:
            return gdal_dataset.GetDriver().GetName()
    except RuntimeError:
        return None


def is_cityjson(suffixes: list[str]) -> bool:
    if isinstance(suffixes, list):
        a = set(s.lower() for s in suffixes) == {".city", ".json"}
        b = set(s.lower() for s in suffixes) == {".cityjson"}
        return a or b
    else:
        raise ValueError("suffixes must be list")


def is_cityjson_seq(suffixes: list[str]) -> bool:
    if isinstance(suffixes, list):
        a = set(s.lower() for s in suffixes) == {".city", ".jsonl"}
        b = set(s.lower() for s in suffixes) == {".cityjsonl"}
        return a or b
    else:
        raise ValueError("suffixes must be list")
