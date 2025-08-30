# NMAKE makefile for the Tandy 1000 EX display driver stub
# Build with: nmake tandy16.mak

CC = cl
CFLAGS = /c /W3
OBJS = tandy16.obj

all: $(OBJS)

# Compile the driver
$(OBJS): src\\tandy16.c src\\tandy16.h
	$(CC) $(CFLAGS) src\\tandy16.c

clean:
	del $(OBJS)
