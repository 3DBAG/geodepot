# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Geodepot is a test data storage system for geospatial data. It helps organize data into test cases, share them, and provide integration with test frameworks. The main interface is a CLI tool built with Click.

Key concepts:
- **Repository**: A collection of related test cases stored in a `.geodepot/` directory
- **Case**: A container with one or more data items, identified by name
- **Data**: The actual files/directories containing test data (GeoPackage, GeoJSON, LAS/LAZ, CityJSON, etc.)
- **Index**: GeoJSON file (`index.geojson`) storing metadata about all cases
- **Remote**: A server URL for pushing/pulling repositories
- **CaseSpec**: A `case_name/data_name` string that identifies a case or data item (e.g. `wippolder/wippolder.gpkg`)

## Common Development Commands

### Setup
```bash
pixi install          # Install default environment
pixi install -e dev   # Install dev environment (includes pytest, ruff, etc.)
```

### Testing
```bash
pixi run -e dev pytest                          # Run all tests
pixi run -e dev pytest tests/test_repository.py # Run specific test file
pixi run -e dev pytest -k test_name             # Run tests matching pattern
pixi run -e dev pytest -v                       # Verbose output
```

### Code Quality
```bash
pixi run ruff check         # Lint code
pixi run ruff format --check # Check code formatting
pixi run ruff format         # Auto-format code
```

### Data Management
```bash
just download-data      # Download test data from remote server
just upload-data        # Upload test data to remote server
```

### Integration Test Server
```bash
just up    # Start Docker-based test server (nginx + sshd)
just down  # Stop test server
```

The test server provides:
- **HTTP**: `http://localhost:8080/geodepot` for pull operations
- **SSH**: `ssh://root@localhost:2222:/srv/geodepot` for push operations (pubkey auth via `~/.ssh/id_rsa.pub`)

## Architecture Notes

**CLI Layer** (`cli.py`):
- Command groups: `geodepot_grp`, `config_grp`, `remote_grp`
- Commands: `init`, `add`, `remove`, `list`, `show`, `get`, `fetch`, `push`, `pull`, `config`, `remote`
- All commands call `get_repository(ctx)` which instantiates `Repository()` from `cwd`

**Repository** (`repository.py`):
- `Repository` class is the core; handles initialize, add, remove, list, index management, push/pull
- Local repo lives in `.geodepot/` with: `index.geojson`, `config.json`, `cases/<case>/<data>`
- Index (GeoJSON) stores case/data metadata as feature properties; bboxes in EPSG:3857
- `IndexDiff` / `Status` enum track conflicts when comparing local vs. remote index during push/pull
- Push/pull flow: `fetch()` → compute diffs → user confirms → `push()`/`pull()` executes

**Data Handling** (`data.py`):
- `Data` dataclass holds metadata (name, format, driver, sha1, bbox, license, description, changed_by)
- Format detection order: CityJSON → OGR → GDAL → PDAL; uses file extension + driver probing
- `BBoxSRS` stores bounding box in both original SRS and EPSG:3857 for the index
- `Data.from_ogr_feature()` deserializes from the GeoJSON index

**Case** (`case.py`):
- `Case` dataclass holds name, description, sha1, dict of `Data` items, and `changed_by` user
- `CaseSpec` is a `(case_name, data_name)` pair parsed from `case_name/data_name` strings

**Configuration** (`config.py`):
- Global config: `~/.geodepotconfig.json` (user info)
- Local config: `.geodepot/config.json` (remotes, overrides global)
- `Remote` supports HTTP and SSH/SFTP URLs; SSH format: `ssh://user@host:/path`
- Config merge: local values override global values

## Key Dependencies

- **geospatial**: GDAL 3.9, PDAL 3.4 (conda-forge via pixi), click, requests, fabric
- **package management**: pixi for conda + PyPI dependencies
- **CI**: GitHub Actions on Windows, macOS, Linux with conda environment

## Testing Strategy

- **Unit tests**: Test individual components using `mock_user_home` and `mock_temp_project` fixtures
- **Integration tests**: `test_repository_collaboration.py` tests push/pull conflicts via Docker test server
- **Fixtures**: `conftest.py` monkeypatches `Path.home()` and `Path.cwd()`, sets `PROJ_LIB` env var
- **Test data**: Downloaded into `tests/data/` via `just download-data`; includes `wippolder.gpkg` and similar spatial datasets

## Important Details

1. **No Version Control for Data**: Geodepot is NOT a DVC/Git-LFS replacement. Data is assumed to exist elsewhere; repositories can be safely discarded and recreated.
2. **Index Format**: Uses GeoJSON with EPSG:3857 (Web Mercator) as standard CRS for bbox storage, but original CRS is preserved in `data_extent_original_srs`.
3. **User Identification**: All changes tracked with user info; pull/push can detect conflicts when the same case was modified by different users.
4. **Format Detection**: Automatic via file extension + driver probing; override with `--format` flag (disables bbox computation).

## Design Document

See `design-doc.md` for detailed problem statement, design rationale, high-level concepts, and workflow examples.
