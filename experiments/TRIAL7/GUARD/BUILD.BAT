@ECHO OFF
REM Run in this SOURCE directory, with your own licensed MSC 6 toolchain.
REM Set PATH, INCLUDE and LIB yourself. LINK4 must be v5.x, not LINK v3.x.
REM DOS small model, strict 8086, no Windows or protected-mode options.
CL /nologo /c /AS /G0 /W3 /Os T7SAFE.C
IF ERRORLEVEL 1 GOTO BAD
LINK4 T7SAFE.OBJ,T7SAFE.EXE,T7SAFE.MAP,SLIBCE.LIB;
IF ERRORLEVEL 1 GOTO BAD
ECHO Built T7SAFE.EXE locally. Review and test before replacing any program.
GOTO DONE
:BAD
ECHO Build failed. No runtime package files were replaced.
:DONE
