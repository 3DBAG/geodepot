# Geodepot – Test data storage system for geospatial data

Spatial data processing software are often tested against real-world data that is difficult to fake.
Consider for example a particularly nasty polygon or a particular configuration of triangles.
Such input is often too large to check into the version control system along with the source code, so we might end up storing them in a separate location.
As time passes and the software evolves, it is easy to forget about the purpose of the data and loose track of it.
Collecting and organizing good test data is a tedious, time consuming process, and it is best not to waste the effort.

Geodepot helps to organize data into test cases, share them and provide integration to some of the test frameworks for ease of use.
It was born from our own experience of writing spatial data processing tools over the past years.

## Example

The minimal example below gives and idea of how Geodepot works.

Initialize an empty repository in the current working directory.

```shell
geodepot init
```

Add some data to this repository.
The GeoPackage file `path/to/local/wippolder.gpkg` is added to the case `wippolder` with the name `wippolder.gpkg`, and the provided license and description are attached to the data entry.

```shell
geodepot add \
  --license CC0 \
  --description "A couple of buildings and a church in Delft for minimal testing." \
  wippolder \
  path/to/local/wippolder.gpkg
```

When writing a test, use one of the API functions to get the full path to the data.

=== "C++"

    ``` c++
    #include <geodepot/geodepot.h>

    int main(void) {
      auto repo = geodepot::Repository(
          "https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot");
      auto p = repo.get("wippolder/wippolder.gpkg");
      return 0;
    }
    ```

=== "Python"

    ``` python
    from geodepot import Repository

    def main():
        repo = Repository("https://data.3dgi.xyz/geodepot-test-data/mock_project/.geodepot")
        p = repo.get("wippolder/wippolder.gpkg")
    ```

Alternatively, you can also use the CLI to get the data path.

```shell
geodepot get wippolder/wippolder.gpkg
```

## Interfaces

### Command-line tool (CLI)

The main interface.
It supports all operations and you are currently reading its documentation.

Repository: [https://github.com/3DGI/geodepot](https://github.com/3DGI/geodepot)

### API

The API is meant for passing data paths to tests, nothing else.
The rest of the operations are done through the CLI.

The API is available in:

- C++ (implementation)
- Python (binding)

Repository: [https://github.com/3DGI/geodepot-api](https://github.com/3DGI/geodepot-api)

## What Geodepot is not

Geodepot is not a version control system, neither for data nor for code.
It is assumed that the data that you store in a Geodepot repository is already available, and will stay available in some other form.
Thus, if the repository is accidentally overwritten with unwanted changes, the desired state can be recreated with some effort.
That is, because the history of the repository is not retained, only the latest version is available at any time.

## Roadmap

The current version (`1`) is considered to be feature complete, and there are no major enhancements planned.
This does not mean however, that the current version is bug free.
The ongoing development focuses on fixing bugs reported by users or discovered during testing.
