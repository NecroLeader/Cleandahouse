@echo off
:: Saca Cleandahouse del inicio de Windows.
:: El programa deja de arrancar solo al encender la PC.
:: No borra nada mas — tus archivos y configuracion quedan intactos.
set LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Cleandahouse.lnk
if exist "%LNK%" (
    del "%LNK%"
    echo Removido del inicio de Windows.
) else (
    echo Cleandahouse no estaba instalado en el inicio.
)
pause
