from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from shutil import copy2, copytree, rmtree
from typing import Self

from osgeo.ogr import (
    UseExceptions,
    GetDriverByName,
    FieldDefn,
    FeatureDefn,
    OFTString,
    OFTInteger64,
    wkbPolygon,
    Feature,
    OGRERR_NONE,
)
from osgeo.osr import SpatialReference

from geodepot.data_file import DataFile

UseExceptions()

from geodepot import GEODEPOT_CONFIG_LOCAL, GEODEPOT_INDEX, GEODEPOT_INDEX_EPSG
from geodepot.case import CaseName, Case, CaseSpec
from geodepot.config import Config, get_current_user

logger = getLogger(__name__)


# to update index: https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#load-data-to-memory
@dataclass(repr=True)
class Index:
    cases: dict[CaseName, Case] = field(default_factory=dict)

    def add_case(self, case: Case):
        self.cases[case.name] = case

    def remove_case(self, case_name: CaseName) -> Case | None:
        return self.cases.pop(case_name, None)

    def serialize(self, path: Path):
        try:
            INDEX_SRS = SpatialReference()
            INDEX_SRS.ImportFromEPSG(GEODEPOT_INDEX_EPSG)
            INDEX_FIELD_DEFINITIONS = (
                FieldDefn("fid", OFTInteger64),
                FieldDefn("case_name", OFTString),
                FieldDefn("case_sha1", OFTString),
                FieldDefn("case_description", OFTString),
                FieldDefn("file_name", OFTString),
                FieldDefn("file_sha1", OFTString),
                FieldDefn("file_description", OFTString),
                FieldDefn("file_format", OFTString),
                FieldDefn("file_changed_by", OFTString),
                FieldDefn("file_license", OFTString),
                FieldDefn("file_srs", OFTString),
                FieldDefn("file_extent_original_srs", OFTString),
            )
            fid = 0
            # We simple write a new index on serialization
            if path.exists():
                path.exists()
            with GetDriverByName("GeoJSON").CreateDataSource(path) as ds:
                # Layer definition
                lyr = ds.CreateLayer(
                    "index",
                    srs=INDEX_SRS,
                    geom_type=wkbPolygon,
                )
                lyr.CreateFields(INDEX_FIELD_DEFINITIONS)
                # Feature definition
                defn = FeatureDefn()
                for fdef in INDEX_FIELD_DEFINITIONS:
                    defn.AddFieldDefn(fdef)

                for case_name, case in self.cases.items():
                    for data in case.data_files.values():
                        feat = Feature(defn)
                        feat["fid"] = fid
                        feat["case_name"] = case_name
                        feat["case_sha1"] = case.sha1
                        feat["case_description"] = case.description
                        feat["file_name"] = data.name
                        feat["file_sha1"] = data.sha1
                        feat["file_description"] = data.description
                        feat["file_format"] = data.format
                        feat["file_changed_by"] = (
                            data.changed_by.to_pretty()
                            if data.changed_by is not None
                            else None
                        )
                        feat["file_license"] = data.license
                        feat["file_srs"] = data.bbox.srs_wkt
                        feat["file_extent_original_srs"] = (
                            data.bbox.bbox_original_srs.to_wkt()
                        )
                        if data.bbox.bbox_epsg_3857 is not None:
                            feat.SetGeometry(
                                data.bbox.bbox_epsg_3857.to_ogr_geometry_wkbpolygon()
                            )
                        if lyr.CreateFeature(feat) != OGRERR_NONE:
                            logger.error(
                                f"Failed to create OGR Feature on the layer from {data}"
                            )
                        fid += 1
        except Exception as e:
            logger.critical(f"Failed to serialize index with exception {e}")

    @classmethod
    def deserialize(cls, path: Path) -> Self:
        cases_in_index = {}
        try:
            with GetDriverByName("GeoJSON").Open(path) as ds:
                lyr = ds.GetLayer()
                for feat in lyr:
                    case_name = CaseName(feat["case_name"])
                    case = cases_in_index.get(
                        case_name,
                        Case(
                            name=CaseName(feat["case_name"]),
                            sha1=feat["case_sha1"],
                            description=feat["case_description"],
                        ),
                    )
                    df = DataFile.from_ogr_feature(feat)
                    case.add_data_file(df)
                    cases_in_index[case_name] = case
        except Exception as e:
            logger.critical(f"Failed to deserialize index with exception {e}")
        return Index(cases=cases_in_index)


