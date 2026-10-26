/* WDWIN.H - Win16 adapter for the WDCORE window-positioning core.
 *
 * Windows 3.0 real mode only.  The adapter owns one static WD and does
 * no background work: no timers, hooks, window classes or callbacks.
 * Every call that moves windows (WDWinPan, WDWinPanBy, WDWinHome,
 * WDWinShutdown) first observes the desktop with WDWinReconcile, so
 * observation happens only when the owner calls in.
 */
#ifndef WDWIN_H
#define WDWIN_H

#ifndef WINVER
#define WINVER 0x0300
#endif

#include <windows.h>
#include "WDCORE.H"

#define WDW_EXMAX   8           /* excluded class-name hashes */
#define WDW_CLSMAX  64          /* class names of 63 chars or fewer */

/* Screen size from GetSystemMetrics, caption height from SM_CYCAPTION.
 * Calls WDInit, clears the exclusion list and excludes the menu class.
 * Captionless helper/icon-title windows are excluded structurally. Returns
 * WD_OK or a negative WD_E_* code. */
int  WDWinInit(int wsw, int wsh);
/* Framebuffer drivers report their logical desktop as SM_*SCREEN. The
 * owner supplies the physical viewport here after parking that driver. */
int  WDWinInitView(int wsw, int wsh, int vieww, int viewh);

/* Add a class name to the exclusion list (stored as a hash).  Returns
 * 0 on success or when already present, -1 when the list is full or
 * the name is NULL or longer than 63 characters. */
int  WDWinExclude(LPCSTR classname);

/* Observe the desktop and merge it into the core.  Returns WD_OK or a
 * negative code. */
int  WDWinReconcile(void);

/* Move the viewport to the ABSOLUTE origin (x, y): reconcile, set the
 * viewport, plan, apply.  Returns the number of windows moved or a
 * negative code. */
int  WDWinPan(int x, int y);

/* Relative pan from the current origin.  Uses long arithmetic. */
int  WDWinPanBy(int dx, int dy);

/* Viewport to (0,0) and rescue windows: reconcile, home, plan, apply.
 * Returns the number of windows moved or a negative code. */
int  WDWinHome(void);
/* End-session query: recover if needed but keep the owner initialized in
 * case another application's query cancels the Windows shutdown. */
int  WDWinPrepareShutdown(void);

/* Repair pinned saved rectangles, Home and verify final moves before
 * releasing ownership. A negative result retains the table for recovery.
 * Safe to call when not initialized, and to call twice after success. */
int  WDWinShutdown(void);

/* Current viewport origin; both are 0 when not initialized. */
void WDWinViewport(int *x, int *y);

/* Windows that did not fit in the core at the last reconcile. */
unsigned WDWinDropped(void);

#endif
