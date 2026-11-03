# Bootstrap script: Automatically download Python Portable + FFmpeg if system has none
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$rootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$runtimeDir = Join-Path $rootDir "runtime"
$pyDir = Join-Path $runtimeDir "python"
$ffDir = Join-Path $runtimeDir "ffmpeg"

New-Item -ItemType Directory -Force -Path $pyDir | Out-Null
New-Item -ItemType Directory -Force -Path $ffDir | Out-Null

# 1. Download Python Embeddable
Write-Host "[1/3] Đang tải Python Portable..." -ForegroundColor Cyan
$pyZip = Join-Path $runtimeDir "python.zip"
$pyUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
try {
    Invoke-WebRequest -Uri $pyUrl -OutFile $pyZip -UseBasicParsing
    Expand-Archive -Path $pyZip -DestinationPath $pyDir -Force
    Remove-Item $pyZip -Force
} catch {
    Write-Warning "Không thể tải Python: $_"
    exit 1
}

# Enable import site
$pth = Get-ChildItem -Path $pyDir -Filter "*._pth" | Select-Object -First 1
if ($pth) {
    (Get-Content $pth.FullName) -replace '#import site', 'import site' | Set-Content $pth.FullName
}

# 2. Download get-pip
Write-Host "[2/3] Đang cài đặt thư viện cần thiết..." -ForegroundColor Cyan
$pipPy = Join-Path $runtimeDir "get-pip.py"
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $pipPy -UseBasicParsing
& (Join-Path $pyDir "python.exe") $pipPy --no-warn-script-location --quiet
Remove-Item $pipPy -Force -ErrorAction SilentlyContinue

$reqFile = Join-Path $rootDir "requirements.txt"
& (Join-Path $pyDir "python.exe") -m pip install -r $reqFile --no-warn-script-location --quiet
& (Join-Path $pyDir "python.exe") -m playwright install chromium --quiet

# 3. Download FFmpeg
Write-Host "[3/3] Đang tải FFmpeg..." -ForegroundColor Cyan
$ffZip = Join-Path $runtimeDir "ffmpeg.zip"
$ffUrl = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
try {
    Invoke-WebRequest -Uri $ffUrl -OutFile $ffZip -UseBasicParsing
    Expand-Archive -Path $ffZip -DestinationPath (Join-Path $runtimeDir "ff_temp") -Force
    $bin = Get-ChildItem -Path (Join-Path $runtimeDir "ff_temp") -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
    if ($bin) {
        Copy-Item (Join-Path $bin.DirectoryName "*") $ffDir -Force
    }
    Remove-Item (Join-Path $runtimeDir "ff_temp") -Recurse -Force
    Remove-Item $ffZip -Force
} catch {
    Write-Warning "Không thể tải FFmpeg: $_"
}

Write-Host "Hoàn tất chuẩn bị môi trường!" -ForegroundColor Green

