server := "3dgi-server"

_default:
    @just --list

download-data:
    wget https://data.3dgi.xyz/geodepot-test-data/data.zip
    unzip -o data.zip
    rm data.zip

upload-data:
    zip -r -9 data.zip tests/data
    rsync data.zip {{server}}:/var/www/3dgi-data/geodepot-test-data
    rm data.zip

up:
    SSH_PUBLIC_KEY="$(cat ~/.ssh/id_rsa.pub)" docker compose -f docker/docker-compose.yaml up -d

down:
    docker compose -f docker/docker-compose.yaml down