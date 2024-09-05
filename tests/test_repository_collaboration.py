from copy import deepcopy
from pathlib import Path

import pytest

from geodepot.repository import Repository, Index, Status, format_indexdiffs
from geodepot.case import CaseName, Case
from geodepot.data import Data, DataName, BBoxSRS, BBox, Drivers
from geodepot.config import RemoteName, User


@pytest.fixture
def mock_temp_project(tmp_path, monkeypatch):
    def mockreturn():
        return tmp_path

    monkeypatch.setattr(Path, "cwd", mockreturn)


@pytest.fixture(scope="function")
def repo(mock_temp_project, mock_user_home):
    repo = Repository()
    return repo


@pytest.fixture(scope="module")
def user_local() -> User:
    return User(name="Kovács János", email="janos@kovacs.me")


@pytest.fixture(scope="module")
def user_remote() -> User:
    return User(name="Remote User", email="remote@user.me")


@pytest.fixture(scope="function")
def case_wippolder(user_local) -> Case:
    return Case(
        name=CaseName("wippolder"),
        description=None,
        sha1=None,
        data=dict(),
        changed_by=user_local,
    )


@pytest.fixture(scope="function")
def data_wippolder_gpkg(user_local) -> Data:
    df = Data.__new__(Data)
    df.name = DataName("wippolder.gpkg")
    df.changed_by = user_local
    df.description = None
    df.driver = Drivers.OGR
    df.format = "GPKG"
    df.license = "CC-0"
    df.sha1 = "b1ec6506eb7858b0667281580c4f5a5aff6894b2"
    df.bbox = BBoxSRS(
        bbox_epsg_3857=BBox(
            minx=486674.52386715333,
            miny=6801456.846056759,
            maxx=486963.8952750344,
            maxy=6801658.42738468,
        ),
        bbox_original_srs=BBox(
            minx=85289.890625, miny=447041.96875, maxx=85466.6953125, maxy=447163.53125
        ),
        srs_wkt='PROJCS["Amersfoort / RD New",GEOGCS["Amersfoort",DATUM["Amersfoort",SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],AUTHORITY["EPSG","6289"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4289"]],PROJECTION["Oblique_Stereographic"],PARAMETER["latitude_of_origin",52.1561605555556],PARAMETER["central_meridian",5.38763888888889],PARAMETER["scale_factor",0.9999079],PARAMETER["false_easting",155000],PARAMETER["false_northing",463000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","28992"]]',
    )
    return df


@pytest.fixture(scope="function")
def data_wippolder_gpkg_modified(user_remote) -> Data:
    df = Data.__new__(Data)
    df.name = DataName("wippolder.gpkg")
    df.changed_by = user_remote
    df.description = None
    df.driver = Drivers.OGR
    df.format = "GPKG"
    df.license = None
    df.sha1 = "ed8b3ccbaf14970a402efd68f7bfa7db20a2543a"
    df.bbox = BBoxSRS(
        bbox_epsg_3857=BBox(
            minx=486698.6792049131,
            miny=6801457.174546329,
            maxx=486918.55532958306,
            maxy=6801606.699109667,
        ),
        bbox_original_srs=BBox(
            minx=85304.3515625, miny=447041.96875, maxx=85438.7265625, maxy=447132.09375
        ),
        srs_wkt='PROJCS["Amersfoort / RD New",GEOGCS["Amersfoort",DATUM["Amersfoort",SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],AUTHORITY["EPSG","6289"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4289"]],PROJECTION["Oblique_Stereographic"],PARAMETER["latitude_of_origin",52.1561605555556],PARAMETER["central_meridian",5.38763888888889],PARAMETER["scale_factor",0.9999079],PARAMETER["false_easting",155000],PARAMETER["false_northing",463000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","28992"]]',
    )
    return df


@pytest.fixture(scope="function")
def data_wippolder_las(user_local) -> Data:
    df = Data.__new__(Data)
    df.name = DataName("wippolder.las")
    df.changed_by = user_local
    df.description = None
    df.driver = Drivers.PDAL
    df.format = "las"
    df.license = "CC-0"
    df.sha1 = "d22feced58136b7052caa73d1676ced45041e7b9"
    df.bbox = BBoxSRS(
        bbox_epsg_3857=None,
        bbox_original_srs=BBox(
            minx=85266.56097, miny=447017.954, maxx=85530.10597, maxy=447214.746
        ),
        srs_wkt=None,
    )
    return df


def test_add_case(case_wippolder, user_local, user_remote):
    """Can we report that a new case was added by the remote?"""
    # Added by remote
    case_remote = deepcopy(case_wippolder)
    case_remote.changed_by = user_remote
    index_local = Index()
    (index_remote := Index()).add_case(case_remote)
    diff_all = index_local.diff(index_remote)
    assert len(diff_all) == 1
    assert diff_all[0].status == Status.ADD
    assert diff_all[0].changed_by_other == user_remote


