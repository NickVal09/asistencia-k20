# Quita el arranque automatico del Sistema de Asistencia K20.
# Uso: .\quitar_autostart.ps1

$ErrorActionPreference = "SilentlyContinue"
$taskName = "AsistenciaK20"

Stop-ScheduledTask -TaskName $taskName
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
Write-Host "Arranque automatico eliminado (tarea '$taskName')." -ForegroundColor Green
Write-Host "El servicio actual puede seguir corriendo; detenlo con .\detener_sistema.ps1" -ForegroundColor DarkGray
