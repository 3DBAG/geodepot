# Geodepot – Test data storage system for geospatial data

Geodepot helps to organize data into test cases, share them and provide integration to some of the test frameworks for ease of use.
It was born from our own requirement from writing spatial data processing tools over the past years.

## Documentation

https://innovation.3dbag.nl/geodepot

## Interfaces

### Command-line tool (CLI)

The main interface, it supports all operations.

Repository (the current repo): https://github.com/3DBAG/geodepot

### API

The API is meant for passing data paths to tests, nothing else.
The rest of the operations are done through the CLI.

The API is available in:

- C++ (implementation)
- Python (binding)
- CMake (binding)

Repository: https://github.com/3DBAG/geodepot-api

## Example

The minimal example below gives and idea of how Geodepot works.

Initialize an empty repository in the current working directory.

```shell
geodepot init
```

Add some data to this repository.
The GeoPackage file `path/to/local/wippolder.gpkg` is added to the case `wippolder` with the name `wippolder.gpkg`, and the provided license and description are attached to the data entry.

```shell
geodepot add \
  --license CC0 \
  --description "A couple of buildings and a church in Delft for minimal testing." \
  wippolder \
  path/to/local/wippolder.gpkg
```

When writing a test, use one of the API functions to get the full path to the data.

Alternatively, you can also use the CLI to get the data path.

```shell
geodepot get wippolder/wippolder.gpkg
```

## What Geodepot is not

Geodepot is not a version control system, neither for data nor for code.
It is assumed that the data that you store in a Geodepot repository is already available, and will stay available in some other form.
Thus, if the repository is accidentally overwritten with unwanted changes, the desired state can be recreated with some effort.
That is, because the history of the repository is not retained, only the latest version is available at any time.

## Roadmap

The current version (`1`) is considered to be feature complete, and there are no major enhancements planned.
This does not mean however, that the current version is bug free.
The ongoing development focuses on fixing bugs reported by users or discovered during testing.

## 3DBAG organisation

This software is part of the 3DBAG project. For more information visit the [3DBAG organisation](https://github.com/3DBAG).
