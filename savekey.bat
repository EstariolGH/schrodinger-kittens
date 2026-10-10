@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo  =====================================================
echo    Котята Шрёдингера: сохраняем ключ IBM Quantum
echo  =====================================================
echo.

set "VPY=.venv\Scripts\python.exe"
if exist "%VPY%" goto have_venv
echo  Сначала нужно запустить install.bat - он установит Python и Qiskit.
echo  Потом запустите savekey.bat ещё раз.
goto end_fail

:have_venv
if exist "apikey.json" goto run
echo  Файл apikey.json рядом не найден.
echo.
echo  Можно закрыть это окно, положить скачанный с IBM apikey.json
echo  в эту папку и запустить savekey.bat ещё раз.
echo.
echo  Или вставить ключ прямо сейчас: скопируйте его на сайте IBM,
echo  щёлкните здесь правой кнопкой мыши и нажмите Enter.
echo  Символы при вводе не видны - так и задумано.
echo.

:run
"%VPY%" save_key.py
if errorlevel 1 goto end_fail

if not exist "apikey.json" goto done
echo.
choice /C YN /M " Удалить apikey.json сейчас? Ключ уже сохранён, файл больше не нужен (Y - да, N - нет)"
if errorlevel 2 goto keep_file
del /q "apikey.json"
echo  Файл apikey.json удалён.
goto done

:keep_file
echo  Хорошо, файл оставлен. Не выкладывайте его в интернет и не показывайте на скриншотах.

:done
echo.
echo  Теперь можно запускать котов на настоящем квантовом компьютере:
echo  start.bat, пункт 5.
echo.
pause
exit /b 0

:end_fail
echo.
pause
exit /b 1
