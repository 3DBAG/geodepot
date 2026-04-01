@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "CONDA_PREFIX=%SCRIPT_DIR%\env"
set "CONDA_SHLVL=1"
set "PATH=%CONDA_PREFIX%\Scripts;%CONDA_PREFIX%\Library\bin;%CONDA_PREFIX%\bin;%PATH%"

if exist "%CONDA_PREFIX%\etc\conda\activate.d" (
    for %%F in ("%CONDA_PREFIX%\etc\conda\activate.d\*.bat") do call "%%~fF"
)

"%CONDA_PREFIX%\Scripts\geodepot.exe" %*
exit /b %ERRORLEVEL%
