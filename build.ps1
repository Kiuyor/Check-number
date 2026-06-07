# ============================================================
# CheckNumber - One-Click Build Script
# Usage: .\build.ps1 [-Clean] [-SkipNuitka] [-SkipInstaller]
# ============================================================
param(
    [switch]$SkipNuitka,
    [switch]$SkipInstaller,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ---- Paths ----
$NuitkaOutput    = "build\v9.2.dist"
$NuitkaBuild     = "build\v9.2.build"
$ExePath         = "$NuitkaOutput\CheckNumber.exe"
$NSIS            = "C:\Program Files (x86)\NSIS\makensis.exe"
$ManifestTool    = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\mt.exe"
$InstallerScript = "installer.nsi"
$ManifestFile    = "$ScriptDir\app.manifest"
$EntryScript     = "v9.2.py"
$ChangelogFile   = "whs_update"
$LogoPNG         = $null  # auto-detect: *logo*.png
$IconFile        = "app.ico"

# ---- DPI-aware Manifest ----
$ManifestContent = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" xmlns:asmv3="urn:schemas-microsoft-com:asm.v3" manifestVersion="1.0">
  <assemblyIdentity type="win32" name="Mini" version="1.0.0.0"/>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
    </application>
  </compatibility>
  <asmv3:application>
    <asmv3:windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
    </asmv3:windowsSettings>
  </asmv3:application>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
    </dependentAssembly>
  </dependency>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>
'@

# =========================================
# Step 0: Environment Check
# =========================================
Write-Host "=== CheckNumber One-Click Build ===" -ForegroundColor Cyan
Write-Host ""

# Check Pillow (for icon conversion)
$pillowOk = $true
python -c "from PIL import Image" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Pillow not installed, icon conversion disabled" -ForegroundColor Yellow
    Write-Host "    Run: pip install Pillow" -ForegroundColor Gray
    $pillowOk = $false
}
else {
    Write-Host "[OK] Pillow" -ForegroundColor Green
}

# Check Nuitka
$nuitkaVer = python -m nuitka --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Nuitka not found. Run: pip install nuitka" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Nuitka" -ForegroundColor Green

# Check NSIS
if (-not (Test-Path $NSIS)) {
    Write-Host "[ERROR] NSIS not found: $NSIS" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] NSIS" -ForegroundColor Green

# Check mt.exe
if (-not (Test-Path $ManifestTool)) {
    Write-Host "[!] mt.exe not found, DPI manifest embedding disabled" -ForegroundColor Yellow
}
else {
    Write-Host "[OK] mt.exe (Manifest Tool)" -ForegroundColor Green
}

# =========================================
# Step 0.5: Clean
# =========================================
if ($Clean) {
    Write-Host ""
    Write-Host "--- Cleaning old builds ---" -ForegroundColor Yellow
    if (Test-Path $NuitkaBuild)  { Remove-Item -Recurse -Force $NuitkaBuild; Write-Host "  Deleted $NuitkaBuild" }
    if (Test-Path $NuitkaOutput) { Remove-Item -Recurse -Force $NuitkaOutput; Write-Host "  Deleted $NuitkaOutput" }
    if (Test-Path "CheckNumber-Setup.exe") { Remove-Item -Force "CheckNumber-Setup.exe"; Write-Host "  Deleted CheckNumber-Setup.exe" }
}

