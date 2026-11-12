' Detiene el Sistema de Asistencia K20 SIN abrir ninguna ventana de terminal.

Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = base

comando = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & base & "\detener_sistema.ps1"""
shell.Run comando, 0, True
