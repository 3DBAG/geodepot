# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Geodepot is a test data storage system for geospatial data. It helps organize data into test cases, share them, and provide integration with test frameworks. The main interface is a CLI tool built with Click.

**Requirements**: Python 3.12+

**Source code**: All source code is in `src/geodepot/`

Key concepts:
- **Repository**: A collection of related test cases stored in a `.geodepot/` directory
- **Case**: A container with one or more data items, identified by name
- **Data**: The actual files/directories containing test data (GeoPackage, GeoJSON, LAS/LAZ, CityJSON, etc.)
- **Index**: GeoJSON file (`index.geojson`) storing metadata about all cases
- **Remote**: A server URL (HTTP or SSH/SFTP) for pushing/pulling repositories
- **CaseSpec**: A `case_name/data_name` string that uniquely identifies a data item (e.g. `wippolder/wippolder.gpkg`). Can reference just a case with `case_name` alone

## Common Development Commands

Use `just` as the single entry point for all development tasks (it wraps `pixi run`).

### Setup
```bash
just lint               # Lint code with ruff
just format             # Auto-format code with ruff
just format-check       # Check code formatting without modifying
just test               # Run all tests with pytest
```

### Testing
```bash
pixi run -e dev pytest tests/test_repository.py  # Run specific test file
pixi run -e dev pytest -k test_name              # Run tests matching pattern
pixi run -e dev pytest -v                        # Verbose output
```

### Data Management
```bash
just download-data      # Download test data from remote server
just upload-data        # Upload test data to remote server
```

### Documentation
```bash
just docs-build         # Build mkdocs locally
just docs-deploy        # Deploy docs to GitHub Pages
```

### Integration Test Server
```bash
just up    # Start Docker-based test server (nginx + sshd)
just down  # Stop test server
```

The test server provides:
- **HTTP**: `http://localhost:8080/geodepot` for pull/fetch operations
- **SSH/SFTP**: `ssh://root@localhost:2222:/srv/geodepot` for push operations (pubkey auth via `~/.ssh/id_rsa.pub`)

## Architecture Notes

### Main Modules

- **`cli.py`**: Click-based CLI implementation
- **`repository.py`**: Core `Repository` class managing local repo state and sync operations
- **`data.py`**: Data item metadata and format/bbox detection
- **`case.py`**: Case and CaseSpec dataclasses
- **`config.py`**: Configuration and remote management
- **`errors.py`**: Custom exception types
- **`encode.py`**: JSON serialization helpers

### CLI Layer (`cli.py`)

- **Command groups**: `geodepot_grp` (main), `config_grp` (configuration), `remote_grp` (remote management)
- **Top-level commands**:
  - `init [URL]`: Initialize local repo; optionally clone from remote
  - `add CASESPEC [PATHS...]`: Add data to a case
  - `remove CASESPEC`: Delete a case or data item
  - `list`: Show all cases and their data items
  - `show CASESPEC`: Display details of a case or data item
  - `get CASESPEC`: Return full local path to a data item
  - `fetch REMOTE`: Check remote for changes (without applying them)
  - `push REMOTE`: Upload local changes to remote (requires confirmation)
  - `pull REMOTE`: Download remote changes to local (requires confirmation)
- All commands instantiate `Repository()` via `get_repository(ctx)` which reads from current working directory

### Repository (`repository.py`)

- **Core class**: `Repository` handles all operations (init, add, remove, list, push, pull)
- **Local layout**: `.geodepot/` contains `index.geojson`, `config.json`, and `cases/<case>/<data>/`
- **Index structure**: GeoJSON file where each feature represents a case; properties store metadata
- **Bbox handling**: Stored in EPSG:3857 (Web Mercator) in index, original SRS preserved as `data_extent_original_srs`
- **Diff tracking**: `IndexDiff` and `Status` enum (ADD, DELETE, MODIFY, ADD_OR_DELETE) track changes between local and remote
- **Push/pull workflow**: 
  1. `fetch()` downloads remote index and compares with local
  2. Differences formatted for user review
  3. User confirms or aborts
  4. `push()` or `pull()` executes the sync

### Data Handling (`data.py`)

- **Metadata**: `Data` dataclass stores name, format, driver, sha1, bbox, license, description, and changed_by user
- **Format detection**: Automatic probing in order: CityJSON (by extension) → OGR (vector) → GDAL (raster) → PDAL (point cloud)
  - Probes file extension and attempts driver-specific reads
  - Override with `--format` flag when auto-detection fails or is incorrect
