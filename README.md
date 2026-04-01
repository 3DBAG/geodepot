# Geodepot – Test data storage system for geospatial data

Geodepot helps to organize data into test cases, share them and provide integration to some of the test frameworks for ease of use.
It was born from our own requirement from writing spatial data processing tools over the past years.

## Documentation

https://innovation.3dbag.nl/geodepot

## Installation

### Quick install

The release installer downloads the correct bundle for the current platform, verifies the published checksum, and installs a small wrapper on `PATH`.

Linux and macOS:

```shell
curl -fsSL https://github.com/3DBAG/geodepot/releases/latest/download/geodepot-install.sh | sh
```

Windows PowerShell:

```powershell
Invoke-RestMethod https://github.com/3DBAG/geodepot/releases/latest/download/geodepot-install.ps1 | Invoke-Expression
```

The installers also support `--version` for installing a specific tag.

### Manual install

Download a release bundle from the [latest release](https://github.com/3DBAG/geodepot/releases/latest), extract it, and keep the extracted directory intact.

The release bundle contains a relocatable runtime environment in `env/` plus a small launcher at the top level.

Linux and macOS:

```text
geodepot/
├── geodepot
└── env/
```

Windows:

```text
geodepot/
├── geodepot.cmd
├── geodepot.ps1
└── env/
```

Run the top-level launcher, not the nested executable in `env/`.
The launcher activates the bundled GDAL, PROJ, and PDAL runtime before starting Geodepot.

- Linux and macOS: `./geodepot`
- Windows: `.\geodepot.cmd`

If you want to use Geodepot from anywhere, add the extracted `geodepot` directory itself to `PATH`.
Do not symlink or copy the launcher out of that directory, because it locates the bundled runtime relative to its own path.

Geodepot has complex native dependencies, so do not `pip install` it unless you are developing Geodepot itself.

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
