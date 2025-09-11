# NMAKE makefile for the Tandy 1000 EX display driver stub
# Build with: nmake TNDY16.MAK

CC = cl
ML = masm

CFLAGS = /c /AL /W3 /Isrc
MASMFLAGS = -v -ML -I.\\ -Isrc\\
OBJS = DLLENTRY.OBJ ENABLE.OBJ TGAVID.OBJ

all: TNDY16.DRV

# Compile the driver
DLLENTRY.OBJ: src\DLLENTRY.C src\WINDOWS.H
	$(CC) $(CFLAGS) src\\DLLENTRY.C

ENABLE.OBJ: src\ENABLE.C src\WINDOWS.H src\TGAVID.H src\TNDY16.H \
            src\STRING.H src\COMPAT.H src\STDINT.H src\STDBOOL.H
	$(CC) $(CFLAGS) src\\ENABLE.C

TGAVID.OBJ: src\\TGAVID.ASM src\\WINDOWS.INC
        $(ML) $(MASMFLAGS) src\\TGAVID.ASM, TGAVID.OBJ;

TNDY16.DRV: $(OBJS) TNDY16.DEF
        link DLLENTRY.OBJ ENABLE.OBJ TGAVID.OBJ, TNDY16.DRV,, slibcew libw gdi kernel user, TNDY16.DEF

clean:
        del DLLENTRY.OBJ
        del ENABLE.OBJ
        del TGAVID.OBJ
        del TNDY16.DRV
