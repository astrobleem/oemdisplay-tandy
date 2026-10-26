/* WDSTUB.C - link and size check for the WDWIN adapter.
 *
 * NOT SHIPPED.  This WinMain exists only so that WDCORE, WDWIN and the
 * Win16 entry code can be linked into an EXE whose map file gives the
 * code and data sizes.  It drives the public API once and exits.
 */
#include "WDWIN.H"

int PASCAL WinMain(HINSTANCE hinst, HINSTANCE hprev, LPSTR cmd,
                   int show)
{
    (void)hinst;
    (void)hprev;
    (void)cmd;
    (void)show;
    (void)WDWinInit(2048, 2048);
    (void)WDWinExclude((LPCSTR)"XTPan");
    (void)WDWinPan(100, 100);
    (void)WDWinPanBy(-50, 25);
    (void)WDWinHome();
    WDWinShutdown();
    return 0;
}
