# Getting started

## Installation

```shell
pip install geodepot
```

## First time setup

### Configure your user

The user information helps to identify changes and locks when working with a remote repository.
It consists of a name and an e-mail address and it is stored in the local HOME directory of the user.

```shell
geodepot config --global user.name "My Name"
geodepot config --global user.email "my@email.me"
```

## Initialize a repository

A local Geodepot repository can be created empty, or from an existing remote repository.

Navigate to the project directory where you want to initialize a Geodepot repository.
Normally, this would be the software project directory.

Create an empty repository.

```shell
geodepot init
```

Download and existing repository.
Note that `init` does not download the data items, only the repository index.
The data will be downloaded either by calling `get` the first time, or `pull`-ing the remote repository.

```shell
geodepot init https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot
```

## Manage test cases

### Add data

The GeoPackage file `path/to/local/wippolder.gpkg` is added to the case `wippolder` with the name `wippolder.gpkg`, and the provided license and description are attached to the data entry.
Geodepot tries to retrieve the Spatial Reference System (SRS) and extent from the data and add it to the data item.

```shell
geodepot add \
  --license CC0 \
  --description "A couple of buildings and a church in Delft for minimal testing." \
  wippolder \
  path/to/local/wippolder.gpkg
```

### Update a data item

To update an existing data item, we use the `add` command without passing an input file.

```shell
geodepot add \
  --description "New description." \
  wippolder/wippolder.gpkg
```

### View the repository contents

`geodepot list` prints the available cases and data items in the repository.

```shell
geodepot list
```

Returns:

```shell
wippolder
        /wippolder.gpkg
        /wippolder.las
        /wippolder.tif
3dbag
        /3dbag_one.city.json
tyler_debug
        /3dtiles
```

`geodepot show` prints the details of a case or data item.

```shell
geodepot show wippolder/wippolder.gpkg
```

Returns:

```shell
NAME=wippolder.gpkg

DESCRIPTION=New description.

format=GPKG
driver=None
license=CC0
sha1=b1ec6506eb7858b0667281580c4f5a5aff6894b2
changed_by=My Name <my@email.me>
extent=POLYGON ((85289.890625 447041.96875,85466.6953125 447041.96875,85466.6953125 447163.53125,85289.890625 447163.53125,85289.890625 447041.96875))
srs=PROJCS["Amersfoort / RD New",GEOGCS["Amersfoort",DATUM["Amersfoort",SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],AUTHORITY["EPSG","6289"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4289"]],PROJECTION["Oblique_Stereographic"],PARAMETER["latitude_of_origin",52.1561605555556],PARAMETER["central_meridian",5.38763888888889],PARAMETER["scale_factor",0.9999079],PARAMETER["false_easting",155000],PARAMETER["false_northing",463000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","28992"]]
```

## Collaboration

Multiple users can access the same test data by adding the same Geodepot repository on a remote server as a 'remote' to their local repository.
The users have read/write access to the remote, so they can update the remote with their local changes.

When an empty repository is initialized, it does not reference any remotes.
If you initialized the repository with a URL, the URL is added as a remote repository with the default name `origin`.

A remote is added with `geodepot remote add`.

```shell
geodepot remote add origin ssh://user@server:/path/to/.geodepot
```

The supported protocols are HTTP, HTTPS, SSH, SFTP. 
The `pull` and `push` commands only support the SSH and SFTP protocols.

