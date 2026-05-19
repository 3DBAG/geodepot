set shell := ["bash", "-uc"]
set dotenv-load := true

compose := env_var_or_default("GEODEPOT_COMPOSE", "docker compose")

_default:
    @just --list

lint:
    pixi run -e dev lint

format:
    pixi run -e dev format

format-check:
    pixi run -e dev format-check

test:
    pixi run -e dev test

test-integration:
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
    SSH_PUBLIC_KEY="$({ cat tests/data/mock_user_home/.ssh/id_rsa.pub 2>/dev/null || cat ~/.ssh/id_rsa.pub; } | head -n 1)" {{compose}} -f docker/docker-compose.yaml up --build --force-recreate -d

down:
    {{compose}} -f docker/docker-compose.yaml down --volumes --remove-orphans
