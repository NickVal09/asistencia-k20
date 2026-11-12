# Inicia el proceso de sincronizacion automatica con el K20 (daemon APScheduler).
# Por defecto solo arranca si SYNC_AUTOMATICA_ENABLED=True en backend/.env.
# Uso: .\\iniciar_sync_auto.ps1 [-Force]
param(
    [switch]$Force
)

$ErrorActionPreference = "SilentlyContinue"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $rootDir "backend\\venv\\Scripts\\python.exe"
$script = Join-Path $rootDir "backend\\scripts\\sync_auto.py"

if (-not (Test-Path $python)) {
    Write-Host "[ERROR] No se encontro el entorno virtual: $python" -ForegroundColor Red
    exit 1
}

$argumentos = @($script)
if ($Force) { $argumentos += "--force" }

$proc = Start-Process -FilePath $python -ArgumentList $argumentos -WorkingDirectory (Join-Path $rootDir "backend") -PassThru -WindowStyle Minimized
Write-Host "Daemon de sincronizacion automatica iniciado (PID $($proc.Id))." -ForegroundColor Green
Write-Host "Para detenerlo: .\\detener_sync_auto.ps1" -ForegroundColor DarkGray
