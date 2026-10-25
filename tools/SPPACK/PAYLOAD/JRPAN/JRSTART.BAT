ECHO OFF
C:\JRPAN\JRGUARD.COM
IF ERRORLEVEL 1 GOTO FAIL
C:
CD \WINDOWS
WIN /R
GOTO END
:FAIL
ECHO The PCjr video page must be reserved before Windows starts.
:END
