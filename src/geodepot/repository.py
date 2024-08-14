import logging
from dataclasses import dataclass, field
from pathlib import Path

from osgeo import ogr

ogr.UseExceptions()

from geodepot import GEODEPOT_CONFIG_LOCAL, GEODEPOT_INDEX
from geodepot.case import CaseId, Case, CaseSpec
from geodepot.config import Config, get_current_user

logger = logging.getLogger(__name__)


# to update index: https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#load-data-to-memory
@dataclass(repr=True)
class Index:
    cases: dict[CaseId, Case] = field(default_factory=dict)

    def serialize(self, path: Path):
        defn = ogr.FeatureDefn()
        defn.AddFieldDefn(ogr.FieldDefn("case_id", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("case_description", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("case_sha1", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_name", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_sha1", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_description", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_format", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_changed_by", ogr.OFTString))
        defn.AddFieldDefn(ogr.FieldDefn("file_license", ogr.OFTString))
        with ogr.GetDriverByName("GeoJSON").CreateDataSource(path) as ds:
            lyr = ds.CreateLayer("index", geom_type=ogr.wkbPolygon)
            for case_id, case in self.cases.items():
                for data in case.data_files:
                    feat = ogr.Feature(defn)
                    feat["case_id"] = case_id
                    feat["case_description"] = case.description
                    feat["case_sha1"] = case.sha1
                    feat["file_name"] = data.name
                    feat["file_sha1"] = data.sha1
                    feat["file_description"] = data.description
                    feat["file_format"] = data.format
                    feat["file_changed_by"] = data.changed_by.to_pretty() if data.changed_by is not None else None
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
        self.cases[case.id] = case

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
            self.index.serialize(self.path.joinpath(GEODEPOT_INDEX))
            Config().write_to_file(self.path.joinpath(GEODEPOT_CONFIG_LOCAL))
            logger.info(f"Empty geodepot repository created at {self.path}")

    def add(
        self,
        casespec,
        pathspec: str = None,
        description: str = None,
        license: str = None,
        format: str = None,
        as_data: bool = False,
        yes: bool = True,
    ):
        cs = CaseSpec.from_str(casespec)
        if not yes:
            raise NotImplementedError
        # Determine if we need to update a case's description or a data's description
        case_description = None
        data_description = None
        if cs.data_file_name is not None:
            data_description = description
        else:
            case_description = description
        # Get an existing case or create an new if not exists
        case = self.index.cases.get(
            cs.case_id, Case(id=cs.case_id, description=case_description)
        )
        # Update the description of an existing case
        if case_description is not None:
            case.description = case_description
        # Add/Update the specified data to the case
        data_paths = parse_pathspec(pathspec, as_data=as_data)
        for p in data_paths:
            df = case.add_path(
                p,
                data_license=license,
                format=format,
                description=data_description,
                changed_by=get_current_user(),
            )
            logger.info(f"Added {df.name} to {case.id}")
        self.index.cases[cs.case_id] = case


def parse_pathspec(pathspec: str, as_data: bool = False) -> list[Path]:
    """Parse a path specifier and return a list of Paths that needs to be added to the
    case.
    :param pathspec: Can be relative or absolute path or a fileglob. Fileglobs cannot be used together with `as_data`.
    :param as_data: Treat a directory as a single file. Only has effect if `pathspec` is a path to a directory.
    :return: List of paths.
    """
    if (is_glob := "*" in pathspec) is not True:
        if not Path(pathspec).exists():
            raise FileNotFoundError(pathspec)

    if is_glob:
        if as_data:
            raise ValueError(
                "Cannot use a fileglob as path specifier and 'as_data' at the same time. To add a whole directory as a single data file, provide the full path to the directory and set the '--as-data' option."
            )
        return list(Path(".").glob(pathspec))

    input_path = Path(pathspec).resolve(strict=True)
    if input_path.is_file() or as_data:
        return [
            input_path,
        ]
    else:
        return [
            dirpath / fname
            for dirpath, dirnames, filenames in input_path.walk()
            if len(filenames) > 0
            for fname in filenames
        ]
