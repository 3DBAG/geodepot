from dataclasses import dataclass, field, fields
from enum import Enum, auto
from itertools import groupby
from logging import getLogger
from pathlib import Path
from shutil import copy2, copytree, rmtree
from tarfile import TarFile
from typing import Self, Any
from urllib.parse import urlparse

from osgeo.ogr import UseExceptions

from geodepot import (
    GEODEPOT_CONFIG_LOCAL,
    GEODEPOT_INDEX,
    GEODEPOT_INDEX_EPSG,
    GEODEPOT_CASES,
)
from geodepot.case import CaseName, Case, CaseSpec
from geodepot.config import (
    Config,
    get_current_user,
    User,
    get_config,
    Remote,
    RemoteName,
)
from geodepot.data import Data
from geodepot.errors import (
    GeodepotRuntimeError,
    GeodepotInvalidRepository,
    GeodepotInvalidConfiguration,
)

UseExceptions()
logger = getLogger(__name__)


class Status(Enum):
    ADD_OR_DELETE = auto()
    ADD = auto()
    DELETE = auto()
    MODIFY = auto()


@dataclass(repr=True, order=True)
class IndexDiff:
    status: Status
    changed_by_other: User | None = None
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


def format_indexdiffs(diff_all: list[IndexDiff], push: bool = True) -> str:
    sign_local = "+" if push else "-"
    sign_remote = "-" if push else "+"

    def l_casespec(cs):
        return cs.casespec_self, cs.casespec_other, cs.status

    diff_all_sorted = sorted(diff_all, key=l_casespec)
    all_changes = []
    currentuser = get_current_user()
    for k, g in groupby(diff_all_sorted, key=l_casespec):
        changes = []
        # Add the case/data header
        indexdiff = next(g)

        changes.append(
            f"{sign_local * 3} local/{indexdiff.casespec_self}    ({currentuser.to_pretty() if currentuser else None})\n{sign_remote * 3} remote/{indexdiff.casespec_other}    ({indexdiff.changed_by_other.to_pretty() if indexdiff.changed_by_other else None})"
        )
        if indexdiff.status == Status.MODIFY:
            changes.append(
                f"{sign_local}{indexdiff.member}={indexdiff.value_self}\n{sign_remote}{indexdiff.member}={indexdiff.value_other}"
            )
        # Report the modified values
        for indexdiff in g:
            if indexdiff.status == Status.MODIFY:
                if indexdiff.member.startswith("bbox"):
                    wkt_self = (
                        None
                        if indexdiff.value_self is None
                        else indexdiff.value_self.to_wkt()
                    )
                    wkt_other = (
                        None
                        if indexdiff.value_other is None
                        else indexdiff.value_other.to_wkt()
                    )
                    changes.append(
                        f"{sign_local}{indexdiff.member}={indexdiff.value_self}\n{sign_remote}{indexdiff.member}={indexdiff.value_other}\n{sign_local}{indexdiff.member} (WKT)={wkt_self}\n{sign_remote}{indexdiff.member} (WKT)={wkt_other}"
                    )
                else:
                    changes.append(
                        f"{sign_local}{indexdiff.member}={indexdiff.value_self}\n{sign_remote}{indexdiff.member}={indexdiff.value_other}"
                    )
        all_changes.append("\n\n".join(changes))
    return "\n\n".join(all_changes)


