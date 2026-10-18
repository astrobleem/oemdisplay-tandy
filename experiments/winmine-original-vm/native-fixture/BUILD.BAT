@echo off
echo BUILD=RUNNING > BUILD.RESULT
set PATH=C:\BIN
set INCLUDE=C:\DDK\286\INC;C:\INCLUDE
set LIB=C:\LIB
S:
cd \
if exist W16CALL.EXE del W16CALL.EXE
if exist W16CALL.OBJ del W16CALL.OBJ
MASM /Ml W16CALL.ASM,W16CALL.OBJ,NUL,NUL > W16ASM.LOG
if errorlevel 1 goto asm_failed
LINK4 /NOE W16CALL.OBJ,W16CALL.EXE,NUL,,, >> W16ASM.LOG
if errorlevel 1 goto asm_link_failed
if not exist W16CALL.EXE goto asm_link_failed
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
:asm_failed
echo BUILD=ASSEMBLY_FAIL > BUILD.RESULT
exit
:asm_link_failed
echo BUILD=ASSEMBLY_LINK_FAIL > BUILD.RESULT
exit
