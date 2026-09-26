@echo off
setlocal
cd /d "%~dp0"

echo Installing application dependencies and PyInstaller...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed

echo Building StikGame.exe...
py -m PyInstaller --noconfirm --clean --onefile --console --name StikGame --add-data "templates;templates" --collect-binaries vgamepad --collect-all charset_normalizer --hidden-import engineio.async_drivers.threading server.py
if errorlevel 1 goto failed

echo.
echo Build complete: dist\StikGame.exe
echo Install ViGEmBus on this PC before running the EXE.
pause
exit /b 0

:failed
echo.
echo Build failed. Review the error above.
pause
exit /b 1