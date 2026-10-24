@ECHO OFF
REM Only inside an explicitly allocated, bounded emulator build slot.
REM T: = verified pinned external legacy toolchain, D: = fresh source copy.
PATH=T:\BIN
SET INCLUDE=T:\DDK\286\INC;T:\INCLUDE
SET LIB=T:\LIB
CL /nologo /c /G0 /Gw /AS /W3 /Od C16MET.C > BUILD.LOG
IF ERRORLEVEL 1 GOTO FAIL
LINK4 /NOE /NOD C16MET.OBJ,C16MET.EXE,C16MET.MAP,T:\LIB\SLIBCEW.LIB T:\LIB\LIBW.LIB,C16MET.DEF; >> BUILD.LOG
IF ERRORLEVEL 1 GOTO FAIL
ECHO PASS>DONE.TXT
GOTO END
:FAIL
ECHO FAIL>DONE.TXT
:END
EXIT
