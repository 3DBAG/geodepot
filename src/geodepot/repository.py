from dataclasses import dataclass, field, fields
from enum import Enum, auto
from logging import getLogger
from pathlib import Path
from shutil import copy2, copytree, rmtree
from typing import Self, Any

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

from geodepot import GEODEPOT_CONFIG_LOCAL, GEODEPOT_INDEX, GEODEPOT_INDEX_EPSG
from geodepot.case import CaseName, Case, CaseSpec
from geodepot.config import Config, get_current_user, User
from geodepot.data import Data

UseExceptions()
logger = getLogger(__name__)


class Status(Enum):
    ADD = auto()
    DELETE = auto()
    MODIFY = auto()


@dataclass(repr=True, order=True)
class IndexDiff:
    status: Status
    changed_by_other: User
    casespec_self: CaseSpec | None = None
    casespec_other: CaseSpec | None = None
    member: str | None = None
    value_self: Any = None
    value_other: Any = None


def create_modified_diff(
    casespec: CaseSpec, df_self: Data, df_other: Data, member: str
) -> IndexDiff:
    return IndexDiff(
        casespec_self=casespec,
        casespec_other=casespec,
        status=Status.MODIFY,
        changed_by_other=df_other.changed_by,
        value_self=df_self.__getattribute__(member),
        value_other=df_other.__getattribute__(member),
        member=member,
    )


