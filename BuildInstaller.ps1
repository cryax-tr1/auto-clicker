$ErrorActionPreference = "Stop"

$compilerCandidates = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$compiler = $compilerCandidates |
    Where-Object { $_ -and (Test-Path $_) } |
    Select-Object -First 1

if (-not $compiler) {
    throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isdl.php."
}

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$distExePath = Join-Path $scriptDirectory "dist\PulseMacro.exe"
$exePath = Join-Path $scriptDirectory "release\PulseMacro.exe"
if (-not (Test-Path $distExePath)) {
    throw "PyInstaller output was not found: $distExePath. Build AutoClicker.spec first."
}

Push-Location $scriptDirectory
try {
    $releaseDirectory = Split-Path -Parent $exePath
    New-Item -ItemType Directory -Path $releaseDirectory -Force | Out-Null
    Copy-Item -LiteralPath $distExePath -Destination $exePath -Force

    & $compiler "AutoClicker.iss"
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed (exit code $LASTEXITCODE)."
    }
}
finally {
    Pop-Location
}
