@echo off
chcp 65001 > nul
title Simulador de Reemplazo de Páginas
cd /d "%~dp0"
python main.py
pause
