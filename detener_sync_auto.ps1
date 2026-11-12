# Detiene el proceso de sincronizacion automatica con el K20.
$ErrorActionPreference = "SilentlyContinue"

$pids = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object {
    $cmd = $_.CommandLine
    $cmd -and $cmd -like "*asistencia-k20*" -and $cmd -like "*sync_auto.py*"
} | Select-Object -ExpandProperty ProcessId

if ($pids) {
    $pids | ForEach-Object { Stop-Process -Id $_ -Force }
    Write-Host "Daemon de sincronizacion automatica detenido (PID: $($pids -join ', '))." -ForegroundColor Yellow
} else {
    Write-Host "El daemon no estaba en ejecucion." -ForegroundColor DarkGray
}