def test_delete_case(case_wippolder, user_local, user_remote):
    """Can we report that a case was deleted by the remote?"""
    # Deleted by remote
    case_local = deepcopy(case_wippolder)
    (index_local := Index()).add_case(case_local)
    index_remote = Index()
    diff_all = index_local.diff(index_remote)
    assert len(diff_all) == 1
    assert diff_all[0].status == Status.DELETE
    assert diff_all[0].changed_by_other is None


def test_add_data(
    case_wippolder,
    data_wippolder_gpkg,
    data_wippolder_gpkg_modified,
    user_local,
    user_remote,
):
    """Can we report that a new data was added by the remote?"""
    # Added by remote
    case_local = deepcopy(case_wippolder)
    (case_remote := deepcopy(case_wippolder)).add_data(data_wippolder_gpkg_modified)
    (index_local := Index()).add_case(case_local)
    (index_remote := Index()).add_case(case_remote)
    diff_all = index_local.diff(index_remote)
    assert len(diff_all) == 1
    assert diff_all[0].status == Status.ADD
    assert diff_all[0].changed_by_other == user_remote


def test_delete_data(
    case_wippolder,
    data_wippolder_gpkg,
    data_wippolder_gpkg_modified,
    user_local,
    user_remote,
):
    """Can we report that a data was deleted by the remote?"""
    # Deleted by remote
    (case_local := deepcopy(case_wippolder)).add_data(data_wippolder_gpkg)
    (case_remote := deepcopy(case_wippolder)).add_data(data_wippolder_gpkg_modified)
    case_remote.remove_data(DataName("wippolder.gpkg"))
    # Mimic that another user deleted the data
    case_remote.changed_by = user_remote
    (index_local := Index()).add_case(case_local)
    (index_remote := Index()).add_case(case_remote)
    diff_all = index_local.diff(index_remote)
    assert len(diff_all) == 1
    assert diff_all[0].status == Status.DELETE
    assert diff_all[0].changed_by_other == user_remote


def test_modify_case(case_wippolder, user_remote):
    """Can we report that a case was modified? Even if the case doesn't contain data?"""
    # Modified by remote
    case_local = deepcopy(case_wippolder)
    case_remote = deepcopy(case_wippolder)
    case_local.description = "Local description"
    case_remote.description = "New description on remote"
    # Mimic that another user deleted the data
    case_remote.changed_by = user_remote
    (index_local := Index()).add_case(case_local)
    (index_remote := Index()).add_case(case_remote)
    diff_all = index_local.diff(index_remote)
    assert len(diff_all) == 1
    for d in diff_all:
        assert d.changed_by_other == user_remote
        assert d.status == Status.MODIFY


def test_modify_data(
    case_wippolder,
    data_wippolder_gpkg,
    data_wippolder_gpkg_modified,
    user_local,
    user_remote,
):
    """Can we report that a data was modified?"""
    # Modified by remote
    (case_local := deepcopy(case_wippolder)).add_data(data_wippolder_gpkg)
    (case_remote := deepcopy(case_wippolder)).add_data(data_wippolder_gpkg_modified)
    (index_local := Index()).add_case(case_local)
    (index_remote := Index()).add_case(case_remote)
    diff_all = index_local.diff(index_remote)
    # There are 3 differences, not 4, because the 'changed_by' is reported separately
    assert len(diff_all) == 3
    for d in diff_all:
        assert d.changed_by_other == user_remote
        assert d.status == Status.MODIFY
    # Modified by local
    diff_all = index_remote.diff(index_local)
    assert len(diff_all) == 3
    for d in diff_all:
        assert d.changed_by_other == user_local
        assert d.status == Status.MODIFY


def test_format_indexdiffs(
    case_wippolder,
    data_wippolder_gpkg,
    data_wippolder_gpkg_modified,
):
    (case_local := deepcopy(case_wippolder)).add_data(data_wippolder_gpkg)
    (case_remote := deepcopy(case_wippolder)).add_data(data_wippolder_gpkg_modified)
    (index_local := Index()).add_case(case_local)
    (index_remote := Index()).add_case(case_remote)
    diff_all = index_local.diff(index_remote)
    diff_all_formatted = format_indexdiffs(diff_all, push=True)
    print()
    print(diff_all_formatted)


def test_push_debug():
    repo = Repository(
        path="/home/balazs/Development/geodepot/tests/data/integration/client1/.geodepot"
    )
    diff_all = repo.fetch(RemoteName("ssh"))
    repo.push(RemoteName("ssh"), diff_all)


# def test_format_indexdiffs_debug():
#     index_local = Index.load(Path("/home/balazs/Development/geodepot/tests/tmp_project/.geodepot/index.geojson"))
#     index_remote = Index.load(Path("/home/balazs/Development/geodepot/tests/data/integration/server/.geodepot/index.geojson"))
#     diff_all = index_local.diff(index_remote)
#     diff_all_formatted = format_indexdiffs(diff_all, push=False)
#     print()
#     print(diff_all_formatted)
