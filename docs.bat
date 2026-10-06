@echo off
title SoftForge - Documentacao Offline
cd /d "%~dp0docs"

echo ======================================================
echo    SoftForge - Servidor de Documentacao Offline (HTML)
echo ======================================================
echo.

if not exist "node_modules" (
    echo [*] Instalando dependencias do VitePress...
    call npm install
)

if not exist ".vitepress\dist" (
    echo [*] Gerando arquivos HTML estaticos com VitePress...
    call npx vitepress build
)

echo [*] Abrindo documentacao em: http://localhost:5174
start http://localhost:5174

echo [*] Servindo arquivos HTML estaticos da pasta .vitepress\dist...
call npx vitepress preview --port 5174
pause
