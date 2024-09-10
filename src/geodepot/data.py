from dataclasses import dataclass
from enum import Enum, auto
from hashlib import file_digest
from json import dumps, load
from logging import getLogger
from pathlib import Path
from typing import NewType, Self

from osgeo.gdal import UseExceptions as gdalUseExceptions
from osgeo.ogr import UseExceptions as ogrUseExceptions

from geodepot import GEODEPOT_INDEX_EPSG
from geodepot.config import User

logger = getLogger(__name__)

gdalUseExceptions()
ogrUseExceptions()

pdal_filter_stats = {"type": "filters.stats", "dimensions": "X,Y"}

DataName = NewType("DataName", str)


class Drivers(Enum):
    CITYJSON = auto()
    GDAL = auto()
    OGR = auto()
    PDAL = auto()

    def __str__(self):
        return self.name


@dataclass(repr=True)
class BBox:
    """Bounding box"""

    minx: float
    miny: float
    maxx: float
    maxy: float

    def __str__(self):
        return f"[{self.minx}, {self.miny}, {self.maxx}, {self.maxy}]"

    def to_ogr_geometry_wkbpolygon(self):
        """Convert to an OGR Geometry that is a wkbPolygon."""
        from osgeo.ogr import Geometry, wkbPolygon, wkbLinearRing

        ring = Geometry(wkbLinearRing)
        ring.AddPoint_2D(self.minx, self.miny)
        ring.AddPoint_2D(self.maxx, self.miny)
        ring.AddPoint_2D(self.maxx, self.maxy)
        ring.AddPoint_2D(self.minx, self.maxy)
        ring.AddPoint_2D(self.minx, self.miny)
        poly = Geometry(wkbPolygon)
        poly.AddGeometry(ring)
        return poly

    def to_wkt(self) -> str:
        """Convert to a WKT Polygon."""
        poly = self.to_ogr_geometry_wkbpolygon()
        return poly.ExportToWkt()


@dataclass(repr=True)
class BBoxSRS:
    """Bounding box in EPSG:3857, original SRS and SRS information"""

    bbox_epsg_3857: BBox | None = None
    bbox_original_srs: BBox | None = None
    srs_wkt: str | None = None