# to update index: https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#load-data-to-memory
@dataclass(repr=True, order=True)
class Index:
    cases: dict[CaseName, Case] = field(default_factory=dict)

    def add_case(self, case: Case):
        self.cases[case.name] = case

    def remove_case(self, case_name: CaseName) -> Case | None:
        return self.cases.pop(case_name, None)

    def write(self, path: Path):
        from osgeo.ogr import (
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
                        if data.bbox is not None:
                            feat["data_srs"] = data.bbox.srs_wkt
                            if data.bbox.bbox_original_srs is not None:
                                feat["data_extent_original_srs"] = (
                                    data.bbox.bbox_original_srs.to_wkt()
                                )
                            if data.bbox.bbox_epsg_3857 is not None:
                                feat.SetGeometry(
                                    data.bbox.bbox_epsg_3857.to_ogr_geometry_wkbpolygon()
                                )
                        else:
                            feat["data_srs"] = None
                            feat["data_extent_original_srs"] = None
                        if lyr.CreateFeature(feat) != OGRERR_NONE:
                            logger.error(
                                f"Failed to create OGR Feature on the layer from {data}"
                            )
                        fid += 1
        except Exception as e:
            logger.critical(
                f"Failed to serialize index with exception '{e}', repository is probably in an invalid state."
            )

    @classmethod
    def load(cls, path: Path | str) -> Self | None:
        """If 'path' is string, it is expected to be a URL with HTTP protocol."""
        if isinstance(path, Path):
            if not path.exists():
                logger.critical(f"Index path {path} does not exist")
                return None
        from osgeo.ogr import GetDriverByName

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
            logger.critical(f"Failed to deserialize index with exception '{e}'")
            return None
        return Index(cases=cases_in_index)

    def diff(self, other: Self) -> list[IndexDiff]:
        """Compare the 'other' index to 'self'.
        The difference is not symmetrical, and additions and deletions are determined
        with respect to 'self'.
        The IndexDiff.status answers the question, "What operation does the 'other' do to 'self'?".
        """
        diff_all = []
        if len(self.cases) == 0 and len(other.cases) == 0:
            return diff_all
        # Compare the cases that exist in both
        for case_name, case_self in self.cases.items():
            if (case_other := other.cases.get(case_name, None)) is not None:
                for data_name, data_self in case_self.data.items():
                    casespec = CaseSpec(case_name=case_name, data_name=data_name)
                    data_other = case_other.data.get(data_name, None)
                    if data_other is not None:
                        for member in fields(Data):
                            if member.name not in ("name", "changed_by"):
                                member_name = member.name
                                value_self = getattr(data_self, member.name)
                                value_other = getattr(data_other, member.name)
                                if value_self != value_other:
                                    # Nasty piece this complex BBoxSRS type...
                                    if member.name == "bbox":
                                        if value_self.srs_wkt != value_other.srs_wkt:
                                            member_name = "srs"
                                            value_self = value_self.srs_wkt
                                            value_other = value_other.srs_wkt
                                        elif (
                                            value_self.bbox_original_srs
                                            != value_other.bbox_original_srs
                                        ):
                                            member_name = "bbox_original_srs"
                                            value_self = value_self.bbox_original_srs
                                            value_other = value_other.bbox_original_srs
                                        elif (
                                            value_self.bbox_epsg_3857
                                            != value_other.bbox_epsg_3857
                                        ):
                                            member_name = "bbox_epsg_3857"
                                            value_self = value_self.bbox_epsg_3857
                                            value_other = value_other.bbox_epsg_3857
                                    diff_all.append(
                                        IndexDiff(
                                            casespec_self=casespec,
                                            casespec_other=casespec,
                                            status=Status.MODIFY,
                                            changed_by_other=data_other.changed_by,
                                            value_self=value_self,
                                            value_other=value_other,
                                            member=member_name,
                                        )
                                    )
                    else:
                        diff_all.append(
                            IndexDiff(
                                casespec_self=casespec,
                                casespec_other=None,
                                status=Status.DELETE,
                                changed_by_other=case_other.changed_by,
                            )
                        )
                diff_other_data = set(case_other.data.keys()).difference(
                    set(case_self.data.keys())
                )
                for data_name in diff_other_data:
                    diff_all.append(
                        IndexDiff(
                            casespec_self=None,
                            casespec_other=CaseSpec(case_name, data_name),
                            status=Status.ADD,
                            changed_by_other=case_other.get_data(data_name).changed_by,
                        )
                    )
                # Check if any of the case attributes have changed
                if case_self.description != case_other.description:
                    diff_all.append(
                        IndexDiff(
                            casespec_self=CaseSpec(case_name=case_name),
                            casespec_other=CaseSpec(case_name=case_name),
                            status=Status.MODIFY,
                            changed_by_other=case_other.changed_by,
                            member="description",
                            value_self=case_self.description,
                            value_other=case_other.description,
                        )
                    )
            else:
                # The case doesn't exist in the other index, not much that we can report
                diff_all.append(
                    IndexDiff(
                        casespec_self=CaseSpec(case_name=case_name),
                        casespec_other=None,
                        status=Status.DELETE,
                        changed_by_other=None,
                    )
                )
        diff_other_cases = set(other.cases.keys()).difference(set(self.cases.keys()))
        for case_name in diff_other_cases:
            # The other has a case that self does not
            diff_all.append(
                IndexDiff(
                    casespec_self=None,
                    casespec_other=CaseSpec(case_name=case_name),
                    status=Status.ADD,
                    changed_by_other=other.cases.get(case_name).changed_by,
                )
            )
        return diff_all


def is_url(path: str) -> bool:
    return (
        path.startswith("http")
        or path.startswith("https")
        or path.startswith("ftp")
        or path.startswith("sftp")
        or path.startswith("ssh")
    )


@dataclass(repr=True, init=False)
class Repository:
    path: Path = field(default_factory=lambda: Path.cwd() / ".geodepot")
    index: Index | None = None
    index_remote: Index | None = None
    config: Config | None = None

    @property
    def path_cases(self):
        return self.path / GEODEPOT_CASES

    @property
    def path_index(self):
        return self.path / GEODEPOT_INDEX

    @property
    def path_config_local(self):
        return self.path / GEODEPOT_CONFIG_LOCAL

    @property
    def cases(self):
        return self.index.cases

    def __init__(self, path: str | None = None, create: bool = False):
        if path is None:
            # We are in the current working directory
            path_local = Path.cwd() / ".geodepot"
            # Get existing repository
            if path_local.exists():
                self._load_from_path(path_local)
            elif create:
                # Create new repository
                self._new_at_path(path=path_local)
            else:
                raise GeodepotInvalidRepository(
                    f"Not a Geodepot repository ({path_local})."
                )
        elif isinstance(path, str):
            if is_url(path):
                if create:
                    raise GeodepotRuntimeError(
                        "Geodepot does not support creating remote repositories (cannot set 'path' to a URL and 'create=True')."
                    )
                from requests import get as requests_get

                path_local = Path.cwd() / ".geodepot"
                if path_local.is_dir():
                    raise GeodepotRuntimeError(
                        f"Geodepot repository already exists at {path_local}, use the 'pull' command to update the local repository with the remote contents."
                    )
                else:
                    path_local.joinpath(GEODEPOT_CASES).mkdir(parents=True)
                url_root = urlparse(path).geturl()
                # Download existing repository
                response = requests_get("/".join([url_root, GEODEPOT_INDEX]))
                response.raise_for_status()
                path_local.joinpath(GEODEPOT_INDEX).write_bytes(response.content)
                response = requests_get("/".join([url_root, GEODEPOT_CONFIG_LOCAL]))
                response.raise_for_status()
                config = Config.from_json(response.content)
                if "origin" not in config.remotes:
                    remote_origin = Remote(name="origin", url=url_root)
                    config.remotes["origin"] = remote_origin
                    config.write(path_local.joinpath(GEODEPOT_CONFIG_LOCAL))
                    logger.debug(f"Added {remote_origin} to config.remotes")
                self._load_from_path(path_local)
            else:
                p = Path(path).resolve()
                if p.is_dir() and p.name == ".geodepot":
                    self._load_from_path(p)
                elif create:
                    # Create new repository
                    path_local = Path(path) / ".geodepot"
                    self._new_at_path(path=path_local)
                else:
                    raise GeodepotInvalidRepository(f"Not a Geodepot repository ({p}).")
        else:
            raise TypeError("Path must be a string or None")

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
        current_user = get_current_user()
        # Determine if we need to update a case's description or a data's description
        case_description = None
        data_description = None
        if casespec.data_name is not None:
            data_description = description
        else:
            case_description = description
        # Get an existing case or create an new if not exists
        if (case := self.get_case(casespec)) is None:
            try:
                case = self.init_case(casespec)
            except FileExistsError:
                raise GeodepotInvalidRepository(
                    f"The data for {casespec} is in the repository, but the index does not contain an entry for {casespec}. Try manually removing {casespec} from {self.path_cases} and re-adding it with 'geodepot add'."
                )
        # Update the description of an existing case
        if case_description is not None:
            case.description = case_description
            case.changed_by = current_user
            logger.info(f"Updated the description on the case {case.name}")
        if pathspec is None:
            # Only update the license or description or format
            if (data := self.get_data(casespec)) is not None:
                if data_description is not None:
                    data.description = data_description
                    data.changed_by = current_user
                    logger.info(f"Updated the description on the data entry {casespec}")
                if license is not None:
                    data.license = license
                    data.changed_by = current_user
                    logger.info(f"Updated the license on the data entry {casespec}")
                if format is not None:
                    data.format = format
                    case.changed_by = current_user
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
                data = case.add_from_path(
                    p,
                    casespec=casespec,
                    data_license=license,
                    data_format=format,
                    data_description=data_description,
                    data_changed_by=current_user,
                )
                self._copy_data(p, casespec)
                logger.info(f"Added {data.name} to {case.name}")
                logger.debug(data.to_pretty())
        self.index.add_case(case)
        self.write_index()
        logger.debug(f"Serialized the index to {self.path_index}")

    def fetch(self, remote: RemoteName) -> list[IndexDiff]:
        self.load_index(remote)
        return self.index.diff(self.index_remote)

    def get_case(self, casespec: CaseSpec) -> Case | None:
        """Retrieve an existing case."""
        return self.index.cases.get(casespec.case_name)

    def get_data(self, casespec: CaseSpec) -> Data | None:
        """Retrieve an existing data item.

        Return `None` if the data does not exist, or `casespec` does not specify a
        `data_name`.
        """
        if casespec.data_name is None:
            logger.error(
                f"Must specify data_name in {casespec} for getting a data item."
            )
            return None
        case = self.get_case(casespec)
        if case is not None:
            return case.get_data(casespec.data_name)
        logger.info(f"The entry {casespec} does not exist in the repository.")
        return None

    def get_data_path(self, casespec: CaseSpec) -> Path | None:
        """Retrieve the full path to an existing data item.

        If the data file does not exist locally, and a remote is configured, that
        contains the file, then it will be downloaded.
        """
        if (_ := self.get_data(casespec)) is not None:
            data_path = self.path_cases.joinpath(casespec.to_path())
            if data_path.exists():
                return data_path
            else:
                # Try downloading from remote
                from requests import get as requests_get

                remote = self.config.remotes.get("origin")
                if remote is not None:
                    logger.debug(
                        f"Did not find {casespec} locally, trying remote {remote}"
                    )
                    url_remote_data = "/".join(
                        [remote.url, GEODEPOT_CASES, str(casespec)]
                    )
                    response = requests_get(url_remote_data)
                    if response.status_code == 200:
                        data_path.parent.mkdir(exist_ok=True)
                        data_path.write_bytes(response.content)
                        logger.info(f"Downloaded {casespec} from remote '{remote}'")
                        return data_path
                    elif response.status_code == 404:
                        pass
                    else:
                        response.raise_for_status()
                else:
                    logger.debug(
                        f"Trying to download {casespec} from a remote, but the config does not contain a remote with name 'origin'."
                    )
        logger.info(f"The entry {casespec} does not exist in the repository.")
        return None

    def init_case(self, casespec: CaseSpec) -> Case:
        """Create a new case an return it."""
        case = Case(name=casespec.case_name, description=None)
        self.index.add_case(case)
        self.path_cases.joinpath(casespec.case_name).mkdir()
        return self.get_case(casespec)

    def load_config(self):
        """Load the configuration."""
        self.config = get_config(local_config=self.path_config_local)

    def load_index(self, remote: RemoteName | None = None):
        """Load the index.

        If 'remote' is provided, download and load the index from the remote.
        """
        if remote is None:
            self.index = Index.load(self.path_index)
            if self.index is None:
                raise GeodepotInvalidRepository(
                    f"Could not load index from {self.path_index}"
                )
        else:
            remote = self.config.remotes.get(remote)
            if remote is None:
                raise GeodepotInvalidRepository(
                    f"The remote '{remote}' is not configured for this repository. You can add it with 'remote add'."
                )

            remote_index_path = remote.path_index
            # If the URL is ssh, then the remote_index_url is the file path on the remote server
            if remote.is_ssh:
                # GDAL cannot handle ssh/sftp
                from fabric import Connection

                ssh_conn = Connection(remote.ssh_host)
                remote_index_locally = self.path / f"remote_{GEODEPOT_INDEX}"
                try:
                    result = ssh_conn.get(
                        remote=str(remote_index_path), local=str(remote_index_locally)
                    )
                    remote_index_url = Path(result.local)
                except Exception as e:
                    raise GeodepotInvalidRepository(
                        f"The remote '{remote}' cannot be accessed or does not contain a {GEODEPOT_INDEX} at {remote_index_path}. With:\n{e}"
                    )
            else:
                remote_index_url = remote_index_path
            if remote_index_url is not None:
                self.index_remote = Index.load(remote_index_url)
            else:
                raise GeodepotRuntimeError(
                    f"Something went wrong, could not load the index from {remote.url}."
                )

    def pull(self, remote_name: RemoteName, diff_all: list[IndexDiff]):
        """Overwrite the local repository with the changes in the remote."""
        remote = self.config.remotes.get(remote_name)
        if remote is None:
            raise GeodepotInvalidConfiguration(
                f"The remote '{remote_name}' is not configured for this repository."
            )
        if not remote.is_ssh:
            raise GeodepotInvalidConfiguration(
                f"The remote '{remote}' must use an ssh/sftp protocol in order to pull changes."
            )

        from fabric import Connection

        # See comments in 'push'. Here we do the opposite, because we overwrite the
        # local with the remote.
        data_to_download = set(
            i.casespec_other
            for i in diff_all
            if i.status == Status.ADD or i.status == Status.MODIFY
        )
        data_to_delete = set(
            i.casespec_self for i in diff_all if i.status == Status.DELETE
        )

        conn_ssh = Connection(remote.ssh_host)

        for data in data_to_download:
            data_path_local = self.path_cases.joinpath(data.to_path())
            data_path_remote = "/".join([remote.path_cases, str(data)])
            if data.is_case:
                case_archive = f"{data.case_name}.tar"
                try:
                    result = conn_ssh.run(
                        f"tar -cf {case_archive} -C {remote.path_cases} {data}"
                    )
                    if not result.ok:
                        logger.error(
                            f"Failed to tar {data} on remote {remote.name} with:\n{result.stderr}"
                        )
                    local_case_archive = self.path_cases / case_archive
                    _ = conn_ssh.get(local=str(local_case_archive), remote=case_archive)
                    with TarFile(local_case_archive) as tf:
                        tf.extractall(path=self.path_cases)
                    local_case_archive.unlink()
                except Exception as e:
                    logger.error(
                        f"Failed to download {data} from remote {remote.name} with:\n{e}"
                    )
            else:
                logger.debug(f"GET local={data_path_local} remote={data_path_remote}")
                try:
                    _ = conn_ssh.get(local=data_path_local, remote=data_path_remote)
                    logger.info(f"Downloaded {data} from {remote.name}")
                except Exception as e:
                    logger.error(
                        f"Failed to download {data} from {remote.name} with:\n{e}"
                    )
        for data in data_to_delete:
            if data.is_case:
                try:
                    rmtree(self.path_cases.joinpath(data.to_path()))
                except Exception as e:
                    logger.error(f"Failed to delete local {data} with error: {e}")
            else:
                try:
                    self.path_cases.joinpath(data.to_path()).unlink()
                except Exception as e:
                    logger.error(f"Failed to delete local {data} with error: {e}")

        try:
            logger.debug(f"GET local={self.path_index}, remote={remote.path_index}")
            _ = conn_ssh.get(local=str(self.path_index), remote=str(remote.path_index))
            logger.info(f"Downloaded {GEODEPOT_INDEX} from {remote_name}")
        except Exception as e:
            logger.error(f"Failed to download {GEODEPOT_INDEX} with error: {e}")

    def push(self, remote_name: RemoteName, diff_all: list[IndexDiff]):
        """Overwrite the remote repository with the changes in the local."""
        remote = self.config.remotes.get(remote_name)
        if remote is None:
            raise GeodepotInvalidConfiguration(
                f"The remote '{remote_name}' is not configured for this repository."
            )
        if not remote.is_ssh:
            raise GeodepotInvalidConfiguration(
                f"The remote '{remote}' must use an ssh/sftp protocol in order to push changes."
            )

        from fabric import Connection

        # i.status == Status.DELETE, because if the remote does not contain a data, it
        # shows as it deleted it
        data_to_upload = set(
            i.casespec_self
            for i in diff_all
            if i.status == Status.DELETE or i.status == Status.MODIFY
        )
        # Similarly, i.status == Status.ADD, because the remote contains a data that the
        # local doesn't, thus it 'adds' it w.r.t to the local. Since we push, we
        # overwrite the remote, meaning that if the local doesn't contain a specific
        # data, the remote shouldn't have it either.
        data_to_delete = set(
            i.casespec_other for i in diff_all if i.status == Status.ADD
        )

        conn_ssh = Connection(remote.ssh_host)

        for data in data_to_upload:
            data_path_local = self.path_cases.joinpath(data.to_path())
            data_path_remote = "/".join([remote.path_cases, str(data)])
            if data.is_case:
                # Upload a whole case
                for dirpath, dirnames, filenames in data_path_local.walk():
                    relpath = dirpath.relative_to(self.path_cases)
                    remote_path = "/".join([remote.path_cases, str(relpath)])
                    try:
                        result = conn_ssh.run(f"mkdir -p {remote_path}")
                        if not result.ok:
                            logger.error(
                                f"Failed to create directory {relpath} on {remote.name} with:\n{result.stderr}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to create directory {relpath} on {remote.name} with:\n{e}:"
                        )

                    for d in dirnames:
                        local_path = dirpath / d
                        relpath = local_path.relative_to(self.path_cases)
                        remote_path = "/".join([remote.path_cases, str(relpath)])
                        try:
                            result = conn_ssh.run(f"mkdir -p {remote_path}")
                            if not result.ok:
                                logger.error(
                                    f"Failed to create directory {d} on {remote.name} with:\n{result.stderr}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Failed to create directory {d} on {remote.name} with:\n{e}:"
                            )

                    for filename in filenames:
                        local_path = dirpath / filename
                        relpath = local_path.relative_to(self.path_cases)
                        remote_path = "/".join([remote.path_cases, str(relpath)])
                        try:
                            logger.debug(f"PUT local={local_path} remote={remote_path}")
                            _ = conn_ssh.put(local=local_path, remote=remote_path)
                            logger.info(f"Uploaded {data} to {remote.name}")
                        except Exception as e:
                            logger.error(
                                f"Failed to upload {data} to {remote.name} with:\n{e}"
                            )
            else:
                # Upload a single data file
                try:
                    logger.debug(
                        f"PUT local={data_path_local} remote={data_path_remote}"
                    )
                    _ = conn_ssh.put(local=data_path_local, remote=data_path_remote)
                    logger.info(f"Uploaded {data} to {remote.name}")
                except Exception as e:
                    logger.error(f"Failed to upload {data} to {remote.name} with:\n{e}")
        for data in data_to_delete:
            data_path_remote = "/".join([remote.path_cases, str(data)])
            try:
                if data.is_case:
                    # Delete a whole case
                    result = conn_ssh.run(f"rm -rf {data_path_remote}")
                else:
                    # Delete a data file
                    result = conn_ssh.run(f"rm {data_path_remote}")

                if not result.ok:
                    logger.error(
                        f"Failed to delete {data} on {remote.name} with:\n{result.stderr}"
                    )
                else:
                    logger.info(f"Deleted {data} on {remote.name}")
            except Exception as e:
                logger.error(f"Failed to delete {data} on {remote.name} with:\n{e}")

        try:
            logger.debug(f"PUT local={self.path_index}, remote={remote.path_index}")
            _ = conn_ssh.put(self.path_index, remote=remote.path_index)
            logger.info(f"Transferred {GEODEPOT_INDEX} to {remote.name}")
        except Exception as e:
            logger.error(
                f"Failed to transfer {GEODEPOT_INDEX} to {remote.name} with:\n{e}"
            )

    def remove(self, casespec: CaseSpec):
        """Remove an entry from the repository."""
        if casespec.is_case:
            # Remove the whole case
            if (
                case := self.index.remove_case(case_name=casespec.case_name)
            ) is not None:
                rmtree(self.path_cases.joinpath(casespec.to_path()))
                self.index.write(self.path_index)
                logger.info(f"Removed {case.name} from the repository")
            else:
                logger.info(f"The case {casespec} does not exist in the repository")
        else:
            if (case := self.get_case(casespec)) is not None:
                data = case.remove_data(casespec.data_name)
                if data is not None:
                    if (p := self.path_cases.joinpath(casespec.to_path())).is_dir():
                        p.rmdir()
                    else:
                        p.unlink(missing_ok=False)
                        # TODO: I could remove the whole case if there are no more files. Don't forget to remove the case from the index too.
                    self.index.write(self.path_index)
                    logger.info(f"Removed {data.name} from the repository")
                else:
                    logger.info(
                        f"The data entry {casespec} does not exist in the repository"
                    )
            else:
                logger.info(
                    f"The case {casespec.case_name} does not exist in the repository"
                )

    def write_index(self):
        """Serialize the index."""
        self.index.write(self.path_index)

    def _copy_data(self, path: Path, casespec: CaseSpec):
        """Copies a data entry into the repository."""
        if path.is_file():
            if casespec.data_name is not None:
                # Rename the file when copied into the case
                copy2(
                    path,
                    self.path_cases.joinpath(casespec.case_name, casespec.data_name),
                )
            else:
                # Keep the file name
                copy2(path, self.path_cases.joinpath(casespec.case_name, path.name))
        else:
            if casespec.data_name is not None:
                # Copying a directory as a single data entry under a new name
                copytree(
                    path,
                    self.path_cases.joinpath(casespec.case_name, casespec.data_name),
                    dirs_exist_ok=True,
                )
            else:
                copytree(
                    path,
                    self.path_cases.joinpath(casespec.case_name, path.name),
                    dirs_exist_ok=True,
                )

    def _load_from_path(self, path: Path) -> None:
        """Load a repository from a local path.

        :raises: GeodepotInvalidRepository"""
        self.path = path
        self.load_index()
        self.load_config()
        if not self.path_cases.is_dir():
            raise GeodepotInvalidRepository(
                f"cases directory {self.path_cases} does not exist"
            )
        if not self.path_config_local.is_file():
            raise GeodepotInvalidRepository(
                f"local config {self.path_config_local} does not exist"
            )
        logger.debug(f"Loaded existing geodepot repository at {self.path}")

    def _new_at_path(self, path: Path) -> None:
        self.path = path
        self.path.mkdir()
        self.path_cases.mkdir()
        self.index = Index()
        self.index.write(self.path_index)
        self.config = Config()
        self.config.write(self.path_config_local)
        logger.info(f"Initialized empty Geodepot repository at {self.path}")


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
