# SoftForge - Inicializador da Documentacao Offline
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DocsDir = Join-Path $ScriptDir "docs"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   SoftForge - Servidor de Documentacao Offline" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $DocsDir

if (-not (Test-Path "node_modules")) {
    Write-Host "[*] Instalando dependencias do VitePress..." -ForegroundColor Yellow
    npm.cmd install
}

Write-Host "[*] Abrindo documentacao no navegador: http://localhost:5174" -ForegroundColor Green
Start-Process "http://localhost:5174"

Write-Host "[*] Iniciando servidor VitePress..." -ForegroundColor Green
npx.cmd vitepress dev --port 5174