@dataclass(repr=True)
class Repository:
    path: Path = field(default_factory=lambda: Path.cwd() / ".geodepot")
    index: Index | None = None

    @property
    def path_cases(self):
        return self.path / "cases"

    @property
    def path_index(self):
        return self.path / GEODEPOT_INDEX

    @property
    def path_config_local(self):
        return self.path / GEODEPOT_CONFIG_LOCAL

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
            self.index.serialize(self.path_index)
            Config().write_to_file(self.path_config_local)
            logger.info(f"Empty geodepot repository created at {self.path}")

    def load_index(self):
        """Load the index."""
        self.index = Index.deserialize(self.path_index)

    def add(
        self,
        casespec: str,
        pathspec: str | None = None,
        description: str | None = None,
        license: str | None = None,
        format: str | None = None,
        as_data: bool = False,
        yes: bool = True,
    ):
        casespec = CaseSpec.from_str(casespec)
        if not yes:
            raise NotImplementedError
        # Determine if we need to update a case's description or a data's description
        case_description = None
        data_description = None
        if casespec.data_file_name is not None:
            data_description = description
        else:
            case_description = description
        # Get an existing case or create an new if not exists
        if (case := self.get_case(casespec)) is None:
            case = self.init_case(casespec)
        # Update the description of an existing case
        if case_description is not None:
            case.description = case_description
        if pathspec is None:
            # Only update the license or description or format
            if case_description is not None:
                case.description = case_description
                logger.info(f"Updated the description on the case {case.name}")
            if (df := self.get_data_file(casespec)) is not None:
                if data_description is not None:
                    df.description = data_description
                    logger.info(f"Updated the description on the data entry {casespec}")
                if license is not None:
                    df.license = license
                    logger.info(f"Updated the license on the data entry {casespec}")
                if format is not None:
                    df.format = format
                    logger.info(f"Updated the format on the data entry {casespec}")
            else:
                logger.error(
                    f"The case/data {casespec} does not exist in the repository"
                )
                return None
        else:
            # Add/Update the specified data to the case
            data_paths = parse_pathspec(pathspec, as_data=as_data)
            for p in data_paths:
                df = case.add_from_path(
                    p,
                    casespec=casespec,
                    data_license=license,
                    format=format,
                    description=data_description,
                    changed_by=get_current_user(),
                )
                self.copy_data(p, casespec)
                logger.info(f"Added {df.name} to {case.name}")
        self.index.cases[casespec.case_name] = case

    def get_case(self, casespec: CaseSpec) -> Case | None:
        """Retrive an existing case."""
        return self.index.cases.get(casespec.case_name)

    def init_case(self, casespec: CaseSpec) -> Case:
        """Create a new case an return it."""
        case = Case(name=casespec.case_name, description=None)
        self.index.add_case(case)
        self.path_cases.joinpath(casespec.case_name).mkdir()
        return self.get_case(casespec)

    def get_data_file(self, casespec: CaseSpec) -> DataFile | None:
        """Retrive an existing data entry.
        Return None if the data entry does not exist."""
        return self.get_case(casespec).get_data_file(casespec.data_file_name)

    def copy_data(self, path: Path, casespec: CaseSpec):
        """Copies a data entry into the repository."""
        if path.is_file():
            if casespec.data_file_name is not None:
                # Rename the file when copied into the case
                copy2(
                    path,
                    self.path_cases.joinpath(
                        casespec.case_name, casespec.data_file_name
                    ),
                )
            else:
                # Keep the file name
                copy2(path, self.path_cases.joinpath(casespec.case_name, path.name))
        else:
            if casespec.data_file_name is not None:
                # Copying a directory as a single data entry under a new name
                copytree(
                    path,
                    self.path_cases.joinpath(
                        casespec.case_name, casespec.data_file_name
                    ),
                    dirs_exist_ok=True,
                )
            else:
                copytree(
                    path,
                    self.path_cases.joinpath(casespec.case_name, path.name),
                    dirs_exist_ok=True,
                )

    def remove(self, casespec: CaseSpec):
        """Remove an entry from the repository."""
        if casespec.data_file_name is None:
            # Remove the whole case
            if (
                case := self.index.remove_case(case_name=casespec.case_name)
            ) is not None:
                rmtree(self.path_cases.joinpath(casespec.as_path()))
                logger.info(f"Removed {case.name} from the repository")
            else:
                logger.info(f"The case {casespec} does not exist in the repository")
        else:
            if (case := self.get_case(casespec)) is not None:
                df = case.remove_data_file(casespec.data_file_name)
                if df is not None:
                    if (p := self.path_cases.joinpath(casespec.as_path())).is_dir():
                        p.rmdir()
                    else:
                        p.unlink(missing_ok=False)
                        # TODO: I could remove the whole case if there are no more files. Don't forget to remove the case from the index too.
                    logger.info(f"Removed {df.name} from the repository")
                else:
                    logger.info(
                        f"The data entry {casespec} does not exist in the repository"
                    )
            else:
                logger.info(
                    f"The case {casespec.case_name} does not exist in the repository"
                )


def parse_pathspec(pathspec: str, as_data: bool = False) -> list[Path]:
    """Parse a path specifier and return a list of Paths that needs to be added to the
    case.
    :param pathspec: Can be relative or absolute path or a fileglob. Fileglobs cannot be used together with `as_data`.
    :param as_data: Treat a directory as a single file, effectively returning a single path. Only has effect if `pathspec` is a path to a directory.
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
