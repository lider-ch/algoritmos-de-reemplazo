@echo off
chcp 65001 > nul
title Simulador de Reemplazo de Páginas - Instalador

echo.
echo ============================================================
echo   SIMULADOR DE REEMPLAZO DE PÁGINAS EN MEMORIA
echo ============================================================
echo.

:: Check if Python is installed
python --version 2>nul | findstr /i "python" > nul
if %errorlevel% neq 0 (
    echo [!] Python no encontrado. Intentando descargar e instalar Python 3.11...
    echo.

    :: Download Python installer
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'}"

    if exist "%TEMP%\python_installer.exe" (
        echo [*] Instalando Python 3.11 (puede tardar unos minutos)...
        "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
        del "%TEMP%\python_installer.exe"
        echo [OK] Python instalado. Reinicia este script.
        pause
        exit /b
    ) else (
        echo [ERROR] No se pudo descargar Python.
        echo Por favor instale Python manualmente desde: https://www.python.org/downloads/
        echo Asegurese de marcar "Add Python to PATH" durante la instalacion.
        pause
        exit /b 1
    )
)

echo [OK] Python encontrado:
python --version
echo.

:: Install dependencies
echo [*] Instalando dependencias (rich, matplotlib, numpy, gitpython)...
python -m pip install rich matplotlib numpy gitpython --quiet --upgrade
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar dependencias.
    echo Intente manualmente: python -m pip install rich matplotlib numpy gitpython
    pause
    exit /b 1
)

echo [OK] Dependencias instaladas.
echo.

:: Initialize git repo
if not exist ".git" (
    echo [*] Inicializando repositorio Git...
    git init
    git add .
    git commit -m "feat: proyecto inicial - simulador de reemplazo de páginas"
    echo [OK] Repositorio Git inicializado.
    echo.
)

:: Run the program
echo [*] Iniciando el simulador...
echo.
python main.py
pause
