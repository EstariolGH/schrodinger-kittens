@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "VPY=.venv\Scripts\python.exe"
if exist "%VPY%" goto menu
echo.
echo  Сначала нужно запустить install.bat - он всё установит.
echo.
pause
exit /b 1

:menu
cls
echo.
echo  =====================================
echo    Котята Шрёдингера
echo  =====================================
echo.
echo    1. Симулятор: общий атом - котят нет
echo    2. Симулятор: у каждого свой атом
echo    3. Модель шумного чипа IBM, без интернета
echo.
echo    4. Сохранить ключ IBM - один раз
echo    5. Настоящий квантовый компьютер IBM
echo.
echo    0. Выход
echo.
set "choice="
set /p "choice=  Ваш выбор: "

if "%choice%"=="1" "%VPY%" cats.py
if "%choice%"=="2" "%VPY%" cats.py --mode independent
if "%choice%"=="3" "%VPY%" cats.py --backend fake
if "%choice%"=="4" "%VPY%" save_key.py
if "%choice%"=="5" "%VPY%" cats.py --backend ibm --shots 4000
if "%choice%"=="0" exit /b 0

echo.
pause
goto menu
