# Developing Geodepot

This page covers setting up a development environment, running tests, and the release process.

## Prerequisites

- [Pixi](https://pixi.sh/) for environment and dependency management
- [just](https://just.systems/) as the task runner (thin wrapper around `pixi run`)
- Docker or Podman (for integration tests)
- Git

## Quickstart

Set up the local development environment:

```shell
git clone https://github.com/3DGI/geodepot.git
cd geodepot
cp .env.example .env
pixi install -e dev
just download-data
just test
```

The default `.env.example` comments assume Docker. If you use rootless Podman,
edit `.env` and enable:

```shell
GEODEPOT_COMPOSE="podman compose"
GEODEPOT_CONTAINER_SOCKET="${XDG_RUNTIME_DIR}/podman/podman.sock"
```

All development tasks are run through `just`. `just` automatically loads the
repo-local `.env` file:

```shell
just lint          # Lint code with ruff
just format        # Auto-format code with ruff
just format-check  # Check formatting without modifying
just test          # Run unit tests with pytest
just integration-test  # Run container-backed integration tests
just docs-build    # Build mkdocs locally
just docs-deploy   # Deploy docs to GitHub Pages
```

To run specific tests:

```shell
pixi run -e dev pytest tests/test_repository.py  # Specific file
pixi run -e dev pytest -k test_name              # Tests matching pattern
pixi run -e dev pytest -v                        # Verbose output
```

## Test Data

Test data must be downloaded before running tests:

```shell
just download-data
```

This populates `tests/data/` with spatial datasets used by the test suite.

## Integration Tests

Integration tests use a containerized test server that provides HTTP and SSH endpoints.
The default unit suite excludes these tests; run them explicitly with:

```shell
just integration-test
```

The test server exposes:

- **HTTP**: `http://localhost:8080/geodepot` (pull/fetch operations)
- **SSH/SFTP**: `ssh://root@localhost:2222:/srv/geodepot` (push operations)

The recipes use the compose command configured in `.env`:

- Docker: `GEODEPOT_COMPOSE="docker compose"` or leave it unset
- Podman: `GEODEPOT_COMPOSE="podman compose"`

When running from a devcontainer, the devcontainer talks to the host container
engine through a Docker-compatible socket. Set `GEODEPOT_CONTAINER_SOCKET` in
`.env`, then launch the IDE from a shell that exports those values before
creating or rebuilding the devcontainer:

```shell
set -a
. ./.env
set +a
pycharm .
```

The devcontainer mounts that socket as `/var/run/docker.sock` and uses the
Docker CLI/Compose plugin as the common client. For rootless Podman-backed
devcontainers, the configuration also uses `--userns=keep-id` so bind-mounted
workspace files remain writable by the `vscode` user.

## Branch Strategy

The project uses a two-branch model:

- **`develop`** — active development; all feature branches merge here
- **`main`** — stable releases only; receives merges from `develop` at release time

## Release Process

Releases are fully automated through three GitHub Actions workflows that chain together:

```text
workflow_dispatch (on develop)
  └─ release-prepare.yaml
       ├─ bumps version in pyproject.toml and flake.nix
       ├─ updates CHANGELOG with version and date
       ├─ regenerates pixi.lock
       ├─ commits and pushes to develop
       └─ opens PR: develop → main

[maintainer reviews and merges PR]
  └─ release-tag.yaml (fires on PR merge to main)
       └─ creates and pushes git tag (e.g. 1.0.5)

[tag push triggers]
  └─ package-release.yaml
       ├─ runs lint, format check, tests
       ├─ builds pixi bundles for Linux, macOS, Windows
       ├─ runs smoke tests on each platform
       └─ creates GitHub release with artifacts
```

### Step by Step

1. **Trigger the release.** Go to Actions > "Prepare Release" > Run workflow.
   Select the branch `develop` and the bump type (`patch`, `minor`, or `major`).

2. **Review the PR.** The workflow opens a PR from `develop` to `main` titled
   "Release vX.Y.Z". Verify the version bump, CHANGELOG entry, and that
   `pixi.lock` is updated.

3. **Merge the PR.** Once merged, `release-tag.yaml` automatically creates the
   git tag on `main` and pushes it.

4. **Release builds.** The tag push triggers `package-release.yaml`, which builds
   release bundles on all three platforms and creates a GitHub release.

### Required Setup: `RELEASE_TOKEN` Secret

Tags pushed with the default `GITHUB_TOKEN` do not trigger downstream workflows
(this is a GitHub Actions safety measure to prevent infinite loops). The
`release-tag.yaml` workflow therefore uses a Personal Access Token stored as the
repository secret `RELEASE_TOKEN`.

To create it:

1. Go to GitHub **Settings > Developer settings > Personal access tokens > Fine-grained tokens**.
2. Create a token scoped to the `3DBAG/geodepot` repository with **Contents: Read and write** permission.
3. Add it as a repository secret at **Settings > Secrets and variables > Actions**, named `RELEASE_TOKEN`.

### Version Management

Versions are managed by [bumpver](https://github.com/mbarkhau/bumpver),
configured in `pyproject.toml`:

```toml
[tool.bumpver]
current_version = "1.0.4"
version_pattern = "MAJOR.MINOR.PATCH"
commit = true
tag = false    # tagging is handled by release-tag.yaml
push = false   # pushing is handled by the workflow
```

The version string appears in two places in `pyproject.toml` (`[project]` and
`[tool.pixi.package]`) plus once in `flake.nix`, and bumpver updates all three
automatically.

!!! warning "pixi.lock must stay in sync"

    The `pixi.lock` file embeds the local package version. If you bump the
    version in `pyproject.toml` without regenerating the lock file, CI will fail
    because `setup-pixi` runs with `locked: true`. The release workflow handles
    this automatically by running `pixi lock` after the version bump. If you
    bump the version manually, always run `pixi lock` afterward and commit the
    updated lock file.

### CHANGELOG

The `CHANGELOG` file follows a [Keep a Changelog](https://keepachangelog.com/)
style. During development, add entries under the `## [Unreleased]` section. The
release workflow automatically inserts a dated version header:

```text
## [Unreleased]

## [1.0.5] - 2026-04-01

- Previously unreleased changes appear here...
```
