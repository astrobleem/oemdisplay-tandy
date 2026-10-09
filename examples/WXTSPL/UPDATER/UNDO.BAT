@ECHO OFF
IF NOT "%1"=="" GOTO END
FASTSET RESTORE C:\WINDOWS C:\WINXT
IF ERRORLEVEL 1 GOTO FAIL
ECHO Original wave launchers restored. HELP02 helper evidence is retained.
GOTO END
:FAIL
ECHO Restore refused or incomplete. Preserve all journals and sidecars.
:END
