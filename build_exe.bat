@echo off
rem Builds Slayer.exe (the window version) and zips it up to send to someone.
rem Double-click this file in the game folder. It takes a minute or two.
rem   Result: dist\Slayer.zip  (and dist\Slayer\Slayer.exe, if you want to try it first)

cd /d "%~dp0"

rem Use "python" if it works, otherwise the "py" launcher.
set PY=python
python --version >nul 2>nul || set PY=py

echo Installing/updating PyInstaller...
%PY% -m pip install --upgrade pyinstaller || goto failed

echo.
echo Building Slayer.exe...
%PY% -m PyInstaller --noconfirm --clean Slayer.spec || goto failed

echo.
echo Zipping it up...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\Slayer' -DestinationPath 'dist\Slayer.zip' -Force" || goto failed

echo.
echo ============================================================
echo  Done!  Send dist\Slayer.zip
echo  To play: unzip it, open the Slayer folder, double-click Slayer.exe
echo ============================================================
echo.
pause
exit /b 0

:failed
echo.
echo Something went wrong. Copy the text above and show it to Claude.
pause
exit /b 1
