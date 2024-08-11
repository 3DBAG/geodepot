# Require at least CMake 3.25, because in 3.24 and 3.25 there were a couple of
# FetchContent-related changes
cmake_minimum_required(VERSION 3.25)

project(geodepot LANGUAGES C CXX)

# Global CMake variables are set here We use C++20, with the assumption that we
# only implement features that are supported by GCC, Clang, MSVC, Apple Clang
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
# Don't use extensions, because they might affect compiler compatibility
set(CMAKE_CXX_EXTENSIONS OFF)

# CMAKE MODULES

# CMake modules, like the documentation module, go in here
list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake/")

# EXTERNAL LIBRARIES

find_package(nlohmann_json REQUIRED)
find_package(fmt REQUIRED)
set(SPDLOG_FMT_EXTERNAL ON)
find_package(spdlog REQUIRED)
find_package(GEOS CONFIG REQUIRED)
# GDAL
find_package(GDAL CONFIG REQUIRED)
if(WIN32) # vcpkg doesn't work when there is a version number here
  find_package(PROJ REQUIRED CONFIG)
else()
  find_package(PROJ 9.0.0 REQUIRED CONFIG)
endif()
find_package(PDAL REQUIRED CONFIG)

add_executable("geodepot" "main.cpp")
set_target_properties("geodepot" PROPERTIES CXX_STANDARD 20)
target_link_libraries("geodepot" PRIVATE GDAL::GDAL fmt::fmt spdlog::spdlog ${PDAL_LIBRARIES})
