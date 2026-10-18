@echo off
echo BUILD=RUNNING > BUILD.RESULT
set PATH=C:\BIN
set INCLUDE=C:\DDK\286\INC;C:\INCLUDE
set LIB=C:\LIB
S:
cd \
CL /nologo /c /AS /G0 /Gw /Zp /Od W16APIN.C > BUILD.LOG
if errorlevel 1 goto compile_failed
LINK4 /NOD /NOE W16APIN.OBJ,W16APIN.EXE,NUL,C:\LIB\SLIBCEW.LIB C:\LIB\LIBW.LIB,W16APIN.DEF >> BUILD.LOG
if errorlevel 1 goto link_failed
echo BUILD=PASS > BUILD.RESULT
exit
:compile_failed
echo BUILD=COMPILE_FAIL > BUILD.RESULT
exit
:link_failed
echo BUILD=LINK_FAIL > BUILD.RESULT
exit
