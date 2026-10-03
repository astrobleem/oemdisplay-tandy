@echo off
PATH=C:\BIN;%PATH%
SET INCLUDE=C:\DDK\286\INC;C:\DDK\INC
SET LIB=C:\LIB
R:
cd \EGA
echo Core renderer build > BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\bitblt.asm,bitblt.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\cblt.asm,cblt.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\polyline.asm,polyline.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\scanline.asm,scanline.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\output.asm,output.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\pixel.asm,pixel.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\scanlr.asm,scanlr.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\rlstrblt.asm,rlstrblt.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\rlbldstr.asm,rlbldstr.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\realfix.asm,realfix.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\realpro.asm,realpro.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\dithers.asm,dithers.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\robject.asm,robject.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\colorinf.asm,colorinf.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\enum.asm,enum.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\colors.asm,colors.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\setmode.asm,setmode.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\chkstk.asm,chkstk.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\charwdth.asm,charwdth.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ..\fb.asm,fb.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T -DLORES ..\dither.asm,lodither.obj; >> BUILD0.LOG
C:\BIN\MASM -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T TSOFT.ASM,TSOFT.OBJ,TSOFT.LST; >> BUILD0.LOG
echo DONE >> BUILD0.LOG
exit
