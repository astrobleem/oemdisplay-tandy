@ECHO OFF
REM Windows host entry point; no DOS emulator or PowerShell required.
SETLOCAL
WHERE py > NUL 2>&1
IF ERRORLEVEL 1 GOTO PYTHON
py -3 "%~dp0MAKEDISK.PY" %*
EXIT /B %ERRORLEVEL%
:PYTHON
WHERE python > NUL 2>&1
IF ERRORLEVEL 1 GOTO MISSING
python "%~dp0MAKEDISK.PY" %*
EXIT /B %ERRORLEVEL%
:MISSING
ECHO Python 3.8 or newer is required. Install it from python.org.
EXIT /B 1
