@echo off
:: Arranca Cleandahouse en segundo plano (sin consola).
:: Podés cerrar esta ventana tranquilamente — el programa sigue corriendo
:: y aparece como ícono de carpeta azul cerca del reloj de Windows.
cd /d "%~dp0"
start "" pythonw organizer.py