# to update index: https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#load-data-to-memory
@dataclass(repr=True, order=True)
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
                FieldDefn("data_name", OFTString),
                FieldDefn("data_sha1", OFTString),
                FieldDefn("data_description", OFTString),
                FieldDefn("data_format", OFTString),
                FieldDefn("data_changed_by", OFTString),
                FieldDefn("data_license", OFTString),
                FieldDefn("data_srs", OFTString),
                FieldDefn("data_extent_original_srs", OFTString),
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
                    for data in case.data.values():
                        feat = Feature(defn)
                        feat["fid"] = fid
                        feat["case_name"] = case_name
                        feat["case_sha1"] = case.sha1
                        feat["case_description"] = case.description
                        feat["data_name"] = data.name
                        feat["data_sha1"] = data.sha1
                        feat["data_description"] = data.description
                        feat["data_format"] = data.format
                        feat["data_changed_by"] = (
                            data.changed_by.to_pretty()
                            if data.changed_by is not None
                            else None
                        )
                        feat["data_license"] = data.license
                        feat["data_srs"] = data.bbox.srs_wkt
                        feat["data_extent_original_srs"] = (
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
    def deserialize(cls, path: Path) -> Self | None:
        if not path.exists():
            logger.critical(f"Index path {path} does not exist")
            return None
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
                    df = Data.from_ogr_feature(feat)
                    case.add_data(df)
                    cases_in_index[case_name] = case
        except Exception as e:
            logger.critical(f"Failed to deserialize index with exception {e}")
            return None
        return Index(cases=cases_in_index)

    def diff(self, other: Self) -> list[IndexDiff]:
        """Compare two indices and return the difference."""
        diff_all = []
        if len(self.cases) == 0 and len(other.cases) == 0:
            return diff_all
        # Compare the cases that exist in both
        for case_name, case_self in self.cases.items():
            if (case_other := other.cases.get(case_name, None)) is not None:
                for df_name, df_self in case_self.data.items():
                    casespec = CaseSpec(case_name=case_name, data_name=df_name)
                    df_other = case_other.data.get(df_name, None)
                    if df_other is not None:
                        for member in fields(Data):
                            if member.name not in ("name", "changed_by"):
                                value_self = getattr(df_self, member.name)
                                value_other = getattr(df_other, member.name)
                                if value_self != value_other:
                                    diff_all.append(
                                        IndexDiff(
                                            casespec_self=casespec,
                                            casespec_other=casespec,
                                            status=Status.MODIFY,
                                            changed_by_other=df_other.changed_by,
                                            value_self=value_self,
                                            value_other=value_other,
                                            member=member.name,
                                        )
                                    )
                    else:
                        deleted = True  # TODO check deletions file of remote
                        changed_by = (
                            User("", "") if deleted else df_self.changed_by
                        )  # TODO deletions file of remote
                        diff_all.append(
                            IndexDiff(
                                casespec_self=casespec,
                                casespec_other=None,
                                status=Status.DELETE if deleted else Status.ADD,
                                changed_by_other=changed_by,
                            )
                        )
                diff_other_data = set(case_other.data.keys()).difference(
                    set(case_self.data.keys())
                )
                for df_name in diff_other_data:
                    deleted = True  # TODO check deletions file of local
                    remote_user = User("", "")
                    changed_by = get_current_user() if deleted else remote_user # TODO deletions file of local
                    diff_all.append(
                        IndexDiff(
                            casespec_self=None,
                            casespec_other=CaseSpec(case_name, df_name),
                            status=Status.DELETE if deleted else Status.ADD,
                            changed_by_other=changed_by,
                        )
                    )
            else:
                deleted = True  # TODO check deletions file of remote
                remote_user = User("", "")
                changed_by = remote_user if deleted else get_current_user()  # TODO deletions file of remote
                diff_all.append(
                    IndexDiff(
                        casespec_self=CaseSpec(case_name=case_name),
                        casespec_other=None,
                        status=Status.DELETE if deleted else Status.ADD,
                        changed_by_other=changed_by,
                    )
                )
        diff_other_cases = set(other.cases.keys()).difference(set(self.cases.keys()))
        for case_name in diff_other_cases:
            deleted = True  # TODO check deletions file of local
            remote_user = User("", "")
            changed_by = get_current_user if deleted else remote_user  # TODO deletions file of local
            diff_all.append(
                IndexDiff(
                    casespec_self=None,
                    casespec_other=CaseSpec(case_name=case_name),
                    status=Status.DELETE if deleted else Status.ADD,
                    changed_by_other=changed_by,
                )
            )
        return diff_all

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

    def write_index(self):
        """Serialize the index."""
        self.index.serialize(self.path_index)

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
        self.load_index()
        casespec = CaseSpec.from_str(casespec)
        if not yes:
            raise NotImplementedError
        # Determine if we need to update a case's description or a data's description
        case_description = None
        data_description = None
        if casespec.data_name is not None:
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
            if (df := self.get_data(casespec)) is not None:
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
                df = case.add_from_path(p, casespec=casespec, data_license=license,
                                        data_format=format,
                                        data_description=data_description,
                                        data_changed_by=get_current_user())
                self.copy_data(p, casespec)
                logger.info(f"Added {df.name} to {case.name}")
        self.index.add_case(case)
        self.write_index()
        logger.debug(f"Serialized the index to {self.path_index}")

    def get_case(self, casespec: CaseSpec) -> Case | None:
        """Retrieve an existing case."""
        return self.index.cases.get(casespec.case_name)

    def init_case(self, casespec: CaseSpec) -> Case:
        """Create a new case an return it."""
        case = Case(name=casespec.case_name, description=None)
        self.index.add_case(case)
        self.path_cases.joinpath(casespec.case_name).mkdir()
        return self.get_case(casespec)

    def get_data(self, casespec: CaseSpec) -> Data | None:
        """Retrieve an existing data entry.
        Return None if the data entry does not exist."""
        if (case := self.get_case(casespec)) is not None:
            if casespec.data_name is not None:
                return case.get_data(casespec.data_name)
        logger.info(f"The entry {casespec} does not exist in the repository.")
        return None

    def get_data_path(self, casespec: CaseSpec) -> Path | None:
        """Retrieve the full path to an existing data entry."""
        if (_ := self.get_data(casespec)) is not None:
            return self.path_cases.joinpath(casespec.to_path())
        logger.info(f"The entry {casespec} does not exist in the repository.")
        return None

    def copy_data(self, path: Path, casespec: CaseSpec):
        """Copies a data entry into the repository."""
        if path.is_file():
            if casespec.data_name is not None:
                # Rename the file when copied into the case
                copy2(
                    path,
                    self.path_cases.joinpath(
                        casespec.case_name, casespec.data_name
                    ),
                )
            else:
                # Keep the file name
                copy2(path, self.path_cases.joinpath(casespec.case_name, path.name))
        else:
            if casespec.data_name is not None:
                # Copying a directory as a single data entry under a new name
                copytree(
                    path,
                    self.path_cases.joinpath(
                        casespec.case_name, casespec.data_name
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
        if casespec.data_name is None:
            # Remove the whole case
            if (
                case := self.index.remove_case(case_name=casespec.case_name)
            ) is not None:
                rmtree(self.path_cases.joinpath(casespec.to_path()))
                logger.info(f"Removed {case.name} from the repository")
            else:
                logger.info(f"The case {casespec} does not exist in the repository")
        else:
            if (case := self.get_case(casespec)) is not None:
                df = case.remove_data(casespec.data_name)
                if df is not None:
                    if (p := self.path_cases.joinpath(casespec.to_path())).is_dir():
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
