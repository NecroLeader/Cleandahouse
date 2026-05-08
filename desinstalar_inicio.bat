@echo off
set LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Downloads Organizer.lnk
if exist "%LNK%" (
    del "%LNK%"
    echo Removido del inicio de Windows.
) else (
    echo No estaba instalado en el inicio.
)
pause
