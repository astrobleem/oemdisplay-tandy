# NMAKE makefile for the Tandy 1000 EX display driver stub
# Build with: nmake tndy16.mak

CC = cl
CFLAGS = /c /W3
OBJS = enable.obj tgavid.obj

all: $(OBJS)

# Compile the driver
enable.obj: src\\enable.c src\\tndy16.h
	$(CC) $(CFLAGS) src\\enable.c

tgavid.obj: src\\tgavid.asm
	ml /c /Fo tgavid.obj src\\tgavid.asm

clean:
	del enable.obj
	del tgavid.obj
