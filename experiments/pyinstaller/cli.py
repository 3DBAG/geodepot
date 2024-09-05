from click import command, argument, echo
from osgeo.ogr import UseExceptions, Open
from pdal import Pipeline
from json import dumps

UseExceptions()

pdal_filter_stats = {"type": "filters.stats", "dimensions": "X,Y"}

path_pdal = "/home/balazs/Development/geodepot/tests/data/wippolder.las"
path_gdal = "/home/balazs/Development/geodepot/tests/data/wippolder.gpkg"


@command()
@argument("path_gdal")
@argument("path_pdal")
def info(path_gdal, path_pdal):
    echo("version 3")
    pdal_pipeline = Pipeline(dumps([path_pdal, pdal_filter_stats]))
    pdal_pipeline.execute()
    x_max = pdal_pipeline.metadata["metadata"]["filters.stats"]["statistic"][0][
        "maximum"
    ]
    x_min = pdal_pipeline.metadata["metadata"]["filters.stats"]["statistic"][0][
        "minimum"
    ]
    y_max = pdal_pipeline.metadata["metadata"]["filters.stats"]["statistic"][1][
        "maximum"
    ]
    y_min = pdal_pipeline.metadata["metadata"]["filters.stats"]["statistic"][1][
        "minimum"
    ]
    echo(f"Point cloud bbox: {x_min} {y_min} {x_max} {y_max}")
    echo(f"Point cloud CRS: {pdal_pipeline.srswkt2}")

    with Open(path_gdal) as ogr_dataset:
        lyr = ogr_dataset.GetLayer(0)
        echo(f"OGR bbox: {lyr.GetExtent(force=True)}")
        echo(f"OGR spatial reference: {lyr.GetSpatialRef().ExportToWkt()}")


if __name__ == "__main__":
    info()
