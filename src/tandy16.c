#include "tandy16.h"

/* Stub implementation for Tandy 1000 EX Windows 3.x display driver */

int far pascal LibMain(unsigned int hInstance,
                       unsigned short wDataSegment,
                       unsigned short wHeapSize,
                       char far* lpszCmdLine)
{
    /* Placeholder for driver initialization */
    return 1; /* success */
}

int far pascal WEP(int bSystemExit)
{
    /* Windows Exit Procedure */
    return 1;
}