@dataclass(repr=True, init=False, order=True)
class Data:
    """A data item in the repository."""

    name: DataName | None = None
    license: str | None = None
    format: str | None = None
    description: str | None = None
    changed_by: User | None = None
    sha1: str | None = None
    driver: Drivers | None = None
    bbox: BBoxSRS | None = None

    def __init__(
        self,
        path: Path,
        data_license: str = None,
        data_format: str = None,
        description: str = None,
        changed_by: User = None,
        data_name: str | DataName = None,
    ):
        self.name = (
            DataName(data_name) if data_name is not None else DataName(path.name)
        )
        self.license = data_license
        self.format = data_format
        self.description = description
        self.changed_by = changed_by
        self.sha1 = None
        self.driver = None
        self.bbox = None
        if path.is_file():
            self.sha1 = self._compute_sha1(path)
            if data_format is None:
                self.driver, self.format = self._infer_format(path)
                if self.driver is None:
                    logger.error(
                        f"Could not determine the driver for the format {self.format} of {path}"
                    )
                else:
                    self.bbox = self._compute_bbox(path)
            else:
                logger.info(
                    f"Forcing format {data_format} on {path}, won't be able to determine driver and compute the bounding box."
                )

    @staticmethod
    def _compute_sha1(path: Path) -> str:
        with path.open("rb") as f:
            return file_digest(f, "sha1").hexdigest()

    @staticmethod
    def _infer_format(path: Path) -> tuple[Drivers, str]:
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

    def _compute_bbox(self, path: Path) -> BBoxSRS:
        from osgeo.osr import SpatialReference, CreateCoordinateTransformation

        target_epsg = GEODEPOT_INDEX_EPSG
        pseudo_mercator = SpatialReference()
        pseudo_mercator.ImportFromEPSG(target_epsg)
        if self.driver == Drivers.CITYJSON:
            with path.open() as f:
                cj = load(f)
                metadata = cj.get("metadata")
                srs = metadata.get("referenceSystem")
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
                    bbox_srs = BBoxSRS(bbox_original_srs=BBox(minx, maxx, miny, maxy))
                    if srs is not None:
                        # EPSG parsing taken from https://github.com/cityjson/cjio
                        if "opengis.net/def/crs" not in srs or srs.rfind("/") < 0:
                            logger.error(f"Cannot parse EPSG code from {srs} of {path}")
                        else:
                            epsg = int(srs[srs.rfind("/") + 1 :])
                            srs = SpatialReference()
                            srs.ImportFromEPSG(epsg)
                            try:
                                ct = CreateCoordinateTransformation(
                                    srs, pseudo_mercator
                                )
                                bbox_srs.bbox_epsg_3857 = BBox(
                                    *ct.TransformBounds(minx, maxx, miny, maxy, 21)
                                )
                            except Exception as e:
                                logger.error(
                                    f"Could not reproject the bounding box of {path} to EPSG:{target_epsg} with exception: {e}"
                                )
                    return bbox_srs
                else:
                    raise ValueError(
                        f"Cannot compute bounding box for {path}, file does not contain a 'vertices' member"
                    )
        elif self.driver == Drivers.GDAL:
            from osgeo.gdal import OpenEx as gdalOpenEx

            with gdalOpenEx(path) as gdal_dataset:
                bbox_srs = BBoxSRS()
                srs = gdal_dataset.GetSpatialRef()
                geotransform = gdal_dataset.GetGeoTransform(can_return_null=True)
                if geotransform is not None:
                    xmin = geotransform[0]
                    ymax = geotransform[3]
                    xsize = gdal_dataset.RasterXSize
                    ysize = gdal_dataset.RasterYSize
                    xres = abs(geotransform[1])
                    yres = abs(geotransform[5])
                    extent = (xmin, ymax - (ysize * yres), xmin + (xsize * xres), ymax)
                    bbox_srs.bbox_original_srs = BBox(
                        extent[0], extent[1], extent[2], extent[3]
                    )
                else:
                    logger.info(
                        f"Could not find the affine transformation parameters of {path} and could not calculate its extent."
                    )
                if srs is not None and geotransform is not None:
                    bbox_srs.srs_wkt = srs.ExportToWkt()
                    try:
                        ct = CreateCoordinateTransformation(srs, pseudo_mercator)
                        bbox_srs.bbox_epsg_3857 = BBox(
                            *ct.TransformBounds(
                                extent[0], extent[1], extent[2], extent[3], 21
                            )
                        )
                    except Exception as e:
                        logger.error(
                            f"Could not reproject the bounding box of {path} to EPSG:{target_epsg} with exception: {e}"
                        )
                else:
                    logger.info(
                        f"Could not retrieve the SRS of {path} and could not reproject the BBox to EPSG:{target_epsg}. The 'data_extent_original_srs' field contains the extent in original coordinates."
                    )
                return bbox_srs
        elif self.driver == Drivers.OGR:
            from osgeo.ogr import Open as ogrOpen

            with ogrOpen(path) as ogr_dataset:
                lyr = ogr_dataset.GetLayer(0)
                srs = lyr.GetSpatialRef()
                extent = lyr.GetExtent(force=True)
                bbox_srs = BBoxSRS(
                    bbox_original_srs=BBox(extent[0], extent[2], extent[1], extent[3])
                )
                if srs is not None:
                    bbox_srs.srs_wkt = srs.ExportToWkt()
                    try:
                        ct = CreateCoordinateTransformation(srs, pseudo_mercator)
                        bbox_srs.bbox_epsg_3857 = BBox(
                            *ct.TransformBounds(
                                extent[0], extent[2], extent[1], extent[3], 21
                            )
                        )
                    except Exception as e:
                        logger.error(
                            f"Could not reproject the bounding box of {path} to EPSG:{target_epsg} with exception: {e}"
                        )
                else:
                    logger.info(
                        f"Could not retrieve the SRS of {path} and could not reproject the BBox to EPSG:{target_epsg}. The 'data_extent_original_srs' field contains the extent in original coordinates."
                    )
                return bbox_srs
        elif self.driver == Drivers.PDAL:
            from pdal import Pipeline

            pdal_pipeline = Pipeline(dumps([str(path), pdal_filter_stats]))
            pdal_pipeline.execute()
            stats = pdal_pipeline.metadata["metadata"]["filters.stats"]["statistic"]
            bbox = (
                stats[0]["minimum"],
                stats[1]["minimum"],
                stats[0]["maximum"],
                stats[1]["maximum"],
            )
            bbox_srs = BBoxSRS(bbox_original_srs=BBox(*bbox))
            srs_wkt = pdal_pipeline.srswkt2
            if srs_wkt is not None and srs_wkt != "":
                bbox_srs.srs_wkt = srs_wkt
                srs = SpatialReference()
                srs.ImportFromWkt(srs_wkt)
                try:
                    ct = CreateCoordinateTransformation(srs, pseudo_mercator)
                    bbox_srs.bbox_epsg_3857 = BBox(*ct.TransformBounds(*bbox, 21))
                except Exception as e:
                    logger.error(
                        f"Could not reproject the bounding box of {path} to EPSG:{target_epsg} with exception: {e}"
                    )
            else:
                logger.info(
                    f"Could not retrieve the SRS of {path} and could not reproject the BBox to EPSG:{target_epsg}. The 'data_extent_original_srs' field contains the extent in original coordinates."
                )
            return bbox_srs
        else:
            raise ValueError(f"Unknown driver: {self.driver}")

    @classmethod
    def from_ogr_feature(cls, feature) -> Self:
        from osgeo.ogr import CreateGeometryFromWkt

        df = cls.__new__(cls)
        df.name = DataName(feature["data_name"])
        df.sha1 = feature["data_sha1"]
        df.description = feature["data_description"]
        df.format = feature["data_format"]
        df.driver = feature["data_driver"]
        df.changed_by = User.from_pretty(feature["data_changed_by"])
        df.license = feature["data_license"]
        if (gref := feature.GetGeometryRef()) is not None:
            extent = gref.GetEnvelope()
            bbox = BBox(extent[0], extent[2], extent[1], extent[3])
        else:
            bbox = None
        if feature["data_extent_original_srs"] is not None:
            extent_original = CreateGeometryFromWkt(
                feature["data_extent_original_srs"]
            ).GetEnvelope()
            df.bbox = BBoxSRS(
                bbox_epsg_3857=bbox,
                bbox_original_srs=BBox(
                    extent_original[0],
                    extent_original[2],
                    extent_original[1],
                    extent_original[3],
                ),
                srs_wkt=feature["data_srs"],
            )
        else:
            df.bbox = None
        return df

    def to_pretty(self) -> str:
        bbox_wkt = None
        srs_wkt = None
        if (bbox := self.bbox) is not None:
            srs_wkt = bbox.srs_wkt
            if bbox.bbox_original_srs is not None:
                bbox_wkt = bbox.bbox_original_srs.to_wkt()
        output = [
            f"NAME={self.name}",
            f"\nDESCRIPTION={self.description}",
            f"\nformat={self.format}",
            f"driver={self.driver}",
            f"license={self.license}",
            f"sha1={self.sha1}",
            f"changed_by={self.changed_by.to_pretty() if self.changed_by is not None else None}",
            f"extent={bbox_wkt}",
            f"srs={srs_wkt}",
        ]
        return "\n".join(output)


def try_pdal(path: Path) -> str | None:
    from pdal import Reader

    try:
        reader = Reader(path)
        if reader.type is not None and reader.type != "":
            return reader.type.replace("readers.", "")
        else:
            return None
    except RuntimeError:
        return None


def try_ogr(path: Path) -> str | None:
    from osgeo.ogr import Open as ogrOpen

    try:
        with ogrOpen(path) as ogr_dataset:
            return ogr_dataset.GetDriver().GetName()
    except RuntimeError:
        return None


def try_gdal(path: Path) -> str | None:
    from osgeo.gdal import OpenEx as gdalOpenEx

    try:
        with gdalOpenEx(path) as gdal_dataset:
            lname = gdal_dataset.GetDriver().LongName
            return lname if lname is not None else gdal_dataset.GetDriver().ShortName
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
