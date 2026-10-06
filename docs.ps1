# SoftForge - Inicializador da Documentacao Offline
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DocsDir = Join-Path $ScriptDir "docs"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   SoftForge - Servidor de Documentacao Offline (HTML)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $DocsDir

if (-not (Test-Path "node_modules")) {
    Write-Host "[*] Instalando dependencias do VitePress..." -ForegroundColor Yellow
    npm.cmd install
}

if (-not (Test-Path ".vitepress\dist")) {
    Write-Host "[*] Gerando arquivos HTML estaticos com VitePress..." -ForegroundColor Yellow
    npx.cmd vitepress build
}

Write-Host "[*] Abrindo documentacao em: http://localhost:5174" -ForegroundColor Green
Start-Process "http://localhost:5174"

Write-Host "[*] Servindo arquivos HTML estaticos da pasta .vitepress\dist..." -ForegroundColor Green
npx.cmd vitepress preview --port 5174
