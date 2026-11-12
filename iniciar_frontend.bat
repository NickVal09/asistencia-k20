@echo off
title Asistencia K20 - Desarrollo (Vite con recarga en caliente)
echo ========================================================
echo   Modo DESARROLLO: Vite en http://127.0.0.1:5174
echo ========================================================
echo.
echo Requiere que el servicio principal este activo en 5173:
echo   .\iniciar_sistema.ps1
echo.
echo Abre luego http://127.0.0.1:5174 para ver los cambios en vivo.
echo.
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [INFO] Instalando dependencias...
    call npm install
)
set VITE_PORT=5174
set VITE_API_TARGET=http://127.0.0.1:5173
call npm run dev
pause
