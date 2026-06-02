<#
.SYNOPSIS
    Geodepot Windows PowerShell Wrapper Script

.DESCRIPTION
    This script launches geodepot from a self-contained portable environment.
    It does NOT require pixi, conda, or any external tools to be installed.
    Just unzip the bundle and run this script.

.EXAMPLE
    .\geodepot.ps1 --help
    .\geodepot.ps1 init
    .\geodepot.ps1 add mycase data.gpkg
#>

# ============================================================================
# Get script directory
# ============================================================================
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# ============================================================================
# Set environment prefix (relative to script location)
# ============================================================================
$env:CONDA_PREFIX = Join-Path $ScriptDir "env"
$env:CONDA_SHLVL = "1"

# ============================================================================
# Set geospatial data paths (critical for GDAL/PDAL to work correctly)
# ============================================================================
# On Windows, conda packages typically place data files in Library\share
$gdalPath1 = Join-Path $env:CONDA_PREFIX "Library\share\gdal"
$gdalPath2 = Join-Path $env:CONDA_PREFIX "share\gdal"

if (Test-Path $gdalPath1) {
    $env:GDAL_DATA = $gdalPath1
} elseif (Test-Path $gdalPath2) {
    $env:GDAL_DATA = $gdalPath2
} else {
    Write-Error "GDAL data files not found in $gdalPath1 or $gdalPath2"
    Write-Error "Please ensure the environment was properly bundled."
    exit 1
}

$projPath1 = Join-Path $env:CONDA_PREFIX "Library\share\proj"
$projPath2 = Join-Path $env:CONDA_PREFIX "share\proj"

if (Test-Path $projPath1) {
    $env:PROJ_LIB = $projPath1
} elseif (Test-Path $projPath2) {
    $env:PROJ_LIB = $projPath2
} else {
    Write-Error "PROJ data files not found in $projPath1 or $projPath2"
    Write-Error "Please ensure the environment was properly bundled."
    exit 1
}

# ============================================================================
# Add conda environment to PATH
# Windows-specific: Scripts, Library\bin, bin
# ============================================================================
$env:PATH = "$(Join-Path $env:CONDA_PREFIX 'Scripts');$(Join-Path $env:CONDA_PREFIX 'Library\bin');$(Join-Path $env:CONDA_PREFIX 'bin');$env:PATH"

# ============================================================================
# Activate conda hooks if they exist (for any environment modifications)
# ============================================================================
$activateDir = Join-Path $env:CONDA_PREFIX "etc\conda\activate.d"
if (Test-Path $activateDir) {
    Get-ChildItem $activateDir -Filter "*.ps1" | Sort-Object Name | ForEach-Object {
        try {
            . $_.FullName
        } catch {
            Write-Warning "Failed to execute activation script: $_"
        }
    }
}

# ============================================================================
# Run geodepot
# ============================================================================
try {
    $pythonExe = Join-Path $env:CONDA_PREFIX "python.exe"
    if (-not (Test-Path $pythonExe)) {
        Write-Error "Python executable not found at $pythonExe"
        exit 1
    }
    
    & $pythonExe -m geodepot @args
    exit $LASTEXITCODE
} catch {
    Write-Error "Failed to run geodepot: $_"
    exit 1
}