# =========================================
# Step 1: Generate Icon (PNG -> ICO)
# =========================================
if (-not $SkipNuitka) {
    Write-Host ""
    Write-Host "--- [1/4] Generate Icon (PNG -> ICO) ---" -ForegroundColor Yellow

    # Auto-detect any *logo*.png in script directory
    $logoSource = Get-ChildItem -Path $ScriptDir -Filter "*logo*.png" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Name

    if ($logoSource -and $pillowOk) {
        python -c @"
from PIL import Image
img = Image.open(r'$logoSource')
if img.mode != 'RGBA':
    img = img.convert('RGBA')
sizes = [(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)]
img.save('$IconFile', format='ICO', sizes=sizes)
print(f'$IconFile generated ({img.size[0]}x{img.size[1]} -> multi-res)')
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] app.ico generated" -ForegroundColor Green
        }
        else {
            Write-Host "[!] Icon generation failed, skipping" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "[!] No logo found or Pillow missing, skipping icon" -ForegroundColor Yellow
    }

    # =========================================
    # Step 2: Nuitka Compile
    # =========================================
    Write-Host ""
    Write-Host "--- [2/4] Nuitka Compile (standalone + PyQt5) ---" -ForegroundColor Yellow
    Write-Host "  This takes 3-8 minutes..." -ForegroundColor Gray

    $nuitkaArgs = @(
        "-m", "nuitka",
        "--standalone",
        "--enable-plugin=pyqt5",
        "--windows-console-mode=disable",
        "--output-dir=build",
        "--output-filename=CheckNumber.exe",
        "--include-data-files=$ChangelogFile=$ChangelogFile",
        "--assume-yes-for-downloads",
        $EntryScript
    )
    if (Test-Path $IconFile) {
        $nuitkaArgs += "--windows-icon-from-ico=$IconFile"
        Write-Host "  Embedding app.ico into exe" -ForegroundColor Gray
    }

    python @nuitkaArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Nuitka compilation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Nuitka compilation done" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "--- [1/4] Icon (skipped) ---" -ForegroundColor Yellow
    Write-Host "--- [2/4] Nuitka (skipped) ---" -ForegroundColor Yellow
}

# =========================================
# Step 3: Embed DPI-aware Manifest
# =========================================
Write-Host ""
Write-Host "--- [3/4] Embed DPI-aware Manifest ---" -ForegroundColor Yellow

if (-not (Test-Path $ExePath)) {
    Write-Host "[ERROR] Exe not found: $ExePath" -ForegroundColor Red
    exit 1
}

Set-Content -Path $ManifestFile -Value $ManifestContent -Encoding UTF8

if (Test-Path $ManifestTool) {
    & $ManifestTool -manifest $ManifestFile -outputresource:"$ExePath;#1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Manifest embedding failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] DPI manifest embedded (PerMonitorV2)" -ForegroundColor Green
}
else {
    Copy-Item $ManifestFile "$ExePath.manifest" -Force
    Write-Host "[OK] External manifest placed (CheckNumber.exe.manifest)" -ForegroundColor Yellow
}

Remove-Item $ManifestFile -Force -ErrorAction SilentlyContinue

# =========================================
# Step 4: NSIS Installer
# =========================================
if (-not $SkipInstaller) {
    Write-Host ""
    Write-Host "--- [4/4] NSIS Installer ---" -ForegroundColor Yellow

    & $NSIS $InstallerScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] NSIS packaging failed" -ForegroundColor Red
        exit 1
    }

    $installerSize = (Get-Item "CheckNumber-Setup.exe").Length / 1MB
    $msg = "[OK] Installer created ({0:F1} MB)" -f $installerSize
    Write-Host $msg -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "--- [4/4] NSIS (skipped) ---" -ForegroundColor Yellow
}

# =========================================
# Done
# =========================================
Write-Host ""
Write-Host "===== Build Complete =====" -ForegroundColor Cyan
Write-Host "Installer : $ScriptDir\CheckNumber-Setup.exe" -ForegroundColor White
Write-Host "Standalone: $ScriptDir\$NuitkaOutput" -ForegroundColor White
Write-Host ""
Write-Host "Usage:" -ForegroundColor Gray
Write-Host "  .\build.ps1                Full build" -ForegroundColor Gray
Write-Host "  .\build.ps1 -Clean         Clean + full build" -ForegroundColor Gray
Write-Host "  .\build.ps1 -SkipNuitka    NSIS repack only" -ForegroundColor Gray
Write-Host "  .\build.ps1 -SkipInstaller Nuitka only" -ForegroundColor Gray
