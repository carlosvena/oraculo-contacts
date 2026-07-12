@echo off
setlocal
cd /d "%~dp0"

echo Verificando ORACULO CONTACTS...
where py >nul 2>nul
if errorlevel 1 where python >nul 2>nul
if errorlevel 1 goto :python_error
echo [OK] Python disponible.

if not exist ".venv\Scripts\python.exe" goto :venv_error
echo [OK] Entorno virtual encontrado.

".venv\Scripts\python.exe" -c "import streamlit; import oraculo_contacts; from oraculo_contacts.infrastructure.contact_import_service import import_contacts; print('[OK] Importaciones principales correctas. Version', oraculo_contacts.__version__)"
if errorlevel 1 goto :import_error

".venv\Scripts\python.exe" -c "from pathlib import Path; from oraculo_contacts.infrastructure.contact_import_service import import_contacts; p=Path('src/oraculo_contacts/ui/demo_contacts.json'); r=import_contacts(p.name,p.read_text(encoding='utf-8')); assert len(r.contacts)>=10; print('[OK] Prueba rapida de datos:',len(r.contacts),'contactos ficticios.')"
if errorlevel 1 goto :test_error

netstat -ano | findstr ":8501" >nul
if errorlevel 1 (
  echo [OK] Puerto 8501 disponible.
) else (
  echo [AVISO] Puerto 8501 en uso. ORACULO puede estar abierto.
)

echo.
echo Diagnostico finalizado: ORACULO esta listo para iniciar.
pause
exit /b 0

:python_error
echo [ERROR] Python 3.11 o posterior no esta disponible.
goto :failed
:venv_error
echo [ERROR] Falta el entorno .venv. Ejecute INSTALAR_ORACULO.bat.
goto :failed
:import_error
echo [ERROR] Faltan componentes. Ejecute nuevamente INSTALAR_ORACULO.bat.
goto :failed
:test_error
echo [ERROR] La prueba rapida fallo. Revise la instalacion.
:failed
pause
exit /b 1

