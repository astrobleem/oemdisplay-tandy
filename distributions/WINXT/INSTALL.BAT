@ECHO OFF
REM Run from the flat WINXT source/support directory at a real DOS prompt.
IF NOT EXIST TINST.EXE GOTO SOURCE
TINST.EXE %1 %2 %3 %4 %5 %6 %7 %8 %9
IF ERRORLEVEL 1 GOTO FAILED
WINXT.BAT SETUP
GOTO DONE
:SOURCE
ECHO TINST.EXE missing. Change to the complete WINXT folder first.
GOTO DONE
:FAILED
ECHO Installation stopped safely. Setup was not started.
:DONE
