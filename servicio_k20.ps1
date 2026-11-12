# Ejecuta el servicio web + API del Sistema de Asistencia K20.
# Lo usa la tarea programada de inicio automatico (instalar_autostart.ps1).
# No hace falta ejecutarlo a mano: usa iniciar_sistema.ps1.

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$puerto = if ($env:APP_PORT) { $env:APP_PORT } else { 5173 }

Set-Location (Join-Path $rootDir "backend")
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
$log = Join-Path (Get-Location) "logs\servidor.log"

# Rotacion simple: si el registro supera 5 MB se archiva y se empieza otro.
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 5MB)) {
    Move-Item -Force $log "$log.old"
}

"=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') iniciando servicio en puerto $puerto ===" | Out-File -Append -Encoding utf8 $log

& ".\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port $puerto 2>&1 | Out-File -Append -Encoding utf8 $log
