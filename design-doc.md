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

- git
- [git-lfs](https://git-lfs.com/)
- https://git-annex.branchable.com/, https://switowski.com/blog/git-annex/, https://www.youtube.com/watch?v=pp8IeGXpRRI&list=PLEQHbPfpVqU6esVrgqjfYybY394XD2qf2&index=5
- https://www.datalad.org/
- CMake's [FetchContent](https://cmake.org/cmake/help/latest/module/FetchContent.html#fetchcontent), [ExternalData](https://cmake.org/cmake/help/latest/module/ExternalData.html)

## High-level design

Geodepot is meant for organising data into test cases, aid with the management operations and provide integration to some of the test frameworks for ease of use.

Geodepot is not a data version control system, so do not use it as such, because you might loose your data.
It is assumed that the data that you store in a geodepot repository is already available, and will stay available in some other form.
Thus, if the repository is accidentally overwritten with unwanted changes, the desired state can be recreated with moderate effort.
That is, because the history of the repository is not retained, only the latest version is available.

At the bare minimum, geodepot provides:

- An overview of the available cases.
- An identifier and description of each case.
- A way to easily get the path to the data file of a case, so that in a test, we can do `geodepot.get(case-id, filename-with-ext)` to obtain the path to the uncompressed data file.

### Concepts

#### User

The user information consists of a name and an e-mail address and it is registered in the local HOME directory of the User.
The user information is used for identifying changes and locks.

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
geodepot add case-name /path/to/dir/with/data --description "text"
geodepot remote add remote-name https://remote.url
geodepot push remote-name
```

Cloning an existing repository from a remote and list the available cases.
Cloning the repository only downloads the index, but not the data files.

```shell
cd my-project
geodepot init https://remote.url
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
Supports all operations, this is the main interface.

#### API 
The API is meant for passing data paths to tests, nothing else.
The rest of the operations are done through the CLI.
Therefore, there are only two functions that are needed: 
- Maybe `geodepot.configure(<path-to-geodepot-dir>)`, see [Repository layout](#repository-layout), but need to see what is best in combination with `init`. Although, the `geodepot` constructor could be used to configure the repository path too, instead of an explicit `configure` method.
- `geodepot.init(remote-url)`, which downloads the remote repository, except the data files and makes it possible to get cases.
- `geodepot.get(case-id, filename-with-ext)`, which returns the full path to a specific file in a specific case on the local system.

The API is available in:
- C++ (implementation)
- Python (binding)
- Rust (binding)

#### CMake 
Offers the same functionality as the API, but with CMake functions:
- `GeodepotInit(remote-url)`
- `GeodepotGet(case-id, filename-with-ext)`

If the geodepot index needs to be parsed, the CMake commands alone won't suffice to write the functions.
In that case, I would need to compile the C++ API into an exe, and run that exe for the functions.
See [CMake custom commands](https://cmake.org/cmake/help/latest/guide/tutorial/Adding%20a%20Custom%20Command%20and%20Generated%20File.html).

Even if I could write `GeodepotInit` and `GeodepotGet` purely in cmake-language, using `FetchContent` it may be better to call a compiled exe that is part of the C++ API.
That is, because, 
1. the C++ implementation is the single source of truth,
2. if I need more complex operations in the future, I won't be limited by the cmake-language.

#### QGIS plugin
Support adding, viewing, modifying cases.

### Commands

the commands that have the same name as in git, but do sth different are confusing

- [x] [config](#config)
- [x] [init](#init)
- [list](#list)
- [show](#show)
- [x] [get](#get)
- [x] [add](#add)
- [x] [remove](#remove)
- [pull](#pull)
- [push](#push)
- [verify](#verify)
- [-] [remote](#remote-list)
- [-] [remote add](#remote-add)
- [-] [remote remove](#remote-remove)
- [snapshot](#snapshot-list)
- [snapshot save](#snapshot-save)
- [snapshot load](#snapshot-load)
- [snapshot remove](#snapshot-remove)

#### config

Configure Geodepot.

#### init

**Synopsis**

```shell
geodepot init [url]
```

**Description**

Initialise a geodepot repository in the current directory.

**Options**

Without arguments, initialise an empty local repository in the current directory.

With a URL to a remote repository as an argument, `geodepot init <url>`, download the remote repository except its data files, to make it available locally.
The data needs to be `pull`-ed explicitly after the repository has been initialised.

#### list

List the cases in the repository.

#### show <case-id>

Show the details of the specified case.

#### get

**Synopsis**

```shell
geodepot get <casespec>
```

**Description**

Return the full local path to the specified data item of the specified case.
If the data item does not exist locally and a remote repository is configured, the data will be downloaded from the remote.

**Options**

`<casespec>`:
Case (and data) specifier, in the form of `case-name/data-name`.
For example, `wippolder/wippolder.gpkg`, where `wippolder` is the case name, `wippolder.gpkg` is the data name.

#### add

**Synopsis**

```shell
geodepot add [-y] [--license=<text>] [--description=<text>] [--format=<format>] [--as-data] [<pathspec>...] <casespec>
```

**Description**

In each operation, the case will be created if it does not exist.
In each operation, existing values, data files are updated with the newly provided.

**Options**

`<casespec>`:
Case (and data) specifier, in the form of `case-name[/data-name]`.
Providing the case name `case-name` is mandatory, the data name `data-name` within the case is optional.
The rest of the options will affect the specified level, either the whole case with `case-name`, or just a single data within the case with `case-name/data-name`.
For example, `wippolder/wippolder.gpkg`, where `wippolder` is the case name, `wippolder.gpkg` is the data name.

`<pathspec>`:
Path specifier for the data files to add to the case.
Can be a path to a single file, a directory or a fileglob (e.g. `*.gpkg`).
Can be passed multiple times.
Only local files are supported.

`-y`: 
Do not require confirmation for updating existing values or files.

`--license=<text>`: 
A license to add to the data.

`--description=<text>`: 
A description to add to the case or data.

`--format=<format>`: 
A format to force on the data in case it cannot be inferred automatically, or the inferred format is not correct.
If the a whole directory is added as a single data entry with `--as-data`, the automatic format inference doesn't work, and it may be necessary to force a format.
Note that when the format is forced, the bounding box calculation and hashing does not work.

`--as-data`:
Add a whole directory as a single data entry.
The default behaviour is to add each file in the directory as a separate data entry.
If `--as-data` is set, the bounding box and file hash cannot be computed for the data.

**Examples**

Add multiple files as data entries to a case.
If the case does not exist, it will be created as `case-name` and the file `file-name` is moved into it.

```shell
geodepot add /path/to/file-name1 /path/to/file-name2 case-name
```

Update the license and description of a data entry (`file-name`) in a case (`case-name`).

```shell
geodepot add --description "long description\nmultiline" --license "CC-0" case-name/file-name1
```

Update the description of a case (`case-name`)

```shell
geodepot add --description "new description of the case" case-name
```

#### remove

**Synopsis**

```shell
geodepot remove [-y] [<casespec>...]
```

**Description**

Delete a case or a data entry from the repository.

**Options**

`<casespec>`:
Case (and data) specifier, in the form of `case-name[/data-name]`.
Can be specified multiple times.
Providing the case name `case-name` is mandatory, the data name `data-name` within the case is optional.
The rest of the options will affect the specified level, either the whole case with `case-name`, or just a single data within the case with `case-name/data-name`.
For example, `wippolder/wippolder.gpkg`, where `wippolder` is the case name, `wippolder.gpkg` is the data name.

`-y`: 
Do not require confirmation for deleting the entries.

#### pull

Downloads any changes from the remote repository, overwriting the local version.
Without arguments, it checks and downloads all cases if needed. 
With the case ID as argument, `geodepot pull <case-id>`, it only checks and downloads the specified case.

#### push

Uploads any local changes to the remote repository, overwriting the remote version.
If the remote contains a changed version that is not the previous state of the local, the `push` operation exits without making any changes on the remote.
In this case the `-f, --force` option can forcibly overwrite the remote, even if there are unknown changes.

#### verify

Verify the integrity of the repository, by comparing the stored hashes in the INDEX to the recomputed hash of the corresponding files.
Without arguments, it verifies the local repository.
With the remote name as argument, it verifies the remote repository.

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

### Configuration

You can specify Geodepot configuration settings with the `geodepot config` command.
Geodepot looks for configuration values on two levels, global and local.

Geodepot first looks for the configuration in the `~/.geodepotconfig.json` file, which is specific to each user.
You can make Geodepot read and write to this file by passing the `--global` option.

Secondly, Geodepot looks for configuration values in the configuration file in the Geodepot directory (`.geodepot/config.json`) of whatever repository you are currently using.
These values are specific to that single repository and they are read and written by passing the `--local` option.
This is the default option of the `geodepot config` command.

The local level config overwrites the values of the global level config.

Reference: [Git Configuration](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration)

### The INDEX

The INDEX contains the overview of all *cases* and *data files* in the repository.
For each *data file*, the INDEX stores:

| Field            | Type    | Description                                                                                       |
|:-----------------|:--------|:--------------------------------------------------------------------------------------------------|
| id               | uint    | Auto-generated, sequential data identifier.                                                       |
| case_id          | string  | User provided case identifier. Must be unique, contain only alphanumeric characters and/or `-,_`. |
| case_description | string  | User provided case description. Long text, can be multiline. Maybe contain markdown?              |
| case_sha1        | string  | SHA-1 hash of the zip-compressed case.                                                            |
| case_changed_by  | string  | The user that made the last change to the case.                                                   |
| file_name        | string  | Data file name, including extensions.                                                             |
| file_sha1        | string  | SHA-1 hash of the data file.                                                                      |
| file_format      | string  | Data format.                                                                                      |
| file_license     | string  | User provided license abbreviation or link to a license.                                          |
| bbox             | Polygon | The bounding polygon of the data file extent.                                                     |

Maybe Flatgeobuff to be queriable without a server.
However, Flatgeobuff requires extra libraries for parsing.
A standard-compliant GeoJSON seems like a better option, because it is easily parsable in any language and it can be visualised by almost every GIS application.
Since I expect that may only contain a few tens of data files, maybe a hundred in extreme cases, there is no need for a high performance format.

More importantly, QGIS cannot use SFTP to retrieve a file, only HTTP/HTTPS/FTP.
Unless the remote repository is published through a webserver, we cannot load the remote INDEX directly to QGIS.
The repository needs to be cloned first.

#### BBox

The BBox is in a global CRS, e.g. EPSG:3857, so that in can be visualised easily in any web viewer.
The data files can be in different CRS-es, even within one case, therefore, their BBox is reprojected into the common CRS and added to the INDEX.

The BBox is optional.
It is possible that the BBox cannot be computed, or the data doesn't have coordinates.
It maybe possible to manually provide a single point of reference.

**Dutch baselayer global CRS availability**

| Dataset        | EPSG:3857 | EPSG:4326 | CRS:84 |
|:---------------|:---------:|:---------:|:------:|
| TOP10NL        |     x     |           |        |
| BAG            |     x     |     x     |   x    |
| BGT            |     x     |           |        |
| Luchtfoto      |     x     |     x     |        |
| OpenBasisKaart |     x     |           |        |
| BRO            |     x     |     x     |   x    |
| CBS datasets   |     x     |     x     |   x    |
| NWB            |     x     |     x     |   x    |

### Conflict resolution

Conflicts between the local and remote repository are resolved according to the selected operation.
The [pull](#pull) command overwrites the local with the contents of the remote repository.
The [push](#push) command overwrites the remote with the content of the local repository.

#### diff

The data structure of diff:

```
local-casespec  remote-casespec new|delete|modify   changed-by  [member]    [local-value]   [remote-value]

# New case
null    case-B  new user1

# Deleted case
case-C  null    delete  user2

# New data entry
case-A/null case-A/data-B   new user1

# Deleted data entry
case-A/data-C   case-A/null delete  user2

# Modified case
case-A  case-A  modify  user2   description value_local value_remote

# Modified data entry
case-A/data-A   case-A/data-A   modify  user1   license value_local value_remote
case-A/data-A   case-A/data-A   modify  user1   format value_local value_remote
case-A/data-A   case-A/data-A   modify  user1   extent_original_srs wkt_original_local wkt_original_remote
```

The formatted output of diff:

```shell
# New case
new case case-B
--- local/null
+++ remote/case-B

# Deleted case
deleted case case-C
--- local/case-C
--- remote/null

# New data entry
new data case-A/data-B
--- local/case-A/null
+++ remote/case-A/data-B

# Deleted data entry
deleted data case-A/data-C
--- local/case-A/data-C
+++ remote/case-A/null

# Case description has changed
--- local/case-A
+++ remote/case-A

-description=value_old
+description=value_new

# Data entry has changed
--- local/case-A/data-A
+++ remote/case-A/data-A

-license=value_old
+license=value_new

-format=value_old
+format=value_new

-extent_original_srs=wkt_original_old
+extent_original_srs=wkt_original_new
```

#### push 

The scenarios below describe the change of a specific case.
Pushing the repository follows the same steps, just it does so for each case in sequence.

**A. Remote has not changed**

User makes local changes and wants to update the remote.
The local INDEX contains the hash of the last update (push/pull).
User issues `push <case-id>`, then:
1. Check if the remote is locked. If not, then continue.
2. Place a LOCK on the remote, with information on who owns the lock. This prevents that the remote is updated by someone else, while the User uploads the changes.
3. Compress the changed case into a temp directory/file.
4. Compute SHA-1 of zip file.
5. Compare the case's local data hash in the INDEX with the remote data hash in the INDEX. Maybe compare the whole INDEX? Because not on the data files can change, but also the description, license. 
6. If there is no difference, that means that the remote hasn't changed since the local changes were made and it is safe to overwrite the remote with the local changes.
7. Overwrite the case's hash in remote INDEX with the hash of the new zipped case on the local.
8. Upload the local zip to the remote and overwrite the remote case with it.
9. Remove the LOCK from the remote.

**B. Remote is being updated**

User makes local changes and wants to update the remote.
The local INDEX contains the hash of the last update (push/pull).
User issues `push <case-id>`, then:
1. Check if the remote is locked. If yes, then stop and display who owns the lock, tell the User to try again later.

**C. Remote has changed**

User makes local changes and wants to update the remote.
The local INDEX contains the hash of the last update (push/pull).
User issues `push <case-id>`, then:
1. Check if the remote is locked. If not, then continue.
2. Place a LOCK on the remote, with information on who owns the lock. This prevents that the remote is updated by someone else, while the User uploads the changes.
3. Compress the changed case into a temp directory/file.
4. Compute SHA-1 of zip file.
5. Compare the case's local INDEX hash with the remote INDEX hash.
6. If there is a difference, that means that the remote has changed since the last pull. This situation cannot be resolved automatically, because geodepot cannot merge data files. The `push` stops and displays who made the last change, the path to the new temp-archive and tells to User to contact the last-changer to resolve the conflict.
7. Remove the LOCK from the remote.

#### pull

Firstly, the repository integrity is verified ([verify](#verify-remote)).
If there are changed cases that haven't been pushed...
The `pull` operation also places a LOCK on the remote, to prevent it from change during the download.
Once the download is complete, the LOCK is removed.



### Data files

Data is in *.zip*. 
There is no custom format, just plain GIS formats zipped. 
2D vector formats are thus GDAL-readable from within the *.zip*.

When data is added, its BBox is computed from the data or header.

#### Data format detection

Try GDAL, PDAL, see what gives.
Some of them are custom implemented, for instance, the extensions `.city.json` refers to the `CityJSON` format, the extension `.city.jsonl` refers to the `CityJSONSequence` format.
3DTiles is similar, because the `tileset.json` or the `.gltf/.b3dm` files refer to the `Cesium 3DTiles` format.

### Repository layout

The geodepot repository is stored in a `.geodepot` directory, at the root directory of a project.
In the example below, `wippolder` is a case ID.

```
.geodepot/
├── cases
│   ├── wippolder
│   │   ├── wippolder.gpkg
│   │   └── wippolder.las
│   └── wippolder.zip
├── index.geojson
├── config.json
└── snapshots
```

The zip-compressed cases are stored along with the uncompressed version, so that pulling a case or repository is as fast as possible and it does not involve other operations on the remote than transferring the file.
When the archive is downloaded, it is extracted into the same directory and the archive is retained.
When a data file is retrieved from a case with `get`, the file path points to the uncompressed case.
Although, retaining the archives increases the space consumption significantly, I expect that the data files are relatively small so in total the space consumption will remain acceptable and the benefits of having the archives ready for download will outweigh the space costs.

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

The installer script,
- downloads the latest release,
- moves it to the correct location, replacing the previous version,
- updates the PATH to include the exe if needed,
- create the global geodepot User on the machine if needed.

## Notes

I was assuming that a data file is a single file, but what if a data file is a directory of files? Like 3DTiles or a Shapefile?

ssh://gilfoyle/data/work/bdukai/geodepot/.geodepot/index.geojson

Probably OO would be neat, like having a `Case` and `CaseCollection` (serialised to the INDEX) with their methods.

https://github.com/ArthurSonzogni/FTXUI
https://textual.textualize.io/

A case can contain any number of files. If `geodepot.get_case(case-id)` returns the path to the case, then the required file name still needs to be appended to the case-path.
How do I know what data files are in a case?
With `geodepot show <case-id>`.

Hash of the archive is required, for checking if new version needs to be downloaded.
Mimic cmake's fetchcontent.

git lfs could be sth to use, but maybe overkill because need to set up and operate a remote server. Would be better not to use any server.

## TODOs

- Sanitize serialize/write_to_file etc.
- Check again that driver detection works
- Test with adding `pickle`
- Add option for providing bbox to `add`
- Add driver to index
- Find out diver from format
- Try building wheels for the deps, so that geodepot is pip-installable
- Read license from a file
- Optimizations:
  - ~~import only the used functions~~
  - generators, list comprehension
  - flatten nested conditionals
  - choose tuple over list
- Improve repository discovery so that the project repository is found even from subdirectories. See how Git does it with [`GIT_DIR` et al.](https://git-scm.com/book/en/v2/Git-Internals-Environment-Variables).
- Robust CityJSONSeq import, so that the metadata can be a separate file.



