# Examples

!!! warning "Incomplete section"

Initialising an empty repository, adding a case, adding a remote and uploading the repository to the remote.

```shell
cd my-project
geodepot init
geodepot add case-name /path/to/dir/with/data --description "text"
geodepot remote add remote-name https://remote.url
geodepot push remote-name
```

Cloning an existing repository from a remote and list the available cases.
Cloning the repository only downloads the index, but not the data files.

```shell
cd my-project
geodepot init https://remote.url
geodepot list
```

Returns:

```shell
ID  NAME    DESCRIPTION
--  ----    -----------
1   case-1  A single building in the Netherlands.
```

Show the details of a case to see its data files.

```shell
geodepot show case-1
```

Returns:

```shell
CASE ID: 1

FILE                CRS
----                ---
footprint.gpkg      EPSG:28992
pointcloud.laz      EPSG:7415

```

Get the path to the specified file of the specified case.

```shell
geodepot get case-1 footprint.gpkg
```

Returns:

```shell
/path/to/.geodepot/cases/1/footprint.gpkg
```
