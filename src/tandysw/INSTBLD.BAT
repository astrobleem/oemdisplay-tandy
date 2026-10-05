@ECHO OFF
REM Microsoft C 6.0, real DOS, small model, 8086/8088 code generation.
CL /AS /G0 /W3 TINST.C > BUILD.LOG
IF ERRORLEVEL 1 GOTO FAILED
ECHO Build succeeded.>>BUILD.LOG
GOTO DONE
:FAILED
ECHO Build FAILED.>>BUILD.LOG
:DONE
