#include "windows.h"

/*
 * DLL entry points for the Tandy 16-color display driver.
 * LibMain is invoked by the loader at attach time, and WEP is called
 * on detach.  The driver performs all work through the exported
 * Enable/Disable routines so these just report success.
 */
int FAR PASCAL LibMain(HINSTANCE hInst, WORD wDataSeg, WORD cbHeap, LPSTR lpCmdLine)
{
    (void)hInst;
    (void)wDataSeg;
    (void)cbHeap;
    (void)lpCmdLine;
    return 1;
}

int FAR PASCAL _loadds WEP(int nParam)
{
    (void)nParam;
    return 1;
}
