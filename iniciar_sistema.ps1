# Inicia (o reutiliza) el Sistema de Asistencia K20 como UN SOLO servicio.
# Un único proceso sirve la web compilada y la API en el mismo puerto (5173),
# por lo que no hace falta Node ni un segundo servidor.
#
# Uso: clic derecho > Ejecutar con PowerShell, o:  .\iniciar_sistema.ps1

$ErrorActionPreference = "SilentlyContinue"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$puerto = if ($env:APP_PORT) { $env:APP_PORT } else { 5173 }
$baseUrl = "http://127.0.0.1:$puerto"
$python = Join-Path $rootDir "backend\venv\Scripts\python.exe"
$dist = Join-Path $rootDir "frontend\dist"

function Test-Servicio($url) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing $url -TimeoutSec 3
        return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500)
    } catch {
        return $false
    }
}

# Procesos del proyecto (backend unificado o Vite de desarrollo)
function Get-PidsProyecto {
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe' or Name = 'node.exe'" | Where-Object {
        $cmd = $_.CommandLine
        $cmd -and $cmd -like "*asistencia-k20*" -and (
            $cmd -like "*uvicorn*" -or $cmd -like "*vite*" -or $cmd -like "*npm*run dev*"
        )
    } | Select-Object -ExpandProperty ProcessId
}

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Sistema de Control de Asistencia K20 - ZKTeco" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

if (-not (Test-Path $python)) {
    Write-Host "[ERROR] No se encontro el entorno virtual: $python" -ForegroundColor Red
    Write-Host "Crea el entorno con: python -m venv venv y pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

if (-not (Test-Path (Join-Path $dist "index.html"))) {
    Write-Host "[AVISO] No existe la web compilada en frontend\dist." -ForegroundColor Yellow
    Write-Host "Ejecuta una vez: cd frontend; npm install; npm run build" -ForegroundColor Yellow
}

if (Test-Servicio "$baseUrl/health") {
    Write-Host "`nEl sistema ya esta funcionando en $baseUrl" -ForegroundColor Green
} else {
    $stale = Get-PidsProyecto
    if ($stale) {
        Write-Host "`nDetectado un servicio anterior que no responde. Reiniciando..." -ForegroundColor Yellow
        $stale | ForEach-Object { Stop-Process -Id $_ -Force }
        Start-Sleep -Seconds 2
    } else {
        Write-Host "`nIniciando el servicio (web + API) en $baseUrl ..." -ForegroundColor Yellow
    }

    $tarea = Get-ScheduledTask -TaskName "AsistenciaK20" -ErrorAction SilentlyContinue
    if (-not $tarea) {
        # Primera vez: crear la tarea oculta (no abre ninguna ventana).
        Write-Host "  Creando el arranque automatico (tarea AsistenciaK20)..." -ForegroundColor DarkGray
        $accion = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$rootDir\servicio_k20.ps1`"" `
            -WorkingDirectory $rootDir
        $disparador = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
        $ajustes = New-ScheduledTaskSettingsSet `
            -Hidden `
            -StartWhenAvailable `
            -RestartCount 5 `
            -RestartInterval (New-TimeSpan -Minutes 1) `
            -ExecutionTimeLimit ([TimeSpan]::Zero) `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries
        Register-ScheduledTask `
            -TaskName "AsistenciaK20" `
            -Action $accion `
            -Trigger $disparador `
            -Settings $ajustes `
            -Description "Asistencia K20: web y API en http://127.0.0.1:$puerto" `
            -Force | Out-Null
    }
    Write-Host "  Iniciando mediante el arranque automatico (tarea AsistenciaK20, sin ventanas)..." -ForegroundColor DarkGray
    Start-ScheduledTask -TaskName "AsistenciaK20"
    $listo = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        if (Test-Servicio "$baseUrl/health") { $listo = $true; break }
    }
    if ($listo) {
        Write-Host "  Servicio listo." -ForegroundColor Green
    } else {
        Write-Host "  ADVERTENCIA: el servicio no respondio. Revisa su ventana." -ForegroundColor Red
    }
}

# Aviso si MySQL no esta disponible (la web lo mostrara con boton Reintentar)
try {
    $r = Invoke-WebRequest -UseBasicParsing "$baseUrl/api/v1/trabajadores?per_page=1" -Headers @{ "X-API-Key" = "k20-access-token-dev" } -TimeoutSec 8
} catch {
    Write-Host "`n[AVISO] La base de datos MySQL no responde. Inicia MySQL (Laragon) y usa 'Reintentar' en la web." -ForegroundColor Yellow
}

Write-Host "`nAplicacion: $baseUrl" -ForegroundColor White
Write-Host "API Docs:   $baseUrl/api/v1/docs" -ForegroundColor White
Write-Host "`nPuedes cerrar el navegador y volver a abrirlo cuando quieras;" -ForegroundColor DarkGray
Write-Host "el servicio sigue activo en segundo plano hasta que ejecutes detener_sistema.ps1." -ForegroundColor DarkGray

Start-Process $baseUrl
