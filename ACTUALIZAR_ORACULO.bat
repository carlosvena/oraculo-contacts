@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Falta el entorno local. Ejecute INSTALAR_ORACULO.bat.
  pause
  exit /b 1
)
echo Actualizando dependencias locales sin borrar sesiones ni datos...
".venv\Scripts\python.exe" -m pip install --upgrade -e ".[ui]"
if errorlevel 1 (
  echo [ERROR] No se pudo actualizar. Sus datos no fueron modificados.
  pause
  exit /b 1
)
echo Actualizacion finalizada. No se borraron sesiones guardadas.
pause
exit /b 0

