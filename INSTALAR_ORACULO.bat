@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python 3.11 o posterior no esta instalado o no esta en PATH.
    echo Instale Python desde https://www.python.org/ y vuelva a intentarlo.
    pause
    exit /b 1
  )
  set "PYTHON=python"
) else (
  set "PYTHON=py -3"
)

if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual local...
  %PYTHON% -m venv .venv
  if errorlevel 1 goto :error
)

echo Instalando ORACULO CONTACTS y su interfaz visual...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -e ".[ui]"
if errorlevel 1 goto :error

echo.
echo Instalacion finalizada correctamente.
echo Ya puede hacer doble clic en INICIAR_ORACULO.bat.
pause
exit /b 0

:error
echo.
echo [ERROR] La instalacion no pudo completarse.
echo Revise su conexion a Internet y los mensajes anteriores.
pause
exit /b 1

