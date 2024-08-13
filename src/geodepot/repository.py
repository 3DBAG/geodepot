from dataclasses import dataclass, field
from pathlib import Path
import logging

from osgeo import ogr, gdal
gdal.UseExceptions()
ogr.UseExceptions()

from geodepot.case import Case

logger = logging.getLogger(__name__)


@dataclass(repr=True)
class Index:
    cases: list[Case] = field(default_factory=list)

    def serialize(self, path: Path):
        defn = ogr.FeatureDefn()
        defn.AddFieldDefn(ogr.FieldDefn("case_id", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("case_description", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("case_sha1", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("case_changed_by", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_name", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_sha1", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_format", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_license", ogr.OFTString))
        with ogr.GetDriverByName("GeoJSON").CreateDataSource(path) as ds:
            lyr = ds.CreateLayer("index", geom_type=ogr.wkbPolygon)
            for case in self.cases:
                for data in case.data_files:
                    feat = ogr.Feature(defn)
                    feat["case_id"] = case.id
                    feat["case_description"] = case.description
                    feat["case_sha1"] = case.sha1
                    feat["case_changed_by"] = case.changed_by
                    feat["file_name"] = data.name
                    feat["file_sha1"] = data.sha1
                    feat["file_format"] = data.format
                    feat["file_license"] = data.license
                    ring = ogr.Geometry(ogr.wkbLinearRing)
                    ring.AddPoint(data.bbox[0], data.bbox[2])
                    ring.AddPoint(data.bbox[1], data.bbox[2])
                    ring.AddPoint(data.bbox[1], data.bbox[3])
                    ring.AddPoint(data.bbox[0], data.bbox[3])
                    ring.AddPoint(data.bbox[0], data.bbox[2])
                    poly = ogr.Geometry(ogr.wkbPolygon)
                    poly.AddGeometry(ring)
                    feat.SetGeometry(poly)
                    lyr.CreateFeature(feat)

    def add_case(self, case):
        self.cases.append(case)

    def to_json_str(self) -> str:
        return "{}"

    def deserialise(self):
        raise NotImplementedError


@dataclass(repr=True)
class Repository:
    path: Path = field(default_factory=lambda: Path.cwd() / ".geodepot")
    index: Index | None = None

    def init(self, url: str = None):
        if self.path.exists():
            logger.info(f"Geodepot repository already exists at {self.path}")
            return
        if url is not None:
            # need to add url as remote
            raise NotImplementedError
        else:
            self.path.mkdir()
            self.path.joinpath("cases").mkdir()
            self.index = Index()
            self.index.serialize(self.path.joinpath("index.geojson"))
            logger.info(f"Empty geodepot repository created at {self.path}")