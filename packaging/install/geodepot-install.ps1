[CmdletBinding()]
param(
    [string]$Version = "latest",
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "geodepot"),
    [string]$BinDir = (Join-Path $HOME ".local\bin"),
    [switch]$NoWrapper,
    [switch]$NoPathUpdate
)

$ErrorActionPreference = "Stop"

$Repo = if ($env:GEODEPOT_REPO) { $env:GEODEPOT_REPO } else { "3DBAG/geodepot" }
$ApiBase = if ($env:GEODEPOT_GITHUB_API) { $env:GEODEPOT_GITHUB_API } else { "https://api.github.com" }
$DownloadBase = if ($env:GEODEPOT_GITHUB_DOWNLOAD) { $env:GEODEPOT_GITHUB_DOWNLOAD } else { "https://github.com/$Repo/releases/download" }

function Write-Status([string]$Message) {
    Write-Host $Message
}

function Resolve-Tag {
    if ($Version -ne "latest") {
        return $Version
    }

    return (Invoke-RestMethod -Headers @{ Accept = "application/vnd.github+json" } -Uri "$ApiBase/repos/$Repo/releases/latest").tag_name
}

function Resolve-Arch {
    switch ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()) {
        "X64" { return "x86_64" }
        "Arm64" { return "arm64" }
        default { throw "Unsupported architecture: $([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture)" }
    }
}

function Test-AssetExists([string]$Url) {
    try {
        Invoke-WebRequest -Uri $Url -Method Head -MaximumRedirection 5 -UseBasicParsing | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Resolve-AssetName([string]$Tag, [string]$Arch) {
    $Candidates = switch ($Arch) {
        "x86_64" { @("geodepot-windows-x86_64.zip", "geodepot-win-x86_64.zip", "geodepot-win.zip") }
        "arm64" { @("geodepot-windows-arm64.zip") }
        default { throw "Unsupported architecture: $Arch" }
    }

    foreach ($Asset in $Candidates) {
        if (Test-AssetExists "$DownloadBase/$Tag/$Asset") {
            return $Asset
        }
    }

    throw "Could not find a release bundle for windows/$Arch at tag $Tag."
}

$Tag = Resolve-Tag
$Arch = Resolve-Arch
$Asset = Resolve-AssetName -Tag $Tag -Arch $Arch
$ChecksumAsset = "$Asset.sha256sum"

Write-Status "Starting Geodepot installation."
Write-Status "Detecting platform and release bundle."
if ($Version -eq "latest") {
    Write-Status "Resolving latest release tag from GitHub."
} else {
    Write-Status "Installing requested version: $Version."
}
Write-Status "Using release $Tag for windows/$Arch."
Write-Status "Selected bundle $Asset."

$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("geodepot-install-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempDir | Out-Null

try {
    $ArchivePath = Join-Path $TempDir $Asset
    $ChecksumPath = Join-Path $TempDir $ChecksumAsset

    Write-Status "Downloading bundle and checksum."
    Invoke-WebRequest -Uri "$DownloadBase/$Tag/$Asset" -OutFile $ArchivePath
    Invoke-WebRequest -Uri "$DownloadBase/$Tag/$ChecksumAsset" -OutFile $ChecksumPath

    Write-Status "Verifying checksum."
    $ExpectedHash = ((Get-Content -Path $ChecksumPath -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
    $ActualHash = (Get-FileHash -Path $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()

    if ($ExpectedHash -ne $ActualHash) {
        throw "Checksum verification failed for $Asset."
    }

    $ReleaseDir = Join-Path $InstallDir "releases\$Tag"
    if (Test-Path $ReleaseDir) {
        Remove-Item -Recurse -Force $ReleaseDir
    }

    New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
    Write-Status "Installing into $ReleaseDir."
    Write-Status "Extracting bundle."
    Expand-Archive -Path $ArchivePath -DestinationPath $ReleaseDir -Force

    $BundleDir = Join-Path $ReleaseDir "geodepot"
    $BundleCmd = Join-Path $BundleDir "geodepot.cmd"
    $BundlePs1 = Join-Path $BundleDir "geodepot.ps1"

    if (-not (Test-Path $BundleCmd)) {
        throw "Unexpected bundle layout in $Asset."
    }

    if (-not $NoWrapper) {
        Write-Status "Installing wrappers in $BinDir."
        New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

        $CmdWrapperPath = Join-Path $BinDir "geodepot.cmd"
        Set-Content -Path $CmdWrapperPath -Value @"
@echo off
call "$BundleCmd" %*
exit /b %ERRORLEVEL%
"@

        $PsWrapperPath = Join-Path $BinDir "geodepot.ps1"
        Set-Content -Path $PsWrapperPath -Value @"
& '$BundlePs1' @args
exit `$LASTEXITCODE
"@

        if (-not $NoPathUpdate) {
            $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
            $PathEntries = @()
            if (-not [string]::IsNullOrWhiteSpace($UserPath)) {
                $PathEntries = $UserPath -split ';' | Where-Object { $_ }
            }

            if ($PathEntries -notcontains $BinDir) {
                $NewPath = if ([string]::IsNullOrWhiteSpace($UserPath)) { $BinDir } else { "$UserPath;$BinDir" }
                [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
                $env:Path = "$env:Path;$BinDir"
                $PathUpdated = $true
            }
        }
    }

    Write-Host "Installed Geodepot $Tag to $BundleDir"
    if (-not $NoWrapper) {
        Write-Host "Installed launcher wrappers to $BinDir"
        if ($PathUpdated) {
            Write-Host "Updated the user PATH. Open a new shell to pick up the change."
        }
        elseif (-not ($env:Path -split ';' | Where-Object { $_ -eq $BinDir })) {
            Write-Host "Add $BinDir to PATH to run 'geodepot' from any shell."
        }
    }
    else {
        Write-Host "Run $BundleCmd to start Geodepot."
    }
}
finally {
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force $TempDir
    }
}