- **Bounding box**: `BBoxSRS` dataclass stores both original SRS bbox and EPSG:3857 bbox
- **Index serialization**: `Data.from_ogr_feature()` deserializes from GeoJSON features

### Case (`case.py`)

- **Structure**: `Case` dataclass holds name, description, sha1, dict of `Data` items, and `changed_by` user
- **Identification**: `CaseSpec` represents `case_name` or `case_name/data_name`; parsed from standard `case/data` strings
- Each case is a directory under `.geodepot/cases/`

### Configuration (`config.py`)

- **Global config**: `~/.geodepotconfig.json` stores user info (name, email)
- **Local config**: `.geodepot/config.json` stores remotes and local overrides
- **Config merge**: Local values override global; enables per-project configuration
- **Remote URLs**:
  - **HTTP(S)**: Standard URL (e.g., `https://example.com/geodepot`)
  - **SSH/SFTP**: `ssh://user@host:/path` or `sftp://user@host:/path`
  - Parsed in `Remote.__post_init__()` to extract host, user, and path

## Error Handling

Custom exception types (defined in `errors.py`) mark important architectural boundaries:

- **`GeodepotRuntimeError`**: General operational failures (e.g., invalid data, file I/O issues)
- **`GeodepotInvalidRepository`**: Repository is missing or malformed (e.g., no `.geodepot/` directory or corrupt index)
- **`GeodepotInvalidConfiguration`**: Config file format or value errors
- **`GeodepotIndexError`**: Failed to read or write the index file
- **`GeodepotDataError`**: Data processing failed (format detection, bbox computation, serialization)
- **`GeodepotSyncError`**: Push or pull operation failed (remote unreachable, conflict, transfer error)

CLI commands catch `GeodepotInvalidRepository` and exit with an error message; `GeodepotSyncError` is caught and logged during push/pull operations.

## Key Dependencies

- **geospatial**: GDAL 3.9, PDAL 3.4 (conda-forge via pixi)
- **CLI**: Click 8.1
- **networking**: requests 2.32, fabric 3.2 (for SSH/SFTP)
- **package management**: pixi for conda + PyPI dependencies
- **testing**: pytest, ruff for linting/formatting
- **docs**: mkdocs, mkdocs-material
- **CI**: GitHub Actions on Windows, macOS, Linux with conda environment

## Testing Strategy

- **Unit tests**: Test individual components using `mock_user_home` and `mock_temp_project` fixtures
- **Integration tests**: `test_repository_collaboration.py` tests push/pull conflicts via Docker test server
- **Fixtures**: `conftest.py` monkeypatches `Path.home()` and `Path.cwd()`, sets `PROJ_LIB` env var
- **Test data**: Downloaded into `tests/data/` via `just download-data`; includes `wippolder.gpkg` and similar spatial datasets

## Important Details

1. **Not a Version Control System**: Geodepot is NOT a DVC/Git-LFS replacement. Data is assumed to exist elsewhere and stay available in some other form (e.g., original source servers). Repositories can be safely discarded and recreated with moderate effort because only the latest state is retained, not history.

2. **Index as GeoJSON**: The index stores all case metadata as a single GeoJSON file. Each feature represents a case, with properties containing data items and their metadata. This allows geographic queries and tool integration but limits scale to what fits in memory.

3. **Bbox in EPSG:3857**: Bounding boxes are stored in Web Mercator (EPSG:3857) for consistent index representation, but original SRS information is preserved in `data_extent_original_srs` and `srs_wkt` properties so original coordinates can be recovered.

4. **User Tracking**: Every case and data item includes `changed_by` user info (name + email from `~/.geodepotconfig.json`). During push/pull, conflicts are detected when the same item was modified by different users, which informs the sync workflow.

5. **Format Detection & Override**: Format detection probes CityJSON → OGR → GDAL → PDAL in order, using file extension + driver-specific tests. When auto-detection fails or is incorrect, the `--format` flag forces a driver; this skips bbox computation since SRS may be unknown.

6. **CaseSpec Parsing**: The `case_name/data_name` format is parsed throughout the codebase using `CaseSpec.from_str()`. Can reference just a case (no bbox, one feature per case) or a specific data item. Used in CLI commands and index lookups.

7. **Configuration Hierarchy**: 
   - Global: `~/.geodepotconfig.json` (shared across all projects; usually just user info)
   - Local: `.geodepot/config.json` (project-specific; remotes and overrides)
   - Local values always override global values during merge

## Design Document

See `design-doc.md` for detailed problem statement, design rationale, high-level concepts, and workflow examples.
