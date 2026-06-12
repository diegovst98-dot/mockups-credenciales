@echo off
chcp 65001 >nul
echo.
echo  Instalando Mockups DISECOD...
set DESTINO=%LOCALAPPDATA%\MockupsDISECOD
mkdir "%DESTINO%" 2>nul
copy /Y "%~dp0MockupsDISECOD.exe" "%DESTINO%\" >nul
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Mockups DISECOD.lnk');$s.TargetPath='%DESTINO%\MockupsDISECOD.exe';$s.WorkingDirectory='%DESTINO%';$s.Save()"
echo  Listo: busca "Mockups DISECOD" en el escritorio.
echo.
pause
