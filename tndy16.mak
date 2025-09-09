# NMAKE makefile for the Tandy 1000 EX display driver stub
# Build with: nmake tndy16.mak

CC = cl
ML = masm

CFLAGS = /c /W3
MASMFLAGS = -v -ML -I.\\
OBJS = dllentry.obj enable.obj tgavid.obj

all: TNDY16.DRV

# Compile the driver
dllentry.obj: src\\dllentry.c
	$(CC) $(CFLAGS) src\\dllentry.c

enable.obj: src\\enable.c src\\tndy16.h src\\string.h src\\compat.h
	$(CC) $(CFLAGS) src\\enable.c

tgavid.obj: src\\tgavid.asm
        $(ML) $(MASMFLAGS) src\\tgavid.asm, tgavid.obj;

TNDY16.DRV: $(OBJS) TNDY16.DEF
        link dllentry.obj enable.obj tgavid.obj, TNDY16.DRV,, libw sdllcew gdi kernel user, TNDY16.DEF

clean:
        del dllentry.obj
        del enable.obj
        del tgavid.obj
        del tndy16.drv
