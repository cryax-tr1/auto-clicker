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
$exePath = Join-Path $scriptDirectory "release\AutoClicker.exe"
if (-not (Test-Path $exePath)) {
    throw "Application EXE was not found: $exePath"
}

Push-Location $scriptDirectory
try {
    & $compiler "AutoClicker.iss"
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed (exit code $LASTEXITCODE)."
    }
}
finally {
    Pop-Location
}
