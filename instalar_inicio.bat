@echo off
:: Agrega Cleandahouse al inicio de Windows.
:: Después de ejecutar esto, el programa arranca automáticamente
:: cada vez que enciendas la PC, sin necesidad de abrir nada.
:: Para desinstalarlo del inicio, usá desinstalar_inicio.bat
setlocal

set SCRIPT=%~dp0organizer.py
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set LNK=%STARTUP%\Cleandahouse.lnk

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%LNK%'); ^
   $s.TargetPath = 'pythonw'; ^
   $s.Arguments = '\"%SCRIPT%\"'; ^
   $s.WorkingDirectory = '%~dp0'; ^
   $s.Description = 'Cleandahouse Downloads Organizer'; ^
   $s.Save()"

if exist "%LNK%" (
    echo Listo. Cleandahouse va a arrancar automaticamente con Windows.
) else (
    echo Error al crear el atajo. Proba ejecutar como administrador.
)
pause
