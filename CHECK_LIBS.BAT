@echo off
PATH=C:\BIN;%PATH%
echo Checking LIBW.LIB... > C:\LIBS.LOG
echo. | lib C:\LIB\LIBW.LIB,C:\LIBW.LST >> C:\LIBS.LOG
echo. >> C:\LIBS.LOG
echo Checking KERNEL.LIB... >> C:\LIBS.LOG
echo. | lib C:\LIB\KERNEL.LIB,C:\KERNEL.LST >> C:\LIBS.LOG
echo Done. >> C:\LIBS.LOG
exit
