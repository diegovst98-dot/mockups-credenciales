@echo off
chcp 65001 >nul
cd /d "%~dp0"
py publicar.py %1
pause
