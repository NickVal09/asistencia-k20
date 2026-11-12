# Instala el arranque automatico del Sistema de Asistencia K20 al iniciar sesion.
# Despues de esto NO necesitas ejecutar iniciar_sistema.ps1: al entrar a Windows
# el servicio queda arriba y http://127.0.0.1:5173 funciona directamente.
#
# Uso: clic derecho > Ejecutar con PowerShell, o:  .\instalar_autostart.ps1

$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskName = "AsistenciaK20"
$script = Join-Path $rootDir "servicio_k20.ps1"
$puerto = if ($env:APP_PORT) { $env:APP_PORT } else { 5173 }

if (-not (Test-Path $script)) {
    Write-Host "[ERROR] No se encontro $script" -ForegroundColor Red
    exit 1
}

$accion = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`"" `
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

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $accion `
        -Trigger $disparador `
        -Settings $ajustes `
        -Description "Asistencia K20: web y API en http://127.0.0.1:$puerto" `
        -Force | Out-Null
} catch {
    Write-Host "[ERROR] No se pudo crear la tarea programada: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Ejecuta esta ventana de PowerShell como Administrador e intentalo de nuevo." -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Arrancarlo ahora mismo si no esta corriendo
try {
    $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$puerto/health" -TimeoutSec 3
} catch {
    Start-ScheduledTask -TaskName $taskName
}

Write-Host "Arranque automatico instalado." -ForegroundColor Green
Write-Host "  Tarea: $taskName (al iniciar sesion en Windows)" -ForegroundColor White
Write-Host "  Web:   http://127.0.0.1:$puerto" -ForegroundColor White
Write-Host "`nPara quitarlo: .\quitar_autostart.ps1" -ForegroundColor DarkGray
Write-Host "Registro del servicio: backend\logs\servidor.log" -ForegroundColor DarkGray
