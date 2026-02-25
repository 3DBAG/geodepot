# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Geodepot is a test data storage system for geospatial data. It helps organize data into test cases, share them, and provide integration with test frameworks. The main interface is a CLI tool built with Click.

Key concepts:
- **Repository**: A collection of related test cases, normally one per project
- **Case**: A container with one or more data items, identified by name
- **Data**: The actual files/directories containing test data (GeoPackage, GeoJSON, LAS/LAZ, CityJSON, etc.)
- **Index**: GeoJSON file (index.geojson) storing metadata about all cases
- **Remote**: A server URL for pushing/pulling repositories
- **User**: Name and email registered in the user's home directory (~/.geodepotconfig.json)

## Project Structure

```
src/geodepot/          # Main package
  __main__.py          # Entry point, delegates to cli.py
  cli.py               # CLI command definitions (Click groups/commands)
  repository.py        # Repository class - core logic for init, add, list, show, get, push, pull, etc.
  case.py              # Case and CaseSpec dataclasses
  data.py              # Data class - handles geospatial data parsing (GDAL/OGR/PDAL/CityJSON)
  config.py            # User and Remote configuration management
  encode.py            # Encoding/compression logic for data transfer
  errors.py            # Custom exception classes
tests/                 # Unit tests with pytest
  conftest.py          # Pytest fixtures for test data and mocking
  test_*.py            # Test modules for each major component
  data/integration/    # Test data for integration tests (server/, client0/, client1/)
docker/                # Docker-based integration test server
  Dockerfile           # Ubuntu 22.04 with nginx + openssh-server
  entrypoint.sh        # Startup script for nginx and sshd
  nginx_server.conf    # Nginx config for serving /srv/geodepot
docker-compose.yml     # Compose definition for test server
docs/                  # MkDocs documentation
design-doc.md          # Detailed design document with concepts and examples
```

## Common Development Commands

### Setup
```bash
pip install -e ".[dev]"  # Install package in editable mode with dev dependencies
```

### Testing
```bash
pytest                   # Run all tests
pytest tests/test_repository.py  # Run specific test file
pytest -v               # Verbose output
pytest -k test_name     # Run tests matching pattern
```

### Code Quality
```bash
ruff check              # Lint code
ruff format --check     # Check code formatting
ruff format             # Auto-format code
```

### Building
```bash
pip install .           # Build and install package
```

### Data Management
```bash
just download-data      # Download test data (uses justfile)
just upload-data        # Upload test data to remote server
```

### Integration Test Server
```bash
just server-up          # Start Docker-based test server (nginx + sshd)
just server-down        # Stop test server
```

The test server provides:
- **HTTP**: `http://localhost:8080/geodepot` for pull operations
- **SSH**: `ssh://root@localhost:2222:/srv/geodepot` for push operations (pubkey auth via `~/.ssh/id_rsa.pub`)

## Architecture Notes

**CLI Layer** (cli.py):
- Organized into command groups: main `geodepot_grp`, `config_grp`, `remote_grp`
- Commands: `init`, `add`, `list`, `show`, `get`, `push`, `pull`, `status`, `config`, `remote`
- Uses Click decorators for options/arguments; passes logger via context object

**Core Logic** (repository.py):
- `Repository` class handles all operations: initialize, add data, list cases, manage index
- Index is stored as GeoJSON with case/data metadata in custom properties
- Uses GDAL/OGR/PDAL to extract spatial metadata (CRS, bounding boxes) from data files
- Stores data in `cases/` directory under repository root
- Supports collaborative workflows: `IndexDiff` tracks conflicts when pushing/pulling from remotes

**Data Handling** (data.py):
- `Data` class represents a single data item with metadata (name, license, description, spatial info)
- Detects format automatically using file extension and GDAL/OGR/PDAL drivers
- Extracts CRS, bounding boxes, and other spatial metadata during initialization
- Supports multiple formats: GeoPackage, Shapefile, GeoJSON, LAS/LAZ, CityJSON, GeoTIFF, etc.

**Configuration** (config.py):
- Two config files: global (~/.geodepotconfig.json) and local (repository config.json)
- Stores user info, remotes, and other settings
- Configuration values override defaults from CLI options

**Test Data**:
- Downloaded into `tests/data/` directory via `just download-data`
- Includes wippolder test dataset (minimal buildings/church in Delft)
- Test fixtures in conftest.py mock file paths and environment variables

## Key Dependencies

- **geospatial**: GDAL, PDAL, click (CLI), requests (remote operations), fabric (SSH)
- **spatial metadata extraction**: Uses GDAL OGR for vectors, PDAL for point clouds
- **CI**: GitHub Actions runs tests on Windows, macOS, Linux with conda environment

## Testing Strategy

- **Unit tests**: Test individual components (repository operations, config, data parsing)
- **Integration tests**: Test collaborative workflows (push/pull conflicts) using Docker test server
- **Fixtures**: Mock user home, project directory, use real test data in tests/data/
- **Test data**: Includes spatial datasets like wippolder.gpkg, various CRS examples

## Integration Test Server

The Docker-based test server (`docker-compose.yml`) provides a lightweight alternative to Vagrant:

- **Service**: Ubuntu 22.04 container running nginx + openssh-server
- **HTTP endpoint**: Serves `/srv/geodepot` on port 8080 for pull operations (directory listing)
- **SSH endpoint**: SSH access on port 2222 for push operations (pubkey auth)
- **Volume mount**: `tests/data/integration/server/` synced to `/srv/geodepot` in container
- **SSH auth**: Automatically injects `~/.ssh/id_rsa.pub` via `SSH_PUBLIC_KEY` environment variable

Start with `just server-up`, connect via `ssh://root@localhost:2222:/srv/geodepot` for pushes.

## Important Details

1. **No Version Control for Data**: Geodepot is NOT a DVC/Git-LFS replacement. Data is assumed to exist elsewhere; repositories can be safely discarded and recreated.
2. **Index Format**: Uses GeoJSON with EPSG:3857 (Web Mercator) as standard CRS for bbox storage, but original CRS is preserved.
3. **User Identification**: All changes tracked with user info; pull/push can detect conflicts when same case modified by different users.
4. **Data Format Detection**: Automatic detection via file extension, but can be overridden with `--format` flag.
5. **Spatial Metadata**: CRS, bounding boxes extracted automatically from data files during `add` operations.

## Design Document

See `design-doc.md` for detailed problem statement, design rationale, high-level concepts, and workflow examples.
