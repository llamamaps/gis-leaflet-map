#!/bin/bash

echo "Updating docker-compose.yml with correct volume..."
sed -i "s#REPO_DIR#$PWD#" docker-compose.yml

echo "Cloning osm-styles geoserver data_dir..."
git clone https://github.com/geosolutions-it/osm-styles.git

echo "Starting docker services postgres, geoserver, nginx"
docker compose up -d

tries=0
echo "Testing to see if postgresql is running..."
until psql -c "select 1" > /dev/null
do
    "postgresql is not running yet. sleeping 5..."
    sleep 5
    tries=$(expr $tries + 1)
    if [ $tries -gt 12 ]; then
        echo postgresql does not seem to be running
        exit 1
    fi
done
echo "postgresql is running..."

echo "Creating the OSM database and enabling extensions..."
psql -U postgres -c "CREATE DATABASE hawaii"
psql -U postgres -d hawaii -c "CREATE EXTENSION postgis"
psql -U postgres -d hawaii -c "CREATE EXTENSION hstore"

echo "Downloading pbf..."
curl -L -O https://download.geofabrik.de/north-america/us/hawaii-latest.osm.pbf -o hawaii-latest.osm.pbf

echo "Importing pbf into postgresql..."
/opt/imposm/imposm-0.11.1-linux-x86-64/imposm import -mapping osm-styles/imposm/mapping.yml -read hawaii-latest.osm.pbf -overwritecache -write -connection postgis://postgres:postgres@localhost/hawaii

echo "removing hawaii-latest.osm.pbf"
rm hawaii-latest.osm.pbf
