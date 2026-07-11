@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] No se encontro el entorno virtual.
  echo Ejecute primero INSTALAR_ORACULO.bat.
  pause
  exit /b 1
)

echo Iniciando ORACULO CONTACTS en modo seguro de solo lectura...
echo El navegador se abrira automaticamente. Para detener, cierre esta ventana.
".venv\Scripts\python.exe" -m oraculo_contacts ui
if errorlevel 1 (
  echo.
  echo [ERROR] No se pudo iniciar ORACULO CONTACTS.
  echo Pruebe ejecutar nuevamente INSTALAR_ORACULO.bat.
  pause
  exit /b 1
)

endlocal

