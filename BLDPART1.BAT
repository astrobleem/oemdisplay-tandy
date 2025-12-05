@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16
echo Starting Build Part 1... > ..\..\BUILD.LOG
del *.obj
del *.map
del *.sym
del tandy16.drv
dir *.asm >> ..\..\BUILD.LOG
echo Assembling Part 1... >> ..\..\BUILD.LOG
masm -I. -v -Mx tandy.asm,tandy.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx cursors.asm,cursors.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx inquire.asm,inquire.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx setmode.asm,setmode.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx disable.asm,disable.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx color.asm,color.obj; >> ..\..\BUILD.LOG
cd ..\..

