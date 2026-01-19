@echo off
echo =====================================
echo Deploy Django - Windows + NSSM
echo =====================================

set NSSM=D:\Web\NSSM\nssm-2.24\win64\nssm.exe

set PROJECT_DIR=D:\Web\Sitios\corporativeune-intranet
set VENV_DIR=D:\Web\Sitios\corporativeune-intranet\.venv
set PYTHON=%VENV_DIR%\Scripts\python.exe
set MANAGE=%PROJECT_DIR%\manage.py

set REQUIREMENTS=D:\Web\Sitios\corporativeune-intranet\requirements.txt

REM === Servicios ===
set DJANGO_SERVICE=corporativoune_intranet
set CELERY_SERVICE=corporativoune_intranet_celery_worker

echo 🛑 Deteniendo servicios...
%NSSM% stop %DJANGO_SERVICE%
%NSSM% stop %CELERY_SERVICE%

timeout /t 5 /nobreak >nul

echo Instalando Librerias...
%PYTHON% -m pip install -r %REQUIREMENTS%

if %errorlevel% neq 0 (
    echo Error en pip install -r requirements.txt
    pause
    exit /b 1
)

echo 🧱 Ejecutando migraciones...
%PYTHON% %MANAGE% migrate --noinput

if %errorlevel% neq 0 (
    echo Error en migrate
    pause
    exit /b 1
)

echo Ejecutando collectstatic...
%PYTHON% %MANAGE% collectstatic --noinput

if %errorlevel% neq 0 (
    echo Error en collectstatic
    pause
    exit /b 1
)

echo Iniciando servicios...
%NSSM% start %DJANGO_SERVICE%
%NSSM% start %CELERY_SERVICE%

echo Deploy terminado correctamente
pause
