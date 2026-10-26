/* WDCORE.H - pure positioning/state core for the WDESK window mover.
 *
 * No Windows calls and no heap.  C89, 16-bit safe: all stored values are
 * 16-bit, all intermediate arithmetic is done in long.  The module keeps
 * an absolute logical rectangle for every tracked top-level window and
 * derives the screen position as (logical - viewport origin) each time,
 * so repeated pans can never accumulate drift.
 */
#ifndef WDCORE_H
#define WDCORE_H

typedef short WDI16;
typedef unsigned short WDU16;

/* Compile-time size checks; a negative array size fails the build. */
typedef char wd_chk_short[(sizeof(WDI16) == 2) ? 1 : -1];
typedef char wd_chk_ushort[(sizeof(WDU16) == 2) ? 1 : -1];
typedef char wd_chk_long[(sizeof(long) >= 4) ? 1 : -1];

#ifndef WD_MAXWIN
#define WD_MAXWIN 24            /* tracked windows; extras are untracked */
#endif

#define WD_WS_MAX   4096        /* largest workspace edge */
#define WD_SCR_MAX  4096        /* largest screen edge */
#define WD_LMIN     (-16384)    /* logical coordinate limits */
#define WD_LMAX     16383
#define WD_SMAX     16384       /* largest stored window width/height */
#define WD_GRABW    40          /* caption width that must stay visible */
#define WD_CAPH_DEF 16

#define WD_OK        0
#define WD_E_RANGE  (-1)        /* argument out of range, state unchanged */
#define WD_E_STATE  (-2)        /* module not initialized */
#define WD_E_FULL   (-3)        /* more than WD_MAXWIN: Home remains available */
#define WD_E_MOVE   (-4)        /* USER did not confirm a requested move/recovery */

#define WD_ST_NORMAL 0
#define WD_ST_ICONIC 1
#define WD_ST_ZOOMED 2

#define WD_F_SEEN    1          /* internal, set during reconcile */
#define WD_F_HASNORM 2          /* lx/ly/wid/ht hold a real normal rect */

/* One observed top-level window, filled in by the adapter.  Screen
 * coordinates are the window's outer rectangle top-left and size. */
typedef struct WDSNAP {
    WDU16 hwnd;
    WDU16 task;
    WDU16 inst;
    WDU16 cls;                  /* class-name hash chosen by the adapter */
    WDU16 owner;                /* owner hwnd, 0 when none */
    WDI16 x;
    WDI16 y;
    WDI16 wid;
    WDI16 ht;
    unsigned char state;        /* WD_ST_* */
    unsigned char normal;       /* actual saved normal rectangle is present */
} WDSNAP;

/* One tracked window: 24 bytes. */
typedef struct WDENT {
    WDU16 hwnd;
    WDU16 task;
    WDU16 inst;
    WDU16 cls;
    WDU16 owner;
    WDI16 lx;                   /* logical top-left; see WD_F_HASNORM */
    WDI16 ly;
    WDI16 wid;
    WDI16 ht;
    WDI16 sx;                   /* last known/commanded screen top-left */
    WDI16 sy;
    unsigned char state;
    unsigned char flags;
} WDENT;

typedef struct WDMOVE {
    WDU16 hwnd;
    WDI16 x;                    /* new screen top-left */
    WDI16 y;
} WDMOVE;

typedef struct WD {
    WDI16 scrw;
    WDI16 scrh;
    WDI16 wsw;
    WDI16 wsh;
    WDI16 ox;                   /* viewport origin in the workspace */
    WDI16 oy;
    WDI16 caph;
    WDU16 count;
    WDU16 dropped;              /* windows that did not fit, last reconcile */
    unsigned char ready;
    WDENT ent[WD_MAXWIN];
} WD;

/* Validate and reset.  Rejects screen/workspace edges < 1 or above the
 * limits and a workspace smaller than the screen.  caph <= 0 selects the
 * default.  On error the structure is left unusable (ready == 0). */
int WDInit(WD *wd, long scrw, long scrh, long wsw, long wsh, long caph);

/* Set the absolute viewport origin, clamped to the workspace.  Returns 1
 * when the origin changed, 0 when not, or a negative WD_E_* code. */
int WDSetViewport(WD *wd, long x, long y);

/* Merge a fresh observation of all eligible top-level windows.  Adds new
 * windows, drops vanished ones, treats an hwnd with a different
 * task/inst/class as a new window, adopts user moves and resizes, and
 * records minimize/maximize transitions.  Returns WD_OK or WD_E_*. */
int WDReconcile(WD *wd, const WDSNAP *snap, unsigned n);

/* Emit a move for every normal-state window whose desired screen
 * position differs from its last known one, updating the known position.
 * At most max entries are written; the rest stay pending for a later
 * call.  Returns the number written.  Never emits for a no-op. */
unsigned WDPlan(WD *wd, WDMOVE *out, unsigned max);

/* Viewport to (0,0) and make every window reachable (see README.MD).
 * Follow with WDPlan.  Returns WD_OK or WD_E_*. */
int WDHome(WD *wd);

/* Home, plan the final moves into out (size WD_MAXWIN), then forget all
 * windows.  Returns the number of moves.  The module stays initialized
 * and may be reconciled again. */
unsigned WDShutdown(WD *wd, WDMOVE *out, unsigned max);

/* Lookup helper; returns table index or -1. */
int WDFind(const WD *wd, unsigned hwnd);

#endif
