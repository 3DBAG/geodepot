set shell := ["bash", "-uc"]

_default:
    @just --list

# Use `pixi` for project tooling and environment-managed commands.
# These recipes are thin wrappers so `just` remains the single entry point.
lint:
    pixi run -e dev lint

format:
    pixi run -e dev format

format-check:
    pixi run -e dev format-check

test:
    pixi run -e dev test

integration-test:
    just up
    trap 'just down' EXIT; pixi run -e dev integration-test

docs-build:
    pixi run -e dev docs-build

docs-deploy:
    pixi run -e dev docs-deploy

download-data:
    pixi run -e dev download-data

upload-data:
    zip -r -9 data.zip tests/data
    rsync data.zip 3dgi-server:/var/www/3dgi-data/geodepot-test-data
    rm data.zip

up:
    SSH_PUBLIC_KEY="$(cat ~/.ssh/id_rsa.pub)" docker compose -f docker/docker-compose.yaml up -d

down:
    docker compose -f docker/docker-compose.yaml down
