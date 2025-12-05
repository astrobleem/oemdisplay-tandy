@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16
echo Testing Build... > ..\..\TEST.LOG
masm -I. -v -Mx color.asm,color.obj; >> ..\..\TEST.LOG
if exist color.obj echo COLOR.OBJ created >> ..\..\TEST.LOG
cd ..\..
exit
