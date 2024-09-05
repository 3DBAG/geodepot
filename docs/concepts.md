# Concepts

## Configuration

Geodepot uses configuration files to store user information and remotes, among other things.

You can specify Geodepot configuration settings with the `geodepot config` command.
Geodepot looks for configuration values on two levels, global and local.

Geodepot first looks for the configuration in the `~/.geodepotconfig.json` file, which is specific to each user.
You can make Geodepot read and write to this file by passing the `--global` option.

Secondly, Geodepot looks for configuration values in the configuration file in the Geodepot directory (`.geodepot/config.json`) of whatever repository you are currently using.
These values are specific to that single repository and they are read and written by passing the `--local` option.
This is the default option of the `geodepot config` command.

The local level config overwrites the values of the global level config.

### User

The user information consists of a name and an e-mail address and it is registered in the local HOME directory of the User.
The user information is used for identifying changes and locks.

Set the user information with the `config` command.

```shell
geodepot config --global user.name "My Name"
geodepot config --global user.email "my@email.me"
```

## Repository

A *repository* is a collection of related *cases* that are used as data in software testing.
Normally, there is one repository per project, storing all the data that are required by the tests of the project.
For example, the projects *3dbag-pipeline* and *geoflow-roofer* would each have their own Geodepot repository.

The repository is itself is stored in a `.geodepot` directory, which is normally located in the software project directory.

If you are using Git, or any other version control system, don't forget to exclude the `.geodepot` directory.

## Index

The *repository* organises the *cases* with its *index*.
The *index* stores the overview of all *cases* in the repository.

## Case

A *case* is an organizational unit of related *data items*.
A *case* is identified by its name.
Examples of a case include a bug report with its related files, a particular area in several data formats etc.

## Data (item)

A *data item* is the actual file or directory that contains the data that is used in a test.
Data items retain their own format when added to the repository, therefore they can be read directly with their format-specific readers.

When the data path is requested, Geodepot returns the full path to the local data file in the repository.

## Remote

A Geodepot repository on a remote server.
By connecting, 'referencing' a remote to your local repository, it is possible to share the data items with other users.
A remote is added with the `geodepot remote add` command.

### Conflict resolution between local and remote repositories

Geodepot does not retain version history for the data items, nor can it merge different versions of a data item.
Therefore, Geodepot does not resolve conflicts automatically.

In short, Geodepot know two alternatives to resolve conflicts, either overwrite the local with the remote data (`pull`), or overwrite the remote with the local data (`push`).

Both of these operations list the detected differences between the local and remote, together with the user that made the last change.
The underlying assumption is that a single Geodepot repository is shared by users who have direct contact with each other, e.g. a team.
Therefore, if it is not clear whether it is safe to overwrite the local/remote with the changes, the users should discuss with each other how to resolve the conflict manually.

**Example**

Both _UserA_ and _UserB_ are working with the same remote repository, _Server_.
Each of the three repositories contain the same data item, `wippolder/wippolder.gpkg`.
_UserA_ removes a few objects from `wippolder/wippolder.gpkg` and updates the data item in her local repository, but does not push the changes to _Server_.
In the meantime, _UserB_ changes the description of `wippolder/wippolder.gpkg` and immediately pushes the changes to _Server_.
After a while, _UserA_ decides to push her changes and Geodepot reports that the data `wippolder/wippolder.gpkg` on _Server_ differs from her local version in its,

- _description_, because _UserB_ changed it,
- _extent_, because _UserB_ pushed a version which still contained the objects that _UserA_ removed,
- _sha1_, because the file itself has changed
- _changed_by_ shows _UserB_, because he made the last change on the version that is on the _Server_.

At this point, _UserA_ and _UserB_ need to agree on a common version for `wippolder/wippolder.gpkg`, push it to the _Server_ and update their local versions with it.

