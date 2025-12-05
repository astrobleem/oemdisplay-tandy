@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16
echo Starting Build Part 2... >> ..\..\BUILD.LOG
echo Assembling Part 2... >> ..\..\BUILD.LOG
masm -I. -v -Mx blkwhite.asm,blkwhite.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx chkstk.asm,chkstk.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx control.asm,control.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx fb.asm,fb.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx charwdth.asm,charwdth.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx -DLORES dither.asm,lodither.obj; >> ..\..\BUILD.LOG
cd ..\..

