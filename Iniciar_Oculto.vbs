' Inicia el Sistema de Asistencia K20 SIN abrir ninguna ventana de terminal.
' Doble clic sobre este archivo. El servicio queda en segundo plano y sigue
' funcionando aunque cierres el navegador o esta ventana.
'
' Equivale a ejecutar: iniciar_sistema.ps1 (pero oculto).

Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = base

comando = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & base & "\instalar_autostart.ps1"""
shell.Run comando, 0, True
