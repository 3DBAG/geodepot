# Design document

## Problem statement

We consider two aspects of robustness both for spatial data processing software, in particular 3D: robustness against critical errors that break the execution of the code, and robustness against regression in the quality of the output.
For measuring and improving both aspects, a comprehensive set of tests and suitable input data are needed.

Spatial data processing software are often tested against specific inputs/cases ... fake data is not suitable

data often stored locally in scattered files, their purpose is forgotten over time
problematic to share with other developers


Collecting, maintaining and serving such an input data set is not trivial. This software aims to facilitate the workflow.

Some of the requirements for the input data:

- it needs to represent the cases where errors occur during reconstruction,
- it needs to represent the cases where quality regression can occur during reconstruction,
- both individual objects and areas need to be available,
- access needs to be fast enough to use during automated testing, this implies that the returned data format needs to efficient for fast transfer over the web,
- it needs to contain one or multiple sample areas of all the input data sets, such as AHN3, AHN4, BAG, TOP10NL,
- the individual cases need to be documented,
- it is possible to easily add and document new cases, for instance a problematic object that was reported by a user.

## Background

- git, [git-lfs](https://git-lfs.com/)
- CMake's [FetchContent](https://cmake.org/cmake/help/latest/module/FetchContent.html#fetchcontent), [ExternalData](https://cmake.org/cmake/help/latest/module/ExternalData.html)

## Notes

add
delete
pull
push
clone

no history

how resolve local-remote conflicts?

index file with id, description, bbox, link, (format?), license. BBox in some global crs for the web to be easily visualized. Maybe flatgeobuff to be queriable without a server.

Data is in .zip. There is no custom format, just plain gis formats zipped. 2D vector formats are thus gdal-readable from within the .zip.

Formats:
- gpkg
- laz
- cityjson

When data is added, its bbox is computed from the data or header.

Hash of the archive is required, for checking if new version needs to be downloaded.
Mimic cmake's fetchcontent.

git lfs could be sth to use, but maybe overkill because need to set up and operate a remote server. Would be better not to use any server.

Ideally, we wouldn't depend on gdal, because it's a very heavy dependency.

QGIS plugin would be the best way to manage (add/remove) data.
