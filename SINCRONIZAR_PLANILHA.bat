@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Sincronizar planilha -^> data\planilha.xlsx
py -3 scripts\sincronizar_planilha_desktop.py 2>nul
if errorlevel 1 python scripts\sincronizar_planilha_desktop.py 2>nul
if errorlevel 1 py scripts\sincronizar_planilha_desktop.py
echo.
pause
