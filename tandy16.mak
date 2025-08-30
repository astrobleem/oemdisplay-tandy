# NMAKE makefile for the Tandy 1000 EX display driver stub
# Build with: nmake tandy16.mak

CC = cl
CFLAGS = /c /W3
OBJS = enable.obj tga_video.obj

all: $(OBJS)

# Compile the driver
enable.obj: src\\enable.c src\\tndy16.h
	$(CC) $(CFLAGS) src\\enable.c

tga_video.obj: src\\tga_video.asm
	ml /c /Fo tga_video.obj src\\tga_video.asm

clean:
	del enable.obj
	del tga_video.obj
