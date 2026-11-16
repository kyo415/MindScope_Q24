@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title MindScope Q24 - Khoi dong website
color 0B

echo.
echo ========================================================
echo        MIND SCOPE - WEBSITE DU DOAN Q24 - FIX GIAO DIEN
echo ========================================================
echo.
echo [1/4] Kiem tra Python 64-bit tuong thich ...
set "PYLAUNCH="
where py >nul 2>&1
if not errorlevel 1 (
  for %%V in (3.13 3.12 3.11 3.14) do (
    if not defined PYLAUNCH (
      py -%%V -c "import sys,struct;assert struct.calcsize('P')==8" >nul 2>&1
      if not errorlevel 1 set "PYLAUNCH=py -%%V"
    )
  )
)
if not defined PYLAUNCH (
  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys,struct; assert (3,11)<=sys.version_info[:2]<=(3,14) and struct.calcsize('P')==8" >nul 2>&1
    if not errorlevel 1 set "PYLAUNCH=python"
  )
)
if not defined PYLAUNCH goto no_python
echo    Da tim thay: %PYLAUNCH%

echo.
echo [2/4] Chuan bi moi truong rieng cua du an ...
if exist ".venv_q24\Scripts\python.exe" (
  ".venv_q24\Scripts\python.exe" -c "import sys,struct;assert (3,11)<=sys.version_info[:2]<=(3,14) and struct.calcsize('P')==8" >nul 2>&1
  if errorlevel 1 (
    echo    Moi truong cu khong tuong thich, dang tao lai...
    rmdir /S /Q ".venv_q24"
  )
)
if not exist ".venv_q24\Scripts\python.exe" (
  %PYLAUNCH% -m venv ".venv_q24"
  if errorlevel 1 goto env_error
)
echo    OK: .venv_q24\Scripts\python.exe

echo.
echo [3/4] Cai thu vien co san, KHONG bien dich tu ma nguon ...
".venv_q24\Scripts\python.exe" -m pip install --disable-pip-version-check --only-binary=:all: -r "requirements.txt"
if errorlevel 1 goto pip_error

echo.
echo [4/4] Kiem tra 3 mo hinh va khoi dong website ...
".venv_q24\Scripts\python.exe" -c "from prediction_service import infer; a={k:1 for k in ['Q1','Q2','Q15','Q16','Q17','Q20','Q21','Q22','Q23','Q27']}; [infer(c,a) for c in ['Bhutan','Morocco','UAE']]; print('    OK: Bhutan, Morocco, UAE')"
if errorlevel 1 goto model_error

echo.
echo ========================================================
echo  WEBSITE:  http://127.0.0.1:5055
echo  Neu trang khong tu mo, dan dia chi tren vao Chrome.
echo  Giu cua so nay mo khi su dung. Bam Ctrl+C de dung.
echo ========================================================
echo.
start "" /B ".venv_q24\Scripts\python.exe" "open_browser.py"
".venv_q24\Scripts\python.exe" "app.py"
echo.
echo May chu da dung.
pause
exit /b 0

:no_python
color 0C
echo.
echo LOI: Khong tim thay Python 3.11 / 3.12 / 3.13 / 3.14 64-bit.
echo Neu ban dang co Python 3.15, no CHUA tuong thich voi model.
echo Hay cai Python 3.13 64-bit tai: https://www.python.org/downloads/
echo Chon Windows installer 64-bit, sau do chay lai file BAT.
goto fail
:env_error
color 0C
echo LOI: Khong tao duoc .venv_q24. Kiem tra quyen ghi thu muc.
goto fail
:pip_error
color 0C
echo LOI: Khong cai duoc thu vien. Kiem tra Internet va Python 64-bit.
goto fail
:model_error
color 0C
echo LOI: Khong mo duoc model. Kiem tra thu muc models/.
goto fail
:fail
echo.
echo Chup lai thong bao nay neu can ho tro.
pause
exit /b 1
