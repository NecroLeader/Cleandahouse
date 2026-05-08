@echo off
:: Agrega el organizer al inicio de Windows usando pythonw (sin consola)
setlocal

set SCRIPT=%~dp0organizer.py
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set LNK=%STARTUP%\Downloads Organizer.lnk

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%LNK%'); ^
   $s.TargetPath = 'pythonw'; ^
   $s.Arguments = '\"%SCRIPT%\"'; ^
   $s.WorkingDirectory = '%~dp0'; ^
   $s.Description = 'Downloads Organizer'; ^
   $s.Save()"

if exist "%LNK%" (
    echo Listo. El organizer va a arrancar automaticamente con Windows.
    echo Atajo creado en: %LNK%
) else (
    echo Error al crear el atajo.
)
pause
