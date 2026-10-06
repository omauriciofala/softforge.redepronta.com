@echo off
title SoftForge - Documentacao Offline
cd /d "%~dp0docs"

echo ======================================================
echo    SoftForge - Servidor de Documentacao Offline
echo ======================================================
echo.

if not exist "node_modules" (
    echo [*] Instalando dependencias do VitePress...
    call npm install
)

echo [*] Abrindo documentacao no navegador: http://localhost:5174
start http://localhost:5174

echo [*] Iniciando servidor VitePress...
call npx vitepress dev --port 5174
pause
