@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Geodepot Windows Wrapper Script
:: 
:: This script launches geodepot from a self-contained portable environment.
:: It does NOT require pixi, conda, or any external tools to be installed.
:: ============================================================================

:: Get script directory with proper path handling
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Set the environment prefix (relative to script location)
set "CONDA_PREFIX=%SCRIPT_DIR%\env"
set "CONDA_SHLVL=1"

:: ============================================================================
:: Set geospatial data paths (critical for GDAL/PDAL to work correctly)
:: ============================================================================
:: On Windows, conda packages typically place data files in Library\share
set "GDAL_DATA=%CONDA_PREFIX%\Library\share\gdal"
set "PROJ_LIB=%CONDA_PREFIX%\Library\share\proj"

:: Also check the standard share directory (fallback)
if not exist "%GDAL_DATA%" set "GDAL_DATA=%CONDA_PREFIX%\share\gdal"
if not exist "%PROJ_LIB%" set "PROJ_LIB=%CONDA_PREFIX%\share\proj"

:: Ensure GDAL_DATA and PROJ_LIB are set (error if not found)
if not exist "%GDAL_DATA%" (
    echo ERROR: GDAL data files not found at %GDAL_DATA%
    echo Please ensure the environment was properly bundled.
    exit /b 1
)

if not exist "%PROJ_LIB%" (
    echo ERROR: PROJ data files not found at %PROJ_LIB%
    echo Please ensure the environment was properly bundled.
    exit /b 1
)

:: ============================================================================
:: Add conda environment to PATH
:: Windows-specific: Scripts, Library\bin, bin
:: ============================================================================
set "PATH=%CONDA_PREFIX%\Scripts;%CONDA_PREFIX%\Library\bin;%CONDA_PREFIX%\bin;%PATH%"

:: ============================================================================
:: Activate conda hooks if they exist (for any environment modifications)
:: ============================================================================
if exist "%CONDA_PREFIX%\etc\conda\activate.d\" (
    for %%F in ("%CONDA_PREFIX%\etc\conda\activate.d\*.bat") do call "%%~fF"
)

:: ============================================================================
:: Run geodepot
:: ============================================================================
"%CONDA_PREFIX%\python.exe" -m geodepot %*
endlocal
exit /b %ERRORLEVEL%
