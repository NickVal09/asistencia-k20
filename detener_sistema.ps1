# Detiene el servicio web + API del Sistema de Asistencia K20.
# Uso: .\detener_sistema.ps1

$ErrorActionPreference = "SilentlyContinue"

function Get-PidsProyecto {
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe' or Name = 'node.exe'" | Where-Object {
        $cmd = $_.CommandLine
        $cmd -and $cmd -like "*asistencia-k20*" -and (
            $cmd -like "*uvicorn*" -or $cmd -like "*vite*" -or $cmd -like "*npm*run dev*"
        )
    } | Select-Object -ExpandProperty ProcessId
}

Write-Host "Deteniendo el servicio del Sistema de Asistencia K20..." -ForegroundColor Cyan

# Si existe la tarea de arranque automatico, se detiene para que no lo reinicie.
$tarea = Get-ScheduledTask -TaskName "AsistenciaK20" -ErrorAction SilentlyContinue
if ($tarea -and $tarea.State -eq "Running") {
    Stop-ScheduledTask -TaskName "AsistenciaK20"
    Write-Host "  Tarea programada AsistenciaK20 detenida." -ForegroundColor Yellow
}

$pids = Get-PidsProyecto
if ($pids) {
    $pids | ForEach-Object { Stop-Process -Id $_ -Force }
    Write-Host "  Servicio detenido (PID: $($pids -join ', '))" -ForegroundColor Yellow
} else {
    Write-Host "  El servicio no estaba en ejecucion." -ForegroundColor DarkGray
}

Write-Host "Listo." -ForegroundColor Green
