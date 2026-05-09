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
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --clean ^
  --name Cleandahouse ^
  --icon icon.ico ^
  --hidden-import pystray._win32 ^
  --collect-data customtkinter ^
  organizer.py

echo [4/4] Copiando config base a dist\...
if not exist dist\config.json copy config.default.json dist\config.json >nul

echo.
echo ================================================
echo  Ejecutable: dist\Cleandahouse.exe
echo  Para GitHub Release: zipear exe + config.json
echo ================================================
pause
