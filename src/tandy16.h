#ifndef TANDY16_H
#define TANDY16_H

/* Stub header for Tandy 1000 EX Windows 3.x display driver */

int far pascal LibMain(unsigned int hInstance,
                       unsigned short wDataSegment,
                       unsigned short wHeapSize,
                       char far* lpszCmdLine);

int far pascal WEP(int bSystemExit);

#endif /* TANDY16_H */
