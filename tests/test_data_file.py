import pytest

from geodepot.data_file import *


@pytest.mark.parametrize(
    "file_name", ("wippolder.gpkg", "wippolder.las", "3dbag_one.city.json")
)
def test_data_file(mock_proj_lib, data_dir, file_name):
    """Can we initialize a DataFile from a local file?"""
    data_file = DataFile(data_dir / file_name, "CC-0")
    assert data_file.bbox is not None


class TestFormatInference:

    @pytest.mark.parametrize(
        "suffixes,expected",
        (
            ([".city", ".json"], True),
            ([".city", ".jsonl"], False),
            ([".cityjson"], True),
        ),
    )
    def test_cityjson(self, suffixes, expected):
        assert is_cityjson(suffixes) == expected

    @pytest.mark.parametrize(
        "file,expected",
        (
            ("wippolder.gpkg", "GPKG"),
            ("wippolder.las", None),
        ),
    )
    def test_ogr(self, data_dir, file, expected):
        assert try_ogr(data_dir / file) == expected

    @pytest.mark.parametrize(
        "file,expected",
        (
            ("wippolder.gpkg", None),
            ("wippolder.las", "las"),
        ),
    )
    def test_pdal(self, data_dir, file, expected):
        assert try_pdal(data_dir / file) == expected
