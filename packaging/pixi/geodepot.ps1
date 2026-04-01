$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:CONDA_PREFIX = Join-Path $ScriptDir "env"
$env:CONDA_SHLVL = "1"
$env:PATH = "$(Join-Path $env:CONDA_PREFIX 'Scripts');$(Join-Path $env:CONDA_PREFIX 'Library\bin');$(Join-Path $env:CONDA_PREFIX 'bin');$env:PATH"

$activateDir = Join-Path $env:CONDA_PREFIX "etc\conda\activate.d"
if (Test-Path $activateDir) {
    Get-ChildItem $activateDir -Filter "*.ps1" | Sort-Object Name | ForEach-Object {
        . $_.FullName
    }
}

& (Join-Path $env:CONDA_PREFIX "Scripts\geodepot.exe") @args
exit $LASTEXITCODE
