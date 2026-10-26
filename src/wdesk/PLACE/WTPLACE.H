/* Caller-owned Windows 3.0 placement observations. Include WINDOWS.H first.
 * No global tracker, hook, timer, USER replacement or placement backport. */
#ifndef WTPLACE_H
#define WTPLACE_H
#define WTP_NORMAL 0
#define WTP_ICONIC 1
#define WTP_ZOOMED 2
#define WTP_KNOWN  1u
#define WTP_SAVED  2u           /* actual USER saved normal rectangle */
#define WTP_MOVE_ONLY 1u
#define WTP_OK 0
#define WTP_E_ARG (-1)
#define WTP_E_WINDOW (-2)
#define WTP_E_MOVE (-4)
#define WTP_E_UNSUPPORTED (-5)
typedef struct {
    WORD size;
    HWND window;
    HTASK task;
    WORD instance;
    WORD state;
    WORD flags;
    RECT normal;
} WTPLACEMENT;
/* Existing Windows 3.0 USER saved-position exports are resolved dynamically.
 * No exports or third-party imports are changed. Available means both exist. */
int FAR PASCAL WTPlaceAvailable(void);
/* Init invents no coordinates. Get observes normal coordinates directly or
 * reads USER's saved normal rectangle for a pinned window (WTP_SAVED).
 * If unavailable, retained observations remain known; an initially pinned
 * window stays unknown. Reused identities reset the caller-owned record. */
int FAR PASCAL WTPlaceInit(HWND window, WTPLACEMENT FAR *place);
int FAR PASCAL WTPlaceGet(HWND window, WTPLACEMENT FAR *place);
/* Set a normal or saved normal rectangle, preserving minimized/maximized and
 * hidden state, activation and z-order. MOVE_ONLY preserves actual normal
 * size. Pinned updates need the USER saved-position exports; otherwise return
 * UNSUPPORTED without restoring or inventing a rectangle. Verify the result.
 * These functions deliberately do not promise a Win32 WINDOWPLACEMENT ABI. */
int FAR PASCAL WTPlaceSetNormal(HWND window, WTPLACEMENT FAR *place,
                              const RECT FAR *normal, WORD flags);
#endif
