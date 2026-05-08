@echo off
:: Compila Cleandahouse en un .exe standalone con PyInstaller.
:: El resultado queda en la carpeta dist/ junto con config.json.
:: Distribuí esos dos archivos juntos — el usuario no necesita Python instalado.
:: Solo necesitas correr esto una vez (o cuando hagas cambios al codigo).
cd /d "%~dp0"

echo [1/4] Instalando dependencias...
pip install -r requirements.txt pyinstaller --quiet

echo [2/4] Generando icono...
python -c "from organizer import generate_icon_ico; generate_icon_ico(); print('icon.ico OK')"

echo [3/4] Compilando .exe...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name Cleandahouse ^
  --icon icon.ico ^
  --hidden-import pystray._win32 ^
  --collect-data customtkinter ^
  organizer.py

echo [4/4] Copiando config.json al directorio de salida...
copy config.json dist\config.json >nul

echo.
echo ================================================
echo  Listo!
echo  Ejecutable: dist\Cleandahouse.exe
echo  Copialo junto con config.json donde quieras.
echo ================================================
pause
