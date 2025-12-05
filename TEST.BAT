@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16

echo Testing Part 4... > ..\..\TEST.LOG
masm -I. -v -Mx TGAVID.ASM,TGAVID.OBJ; >> ..\..\TEST.LOG
masm -I. -v -Mx cursor.asm,cursor.obj; >> ..\..\TEST.LOG
exit
