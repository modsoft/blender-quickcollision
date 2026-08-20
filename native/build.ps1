# Builds stanhull-win64.dll into the add-on root.
# Requires Visual Studio with C++ build tools.

$ErrorActionPreference = "Stop"

$nativeDir = $PSScriptRoot
$addonDir = Split-Path $nativeDir -Parent
$outDll = Join-Path $addonDir "stanhull-win64.dll"

$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vswhere)) {
    throw "vswhere.exe not found; install Visual Studio with C++ build tools"
}
$vsPath = & $vswhere -latest -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
    -property installationPath
if (-not $vsPath) {
    throw "No Visual Studio installation with C++ tools found"
}

$vcvars = Join-Path $vsPath "VC\Auxiliary\Build\vcvars64.bat"
$buildDir = Join-Path $nativeDir "build"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

cmd /c "`"$vcvars`" >nul 2>&1 && cl /nologo /O2 /EHsc /MD /LD /I`"$nativeDir`" `"$nativeDir\stanhull.cpp`" `"$nativeDir\stanhull_capi.cpp`" /Fo:`"$buildDir\\`" /Fe:`"$outDll`""
if ($LASTEXITCODE -ne 0) {
    throw "Compilation failed with exit code $LASTEXITCODE"
}

# ctypes only needs the DLL; drop the MSVC import-library artifacts.
Remove-Item -ErrorAction SilentlyContinue `
    (Join-Path $addonDir "stanhull-win64.lib"), `
    (Join-Path $addonDir "stanhull-win64.exp")

Write-Output "Built $outDll"
