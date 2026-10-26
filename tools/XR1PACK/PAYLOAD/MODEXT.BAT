@ECHO OFF
IF "%1"=="" GOTO HELP
IF NOT "%1"=="/XR1" GOTO HELP
C:\WINXT\FIXXT.EXE REPAIR C:\WINDOWS C:\WINXT /XR1
IF ERRORLEVEL 1 GOTO BAD
C:\WINXT\CPSET.EXE APPLY C:\WINDOWS
IF ERRORLEVEL 1 GOTO BAD
ECHO XR1 selected. Run C:\STARTXT from plain DOS.
GOTO DONE
:HELP
ECHO This package supplies XR1. Use MODEXT /XR1 from plain DOS.
ECHO Other display profiles remain in their separate packages.
GOTO DONE
:BAD
ECHO Profile repair stopped. Read the stated error.
:DONE
