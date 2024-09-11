# Command-line tool

## geodepot

Test data storage system for geospatial data

**Usage**

```shell
geodepot [OPTIONS] <COMMAND>
```

**Commands**

[`geodepot add`](#add): Add or update a case or a data item.

[`geodepot config`](#config): Query or set Geodepot configuration values.

[`geodepot fetch`](#fetch): Compare the local repository against a remote.

[`geodepot get`](#get): Return the full local path to the specified data item of the specified case.

[`geodepot init`](#init): Initialise a Geodepot repository in the current directory.

[`geodepot list`](#list): List the cases and data items in the repository.

[`geodepot pull`](#pull): Download any changes from a remote repository and overwrite the local version.

[`geodepot push`](#push): Upload any local changes to a remote repository and overwrite the remote version.

[`geodepot remote`](#remote): Connect an existing remote Geodepot repository.

[`geodepot remove`](#remove): Delete a case or a data entry from the repository.

[`geodepot show`](#show): Show the details of the specified case or data.

## add

**Synopsis**

```shell
geodepot add [-y] [--license=<text>] [--description=<text>] [--format=<format>] [--as-data] [<pathspec>...] <casespec>
```

**Description**

Add or update a case or a data item.
In each operation, the case will be created if it does not exist.
In each operation, existing values, data files are updated with the newly provided.

**Options**

`<casespec>`:
Case (and data) specifier, in the form of `case-name[/data-name]`.
Providing the case name `case-name` is mandatory, the data name `data-name` within the case is optional.
The rest of the options will affect the specified level, either the whole case with `case-name`, or just a single data within the case with `case-name/data-name`.
For example, `wippolder/wippolder.gpkg`, where `wippolder` is the case name, `wippolder.gpkg` is the data name.

`<pathspec>`:
Path specifier for the data files to add to the case.
Can be a path to a single file, a directory or a fileglob (e.g. `*.gpkg`).
Can be passed multiple times.
Only local files are supported.

`-y`:
Do not require confirmation for updating existing values or files.

`--license=<text>`:
A license to add to the data.

`--description=<text>`:
A description to add to the case or data.

`--format=<format>`:
A format to force on the data in case it cannot be inferred automatically, or the inferred format is not correct.
If the a whole directory is added as a single data entry with `--as-data`, the automatic format inference doesn't work, and it may be necessary to force a format.
Note that when the format is forced, the bounding box calculation and hashing does not work.

`--as-data`:
Add a whole directory as a single data entry.
The default behaviour is to add each file in the directory as a separate data entry.
If `--as-data` is set, the bounding box and file hash cannot be computed for the data.

**Examples**

Add multiple files as data entries to a case.
If the case does not exist, it will be created as `case-name` and the file `file-name` is moved into it.

```shell
geodepot add /path/to/file-name1 /path/to/file-name2 case-name
```

Update the license and description of a data entry (`file-name`) in a case (`case-name`).

```shell
geodepot add --description "long description\nmultiline" --license "CC-0" case-name/file-name1
```

Update the description of a case (`case-name`)

```shell
geodepot add --description "new description of the case" case-name
```

## fetch

**Synopsis**

```shell
geodepot fetch <name>
```

**Description**

Compare the local repository against the remote `<name>`.
The differences are printed to the console.

## config

**Synopsis**

```shell
geodepot config list
geodepot config get [--global] <name>
geodepot config set [--global] <name> <value>
```

**Description**

Query or set Geodepot configuration values.
The `name` is actually the section and the key separated by a dot, and the `value` will be escaped.

**Options**

`--global`:
For writing options: write to the global `~/.geodepotconfig` file rather than the repository `.geodepot/config`.

For reading options: read only from the global `~/.geodepotconfig` file rather than the repository `.geodepot/config`.

**Examples**

```shell
geodepot config add --global user.name "Kovács János"
geodepot config add --global user.email janos@kovacs.me
```

### config list

List all variables set in the config files, along with their values.

### config get

Emits the value of the specified key. If key is present multiple times in the configuration, emits the last value.

### config set

Set the value for one configuration option.

## get

**Synopsis**

```shell
geodepot get <casespec>
```

**Description**

Return the full local path to the specified data item of the specified case.
If the data item does not exist locally and a remote repository is configured, the data will be downloaded from the remote.

**Options**

`<casespec>`:
Case (and data) specifier, in the form of `case-name/data-name`.
For example, `wippolder/wippolder.gpkg`, where `wippolder` is the case name, `wippolder.gpkg` is the data name.

**Examples**

Get the full local path to the data item `wippolder/wippolder.gpkg`.

```shell
geodepot get wippolder/wippolder.gpkg
```

## init

**Synopsis**

```shell
geodepot init [url]
```

**Description**

Initialise a Geodepot repository in the current directory.

**Options**

Without arguments, initialise an empty local repository in the current directory.

With a URL to a remote repository as an argument, `geodepot init <url>`, download the remote repository except its data files, to make it available locally.
The data needs to be `pull`-ed explicitly after the repository has been initialised.

## list

**Synopsis**

```shell
geodepot list
```

**Description**

List the cases and data items in the repository.

## pull

**Synopsis**

```shell
geodepot pull [--yes] <name>
```

**Description**

Download any changes from the remote repository `<name>`, overwriting the local version.
Geodepot lists the differences between the local and remote, by calling `geodepot fetch` internally and asks for confirmation before overwriting the local.

**Options**

`--yes / -y`:
Automatically overwrite the local without asking for confirmation.

## push

**Synopsis**

```shell
geodepot push [--yes] <name>
```

**Description**

Upload any local changes to the remote repository `<name>`, overwriting the remote version.
Geodepot lists the differences between the local and remote, by calling `geodepot fetch` internally and asks for confirmation before overwriting the remote.

**Options**

`--yes / -y`:
Automatically overwrite the remote without asking for confirmation.

## remote

**Synopsis**

```shell
geodepot remote list
geodepot remote add <name> <url>
geodepot remote remove <name>
```

**Description**

Connect an existing remote Geodepot repository.

**Examples**

```shell
geodepot remote add origin https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot
```

### remote list

List the available remote repositories.

### remote add

Add a remote repository to track. The remote repository must exist.

### remote remove

Remove the remote from the tracked remotes. The remote repository is not deleted.

## remove

**Synopsis**

```shell
geodepot remove [-y] [<casespec>...]
```

**Description**

Delete a case or a data entry from the repository.

**Options**

`<casespec>`:
Case (and data) specifier, in the form of `case-name[/data-name]`.
Can be specified multiple times.
Providing the case name `case-name` is mandatory, the data name `data-name` within the case is optional.
The rest of the options will affect the specified level, either the whole case with `case-name`, or just a single data within the case with `case-name/data-name`.
For example, `wippolder/wippolder.gpkg`, where `wippolder` is the case name, `wippolder.gpkg` is the data name.

`-y`:
Do not require confirmation for deleting the entries.

## show

**Synopsis**

```shell
geodepot show <casespec>
```

**Description**

Show the details of the specified case or data.

