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

## High-level design

Related test data is organised into repositories.
Normally, there is one repository per project, storing all the data that are required by the tests of the project.
For example, the 3dbag-pipeline and geoflow-roofer would each have their own repository.

Geodepot is meant for organising data into test cases, aid with the management operations and provide integration to some of the test frameworks for ease of use.

Geodepot is not a data version control system, so do not use it as such, because you might loose your data.
It is assumed that the data that you store in a geodepot repository is already available, and will stay available in some other form.
Thus, if the repository is accidentally overwritten with unwanted changes, the desired state can be recreated with moderate effort.
That is, because the history of the repository is not retained, only the latest version is available.

Conflicts between the local and remote repository are resolved according to the selected operation.
The [pull](#pull) command overwrites the local with the contents of the remote repository.
The [push](#push) command overwrites the remote with the content of the local repository.

### Interfaces

- CLI
- CMake module that exposes a single function, similar to FetchContent, to download and update the test data
- API (python)
- QGIS plugin

### Operations

- [init](#init)
- [clone](#clone)
- [add](#add)
- [remove](#remove)
- [pull](#pull)
- [push](#push)
- [remote](#remote-list)
- [remote add](#remote-add)
- [remote remove](#remote-remove)
- [snapshot](#snapshot-list)
- [snapshot save](#snapshot-save)
- [snapshot load](#snapshot-load)
- [snapshot remove](#snapshot-remove)

#### init

Initialise an empty local repository.

#### clone

Clone a remote repository and make it available locally.
Only downloads the INDEX, does not download the data files.
The data needs to be `pull`-ed explicitly after the repository has been cloned.

#### add

Adds a single case to the repository.

#### remove

Deletes a single case from the repository.

#### pull

Downloads any changes from the remote repository, overwriting the local version.
Without arguments, it checks and downloads all cases if needed. 
With the case ID as argument, `geodepot pull <case-id>`, it only checks and downloads the specified case.

#### push

Uploads any local changes to the remote repository, overwriting the remote version.

#### remote

With no arguments, shows the existing remotes.

#### remote add

Add a remote repository to track. The remote repository must exist.

#### remote remove

Remove the remote from the tracked remotes. The remote repository is not deleted.

#### snapshot

With no arguments, shows the available snapshots.

#### snapshot save

Save the current state of the repository.

#### snapshot load

Overwrite the repository from a saved snapshot.

#### snapshot remove

Delete a snapshot.

## Detailed design

### The INDEX

The INDEX contains the overview of all cases in the repository.
For each case, the INDEX stores:

- identifier
- description
- bounding box
- projection information
- link (? might not be necessary)
- license

The BBox is in EPSG:3857, so that in can be visualised easily in any web viewer.
Maybe Flatgeobuff to be queriable without a server.

### Data files

Data is in *.zip*. 
There is no custom format, just plain GIS formats zipped. 
2D vector formats are thus GDAL-readable from within the *.zip*.

Formats:
- gpkg
- laz
- cityjson

When data is added, its BBox is computed from the data or header.
Although, ideally, we would not depend on GDAL, because it's a very heavy dependency.

## Notes

Need to have an self-contained executable for all the three OS-es, although, it could rely on a gdal installation.

Hash of the archive is required, for checking if new version needs to be downloaded.
Mimic cmake's fetchcontent.

git lfs could be sth to use, but maybe overkill because need to set up and operate a remote server. Would be better not to use any server.



