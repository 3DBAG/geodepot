from geodepot.data_file import DataFile
from geodepot.case import *


def test_case(data_dir):
    case = Case("wippolder", "Some case description.\nMultiline.\nText")
    for df in ("wippolder.gpkg", "wippolder.las", "3dbag_one.city.json"):
        case.add_data_file(DataFile(data_dir / df))
    print(case)
