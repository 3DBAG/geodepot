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

Geodepot is meant for organising data into test cases, aid with the management operations and provide integration to some of the test frameworks for ease of use.

Geodepot is not a data version control system, so do not use it as such, because you might loose your data.
It is assumed that the data that you store in a geodepot repository is already available, and will stay available in some other form.
Thus, if the repository is accidentally overwritten with unwanted changes, the desired state can be recreated with moderate effort.
That is, because the history of the repository is not retained, only the latest version is available.

Conflicts between the local and remote repository are resolved according to the selected operation.
The [pull](#pull) command overwrites the local with the contents of the remote repository.
The [push](#push) command overwrites the remote with the content of the local repository.
- use a lock to lock the repository
- check hashes to see what was the previous state, store hashes in the index file

At the bare minimum, geodepot provides:

- An overview of the available cases.
- An identifier and description of each case.
- A way to easily get the path to the data file of a case, so that in a test, we can do `geodepot.get(case-id, filename-with-ext)` to obtain the path to the uncompressed data file.

### Concepts

#### Repository

A *repository* is a collection of related *cases* that are used as data in software testing.
Normally, there is one repository per project, storing all the data that are required by the tests of the project.
For example, the *3dbag-pipeline* and *geoflow-roofer* would each have their own repository.

#### Index

The *repository* organises the *cases* with its *index*.
The *index* stores the overview of all *cases* in the repository.

#### Case

A *case* is identified by its identifier and name.
A *case* contains one or more *data files*.

#### Data (file)

A *data file* is the actual file that contains the data that is used in a test.
Data files are regular GIS files, for example GeoPackage, LAS or CityJSON.

### Examples

Initialising an empty repository, adding a case, adding a remote and uploading the repository to the remote.

```shell
cd my-project
geodepot init
geodepot add case-name /path/to/dir/with/data description
geodepot remote add remote-name https://remote.url
geodepot push remote-name
```

Cloning an existing repository from a remote and list the available cases.
Cloning the repository only downloads the index, but not the data files.

```shell
cd my-project
geodepot clone https://remote.url
geodepot list
```

Returns:

```shell
ID  NAME    DESCRIPTION
--  ----    -----------
1   case-1  A single building in the Netherlands.
```

Show the details of a case to see its data files.

```shell
geodepot show case-1
```

Returns:

```shell
CASE ID: 1

FILE                CRS
----                ---
footprint.gpkg      EPSG:28992
pointcloud.laz      EPSG:7415

```

Get the path to the specified file of the specified case.

```shell
geodepot get case-1 footprint.gpkg
```

Returns:

```shell
/path/to/.geodepot/cases/1/footprint.gpkg
```

### Interfaces

#### CLI 
supports all operations, this is the main interface

#### CMake 
CMake module that exposes a single function, similar to FetchContent, to download and update the test data. Alternatively, a CMake function like `GeodepotGet(case-id, filename-with-ext)`, which would return the path to the unzipped data file of the case. If the repository is not present on the local system, it clones the repo on the first call of the function.

#### API 
Basically, the only function that is needed is `geodepot.get(case-id, filename-with-ext)`, which gives the full path to a specific file in a specific case.

#### QGIS plugin
Support adding, viewing, modifying cases.

### Operations

the commands that have the same name as in git, but do sth different are confusing

- [init](#init) merge init with clone so that `init <remote-url>` downloads the repo and index
- [clone](#clone)
- [list](#list)
- [show](#show)
- [get](#get)
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

#### list

List the cases in the repository.

#### show <case-id>

Show the details of the specified case.

#### get <case-id> <filename>

Return the full path to the specified data file of the specified case.

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
- storage format
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

### Repository layout

The geodepot repository is stored in a `.geodepot` directory, at the root directory of a project.

```
.geodepot/
├── cases
├── index
├── refs
└── snapshots
```

When using the CLI, geodepot looks for the `.geodepot` directory in the current directory.
When using the API, geodepot can be configured with a path to `.geodepot`, e.g. `geodepot.configure(<path-to-geodepot-dir>)`.

### Dependencies

Basically, the data files only need to be parsed when their BBox is computed, when they are added to the repository.
That means, that in a testing scenario when the cases are only retrieved, e.g. CI, the heavy GIS dependencies like GDAL, PDAL are not required.
Need to have an self-contained executable for all the three OS-es, although, it could rely on a system GDAL installation.

### Language of choice

C++ is a pain, but offers the best possibilities, especially, because of the native GIS libraries.

Rust is a love, but the GIS library ports are only supported on Ubuntu (mostly).

Python is very convenient for development, but the whole Python interpreter + venv is required for running geodepot.
Additionally, Python is not the best language to write bindings to other languages, like C++ and Rust.
Unless, I compile it into an exe with pyinstaller.
With pyinstaller, geodepot is compiled into a statically linked exe, so it can be used without Python and GIS dependencies.
We can write it all in Python, and distribute the exe.
Then write the API in C++/Rust, which is easy, because they only need two functions, `configure` and `get`. 
Both are simple operations.
In this case, the API would have a complete independent codebase from the geodepot app, thus it wouldn't require any of the heavy dependencies, which is nice.
Maintaining the two functions in the API is easy enough.

### Packaging and distribution

The executable and directory bundle is generated with Pyinstaller's `--onedir` option.
The exe must stay in the directory, thus when the user downloads the latest release, they need to place the whole dir to the location and link to the exe somehow.
I could create and install script for each release, which would download the latest release, move to the correct location, evtl. replace the old version and take care to adding the exe to the path.

## Notes

How to compute the BBox of a case, if the the data files have different CRS?
In case there are multiple CRS-es are detected in the case, geodepot could ask which file to use for the BBox calculation.

If cannot compute BBox, maybe possible to manually provide a single point of reference.
Spatial reference and projection information is optional.

Probably OO would be neat, like having a `Case` and `CaseCollection` (serialised to the INDEX) with their methods.

https://github.com/ArthurSonzogni/FTXUI
https://textual.textualize.io/

A case can contain any number of files. If `geodepot.get_case(case-id)` returns the path to the case, then the required file name still needs to be appended to the case-path.
How do I know what data files are in a case?
With `geodepot show <case-id>`.

Hash of the archive is required, for checking if new version needs to be downloaded.
Mimic cmake's fetchcontent.

git lfs could be sth to use, but maybe overkill because need to set up and operate a remote server. Would be better not to use any server.



