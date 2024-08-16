import pytest

from geodepot.data_file import DataFile
from geodepot.repository import *


@pytest.fixture
def mock_temp_project(tmp_path, monkeypatch):
    def mockreturn():
        return tmp_path

    monkeypatch.setattr(Path, "cwd", mockreturn)


def test_empty(mock_temp_project):
    """Can we create an empty repository?"""
    repo = Repository()
    repo.init()
    print(repo)


def test_add(mock_temp_project, mock_user_home, data_dir):
    repo = Repository()
    repo.init()

    repo.add("wippolder", pathspec=str(data_dir/"wippolder.gpkg"),
             description="wippolder case description", license="CC-0")
    repo.add("wippolder", pathspec=str(data_dir/"wippolder.las"),
             description="wippolder case description", license="CC-0")

    # fishy
    repo.index.serialize(repo.path.joinpath("index.geojson"))
    print(repo)

def test_load(mock_temp_project, mock_user_home, data_dir):
    repo = Repository()
    repo.init()

    repo.add("wippolder", pathspec=str(data_dir/"wippolder.gpkg"),
             description="wippolder case description", license="CC-0")
    repo.add("wippolder", pathspec=str(data_dir/"wippolder.las"),
             description="wippolder case description", license="CC-0")

    # fishy
    repo.index.serialize(repo.path.joinpath("index.geojson"))
    print()
    print(repo.index)
    repo.load_index()
    print(repo.index)