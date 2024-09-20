# API Reference

## Init

Initialize a local repository from an existing Geodepot repository.
The constructor take a path to a local directory or a URL to a remote directory.
The path must contain a valid Geodepot repository.
After initialization, the data items in this repository can be downloaded and used in the tests.

=== "C++"

    ``` c++
    #include <geodepot/geodepot.h>

    int main(void) {
      auto repo = geodepot::Repository(
          "https://data.3dgi.xyz/geodepot-test-data/mock_project");
    }
    ```

=== "Python"

    ``` python
    from geodepot import Repository

    def main():
        repo = Repository("https://data.3dgi.xyz/geodepot-test-data/mock_project")
    ```

=== "CMake"

    ```cmake
    include(GeoDepot)
    
    GeodepotInit("https://data.3dgi.xyz/geodepot-test-data/mock_project")
    ```

## Get

Once the repository has been initialized, it is possible to get the full local path to a data item.
If the data is not available locally, it will be downloaded from the remote on the first call if the function.

=== "C++"

    ``` c++
    std::filesystem::path p = repo.get("wippolder/wippolder.gpkg");
    ```

=== "Python"

    ``` python
    p = repo.get("wippolder/wippolder.gpkg")
    ```

=== "CMake"
    Geodepot sets the `GEODEPOT_DIR` CMake cache variable to the path to the initialized geodepot repository.
    In order obtain the full path to a data item, construct the path as `${GEODEPOT_DIR}/<case name>/<data name>`.

    ```cmake
    GeodepotGet("wippolder/wippolder.gpkg")

    # add executables, entable tests etc...

    add_test(
          NAME "function-using-geodepot-data"
          COMMAND test_geodepot_cmake "${GEODEPOT_DIR}/wippolder/wippolder.gpkg"
          WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
    ```