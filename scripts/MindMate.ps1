param(
    [ValidateSet('Launch', 'Build')]
    [string]$Mode = 'Launch'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvDirectory = Join-Path $ProjectRoot '.venv'
$VenvPython = Join-Path $VenvDirectory 'Scripts\python.exe'
$RuntimeRequirements = Join-Path $ProjectRoot 'requirements.txt'

# Probe candidates without allowing missing versions or Store aliases to stop setup.
function Test-Python {
    param([string]$Executable, [string[]]$Prefix = @())
    $PreviousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Executable @Prefix -c "import struct, sys; sys.exit(0 if (3, 10) <= sys.version_info[:2] <= (3, 14) and struct.calcsize('P') == 8 else 1)" 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
    finally {
        $ErrorActionPreference = $PreviousPreference
    }
}

function Find-Python {
    $Launcher = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($Launcher) {
        # Prefer these widely available versions; fall back to the user's default.
        foreach ($Version in @('-3.13', '-3.12', '-3')) {
            if (Test-Python -Executable $Launcher.Source -Prefix @($Version)) {
                return @{ Executable = $Launcher.Source; Prefix = @($Version) }
            }
        }
    }

    $Python = Get-Command 'python.exe' -ErrorAction SilentlyContinue
    if ($Python -and (Test-Python -Executable $Python.Source)) {
        return @{ Executable = $Python.Source; Prefix = @() }
    }

    throw 'Install 64-bit Python 3.12 or 3.13 from https://www.python.org/downloads/windows/ (include the Python launcher or Add Python to PATH), then double-click this file again. Python 3.10 through 3.14 is supported.'
}

function Ensure-Environment {
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        if (Test-Path -LiteralPath $VenvDirectory) {
            throw 'The .venv folder is incomplete. Rename that folder and try again to create a fresh environment. Your journals and API settings are stored separately.'
        }
        $Python = Find-Python
        $PythonPrefix = $Python.Prefix
        Write-Host 'Preparing a local Python environment. This is only needed once...'
        & $Python.Executable @PythonPrefix -m venv $VenvDirectory
        if ($LASTEXITCODE -ne 0) {
            throw 'Python could not create the local environment. Check that this folder is writable and your Python installation includes venv.'
        }
    }

    if (-not (Test-Python -Executable $VenvPython)) {
        throw 'The .venv environment no longer works. Rename it and try again with 64-bit Python 3.10 through 3.14 installed.'
    }

    $CheckRequirements = @'
from importlib.metadata import version
from pathlib import Path
import sys
for line in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#'):
        name, expected = line.split('==', 1)
        if version(name) != expected:
            raise RuntimeError('Dependency version changed')
from PyQt6 import QtCore, QtGui, QtWidgets
'@
    $PreviousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $VenvPython -c $CheckRequirements $RuntimeRequirements 2>$null
        $DependenciesReady = $LASTEXITCODE -eq 0
    }
    finally {
        $ErrorActionPreference = $PreviousPreference
    }

    if (-not $DependenciesReady) {
        Write-Host 'Installing MindMate dependencies. Internet is needed for this first setup...'
        & $VenvPython -m pip install --disable-pip-version-check --only-binary=:all: -r $RuntimeRequirements
        if ($LASTEXITCODE -ne 0) {
            throw 'Dependencies could not be installed. Check your internet connection, then run this file again.'
        }
    }
}

try {
    Set-Location -LiteralPath $ProjectRoot
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'MindMate.py') -PathType Leaf)) {
        throw 'MindMate.py is missing. Extract the complete downloaded project before starting it.'
    }
    Ensure-Environment

    if ($Mode -eq 'Build') {
        Write-Host 'Preparing the Windows app build tools...'
        & $VenvPython -m pip install --disable-pip-version-check --only-binary=:all: -r (Join-Path $ProjectRoot 'requirements-build.txt')
        if ($LASTEXITCODE -ne 0) {
            throw 'Build tools could not be installed. Check your internet connection and try again.'
        }
        Write-Host 'Building MindMate.exe with the original image assets...'
        $PythonBase = & $VenvPython -c 'import sys; print(sys.base_prefix)'
        if ($LASTEXITCODE -ne 0) {
            throw 'The Python installation path could not be determined for the build.'
        }
        $OriginalBuildPath = $env:PATH
        try {
            # Keep unrelated tools' DLLs on PATH out of the packaged application.
            $env:PATH = @(
                (Join-Path $VenvDirectory 'Scripts'),
                $PythonBase,
                (Join-Path $env:SystemRoot 'System32'),
                $env:SystemRoot
            ) -join ';'
            & $VenvPython -m PyInstaller --noconfirm --clean (Join-Path $ProjectRoot 'MindMate.spec')
            if ($LASTEXITCODE -ne 0) {
                throw 'PyInstaller reported a build failure. The messages above show what needs attention.'
            }
        }
        finally {
            $env:PATH = $OriginalBuildPath
        }
        Write-Host ('Ready: ' + (Join-Path $ProjectRoot 'dist\MindMate.exe'))
    }
    else {
        Write-Host 'Starting MindMate. Keep this window open while the app is running.'
        & $VenvPython (Join-Path $ProjectRoot 'MindMate.py')
        if ($LASTEXITCODE -ne 0) {
            throw 'MindMate exited with an error. The details are printed above.'
        }
    }
    exit 0
}
catch {
    Write-Host ''
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
