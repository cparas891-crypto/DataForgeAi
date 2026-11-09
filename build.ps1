Write-Host ""
Write-Host "========================================"
Write-Host " DataForge AI Build"
Write-Host "========================================"
Write-Host ""

Write-Host "Installing build dependencies..."

python -m pip install --upgrade pyinstaller

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller installation failed."
    exit 1
}

Write-Host ""
Write-Host "Removing previous build..."

if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

Write-Host ""
Write-Host "Building DataForge AI..."

python -m PyInstaller `
    --clean `
    --noconfirm `
    DataForgeAI.spec

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "DataForge build FAILED."
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host " BUILD COMPLETE"
Write-Host "========================================"
Write-Host ""

Write-Host "Executable:"
Write-Host ".\dist\DataForgeAI\DataForgeAI.exe"
Write-Host ""