@echo off
title Asistencia K20 - Servicio unico (web + API)
echo ========================================================
echo   Asistencia K20 - web y API en un solo servicio
echo ========================================================
cd /d "%~dp0backend"
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en backend\venv.
    echo Ejecuta: python -m venv venv  y  pip install -r requirements.txt
    pause
    exit /b 1
)
if not exist "..\frontend\dist\index.html" (
    echo [AVISO] No existe frontend\dist. Compilando la web...
    pushd "..\frontend"
    if not exist "node_modules" call npm install
    call npm run build
    popd
)
echo.
echo Servidor en http://127.0.0.1:5173  (web + API)
echo Documentacion: http://127.0.0.1:5173/api/v1/docs
echo Cierra esta ventana o pulsa Ctrl+C para detenerlo.
echo.
call venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 5173
pause
