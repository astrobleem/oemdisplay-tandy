@ECHO OFF
C:\WINXT\FIXXT.EXE REPAIR C:\WINDOWS C:\WINXT %1
IF ERRORLEVEL 1 GOTO BAD
C:\WINXT\CPSET.EXE APPLY C:\WINDOWS
IF ERRORLEVEL 1 GOTO BAD
ECHO Repair complete. Run C:\STARTXT to start Windows XT.
GOTO DONE
:BAD
ECHO Repair stopped at the stated error. Keep its temporary files for recovery.
:DONE
