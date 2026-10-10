@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo  =====================================================
echo    Котята Шрёдингера: установка всего необходимого
echo  =====================================================
echo.

set "PYEXE="

rem --- 1. Ищем уже установленный Python 3.11+ ---------------------------
where py >nul 2>nul
if errorlevel 1 goto try_python
for /f "delims=" %%i in ('py -3 -c "import sys;print(sys.executable if sys.version_info>=(3,11) else '')" 2^>nul') do set "PYEXE=%%i"
if defined PYEXE goto have_python

:try_python
for /f "delims=" %%i in ('python -c "import sys;print(sys.executable if sys.version_info>=(3,11) else '')" 2^>nul') do set "PYEXE=%%i"
if defined PYEXE goto have_python

rem --- 2. Python не найден: ставим ---------------------------------------
echo  Python 3.11+ не найден. Устанавливаю Python 3.13...
echo.
where winget >nul 2>nul
if errorlevel 1 goto download_python

winget install -e --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
goto find_installed

:download_python
echo  winget недоступен, скачиваю установщик с python.org...
curl -L -o "%TEMP%\python-installer.exe" https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe
if errorlevel 1 goto fail_download
"%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1
del "%TEMP%\python-installer.exe" >nul 2>nul

:find_installed
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PYEXE if exist "%ProgramFiles%\Python313\python.exe" set "PYEXE=%ProgramFiles%\Python313\python.exe"
if defined PYEXE goto have_python
echo.
echo  Не получилось найти Python после установки.
echo  Закройте это окно, откройте новое и запустите install.bat ещё раз.
echo  Если не поможет - поставьте Python вручную, см. README, шаг 1.
goto end_fail

:have_python
echo  Найден Python: %PYEXE%
"%PYEXE%" --version
echo.

rem --- 3. Виртуальное окружение ------------------------------------------
if exist ".venv\Scripts\python.exe" goto have_venv
echo  Создаю виртуальное окружение .venv ...
"%PYEXE%" -m venv .venv
if errorlevel 1 goto fail_venv

:have_venv
set "VPY=.venv\Scripts\python.exe"

rem --- 4. Библиотеки -----------------------------------------------------
echo  Устанавливаю Qiskit и остальные библиотеки. Это займёт несколько минут...
echo.
"%VPY%" -m pip install --upgrade pip --quiet
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto fail_pip

rem --- 5. Проверка -------------------------------------------------------
echo.
"%VPY%" -c "import qiskit, qiskit_aer, qiskit_ibm_runtime, matplotlib; print(' Qiskit', qiskit.__version__, '- всё на месте!')"
if errorlevel 1 goto fail_pip

echo.
echo  =====================================================
echo    Готово!
echo.
echo    Запускайте котов двойным щелчком по start.bat
echo    или из командной строки:  .venv\Scripts\python.exe cats.py
echo  =====================================================
echo.
pause
exit /b 0

:fail_download
echo.
echo  Не удалось скачать Python. Проверьте интернет или поставьте Python вручную,
echo  см. README, шаг 1.
goto end_fail

:fail_venv
echo.
echo  Не удалось создать виртуальное окружение. См. README, раздел про проблемы.
goto end_fail

:fail_pip
echo.
echo  Библиотеки установились с ошибкой. Проверьте интернет и запустите install.bat ещё раз.
goto end_fail

:end_fail
echo.
pause
exit /b 1
