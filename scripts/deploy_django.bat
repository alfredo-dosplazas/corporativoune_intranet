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

set DJANGO_SERVICE=corporativoune_intranet
set CELERY_SERVICE=corporativoune_intranet_celery_worker
set BEAT_SERVICE=corporativoune_intranet_celery_beat

echo [1/6] Bajando cambios del repositorio...
git pull origin
if %errorlevel% neq 0 (
    echo [ERROR] Falla en git pull. Abortando deploy.
    pause
    exit /b 1
)

echo [2/6] Instalando Librerias...
%PYTHON% -m pip install -r %REQUIREMENTS% --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Falla en pip install. Abortando deploy.
    pause
    exit /b 1
)

echo [3/6] Ejecutando migraciones de base de datos...
%PYTHON% %MANAGE% migrate --noinput
if %errorlevel% neq 0 (
    echo [ERROR] Falla en migraciones. Abortando deploy.
    pause
    exit /b 1
)

echo [4/6] Recopilando archivos estaticos (Collectstatic)...
%PYTHON% %MANAGE% collectstatic --noinput
if %errorlevel% neq 0 (
    echo [ERROR] Falla en collectstatic. Abortando deploy.
    pause
    exit /b 1
)

echo [5/6] Deteniendo servicios en segundo plano...
%NSSM% stop %CELERY_SERVICE%
%NSSM% stop %BEAT_SERVICE%
%NSSM% stop %DJANGO_SERVICE%

echo [6/6] Reiniciando servicios actualizados...
%NSSM% start %DJANGO_SERVICE%
%NSSM% start %CELERY_SERVICE%
%NSSM% start %BEAT_SERVICE%

echo =====================================
echo  Deploy terminado con exito! 🚀
echo =====================================
pause