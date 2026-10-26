#include <windows.h>
#include "WTPLACE.H"

/* Windows 3.0 USER exports 460/461. The exact ABI and SW_SHOWNA/SW_HIDE
 * saved-position behavior were exercised on real USER in a disposable guest.
 * These are private implementation details behind our own explicit API. */
typedef WORD (FAR PASCAL *WTPGET)(HWND,LPRECT,LPPOINT);
typedef void (FAR PASCAL *WTPSET)(HWND,WORD,LPRECT,LPPOINT);
static WTPGET wtp_get(void)
{
    return (WTPGET)GetProcAddress(GetModuleHandle("USER"),
                                 "GETINTERNALWINDOWPOS");
}
static WTPSET wtp_set(void)
{
    return (WTPSET)GetProcAddress(GetModuleHandle("USER"),
                                 "SETINTERNALWINDOWPOS");
}
/* USER can create or raise a window's owned icon-title helper while updating
 * its saved position. Anchor the whole owned group against unrelated siblings,
 * not against one of the target's own transient helper HWNDs. */
static int wtp_owned(HWND window, HWND owner)
{
    unsigned n;
    for (n = 0; window && n < 32; n++) {
        if (window == owner) return 1;
        window = GetWindow(window, GW_OWNER);
    }
    return 0;
}
static HWND wtp_previous(HWND window)
{
    HWND before = GetWindow(window, GW_HWNDPREV);
    while (before && wtp_owned(before, window))
        before = GetWindow(before, GW_HWNDPREV);
    return before;
}
int FAR PASCAL WTPlaceAvailable(void)
{
    return wtp_get() != 0 && wtp_set() != 0;
}

int FAR PASCAL WTPlaceInit(HWND window, WTPLACEMENT FAR *p)
{
    if (!p) return WTP_E_ARG;
    p->size = (WORD)sizeof(*p);
    p->window = window;
    p->flags = 0;
    p->state = WTP_NORMAL;
    p->task = 0;
    p->instance = 0;
    p->normal.left = p->normal.top = 0;
    p->normal.right = p->normal.bottom = 0;
    if (!IsWindow(window)) return WTP_E_WINDOW;
    p->task = GetWindowTask(window);
    p->instance = GetWindowWord(window, GWW_HINSTANCE);
    return WTP_OK;
}

int FAR PASCAL WTPlaceGet(HWND window, WTPLACEMENT FAR *p)
{
    RECT r;
    int result;
    WTPGET get;
    WORD show;
    if (!p || p->size != sizeof(*p)) return WTP_E_ARG;
    if (!IsWindow(window)) return WTP_E_WINDOW;
    if (p->window != window || p->task != GetWindowTask(window) ||
        p->instance != GetWindowWord(window, GWW_HINSTANCE)) {
        result = WTPlaceInit(window, p);
        if (result != WTP_OK) return result;
    }
    p->state = IsIconic(window) ? WTP_ICONIC :
               IsZoomed(window) ? WTP_ZOOMED : WTP_NORMAL;
    p->flags = (WORD)(p->flags & (WORD)~WTP_SAVED);
    if (p->state == WTP_NORMAL) {
        GetWindowRect(window, &r);
        if (!IsWindow(window)) return WTP_E_WINDOW;
        p->normal = r;
        p->flags |= WTP_KNOWN;
    } else {
        get = wtp_get();
        if (get) {
            show = get(window, &r, 0);
            if (!IsWindow(window)) return WTP_E_WINDOW;
            if ((show == SW_SHOWMINIMIZED || show == SW_SHOWMAXIMIZED) &&
                r.right > r.left && r.bottom > r.top) {
                p->normal = r;
                p->flags |= WTP_KNOWN | WTP_SAVED;
            }
        }
    }
    return WTP_OK;
}

int FAR PASCAL WTPlaceSetNormal(HWND window, WTPLACEMENT FAR *p,
                              const RECT FAR *normal, WORD flags)
{
    RECT wanted;
    long width, height;
    int result;
    UINT swp;
    WORD state;
    int visible;
    HWND active, previous;
    WTPSET put;
    if (!normal || (flags & ~WTP_MOVE_ONLY)) return WTP_E_ARG;
    wanted = *normal;
    width = (long)wanted.right - wanted.left;
    height = (long)wanted.bottom - wanted.top;
    if (!(flags & WTP_MOVE_ONLY) &&
        (width < 1 || width > 16384L || height < 1 || height > 16384L))
        return WTP_E_ARG;
    if (flags & WTP_MOVE_ONLY) width = height = 0;
    result = WTPlaceGet(window, p);
    if (result != WTP_OK) return result;
    if ((flags & WTP_MOVE_ONLY) && (p->flags & WTP_KNOWN)) {
        width = (long)wanted.left + p->normal.right - p->normal.left;
        height = (long)wanted.top + p->normal.bottom - p->normal.top;
        if (width < -32768L || width > 32767L ||
            height < -32768L || height > 32767L) return WTP_E_ARG;
        wanted.right = (short)width; wanted.bottom = (short)height;
        width = height = 0;
    }
    if (p->state != WTP_NORMAL) {
        put = wtp_set();
        if (!put || !(p->flags & WTP_SAVED)) return WTP_E_UNSUPPORTED;
        state = p->state; visible = IsWindowVisible(window);
        active = GetActiveWindow(); previous = wtp_previous(window);
        put(window, visible ? SW_SHOWNA : SW_HIDE, &wanted, 0);
        result = WTPlaceGet(window, p);
        if (result != WTP_OK) return result;
        if (wtp_previous(window) != previous) {
            if (previous && !IsWindow(previous)) return WTP_E_MOVE;
            /* Windows 3.0 specifies no SetWindowPos return value. Some
             * newer headers declare BOOL: only observed state is evidence. */
            (void)SetWindowPos(window, previous, 0, 0, 0, 0,
                               SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
            result = WTPlaceGet(window, p);
            if (result != WTP_OK) return result;
        }
        return p->state == state && (p->flags & WTP_SAVED) &&
            p->normal.left == wanted.left && p->normal.top == wanted.top &&
            p->normal.right == wanted.right && p->normal.bottom == wanted.bottom &&
            IsWindowVisible(window) == visible && GetActiveWindow() == active &&
            wtp_previous(window) == previous ? WTP_OK : WTP_E_MOVE;
    }
    swp = SWP_NOZORDER | SWP_NOACTIVATE;
    if (flags & WTP_MOVE_ONLY) swp |= SWP_NOSIZE;
    (void)SetWindowPos(window, 0, wanted.left, wanted.top,
                       (int)width, (int)height, swp);
    if (WTPlaceGet(window, p) != WTP_OK) return WTP_E_WINDOW;
    if (p->state != WTP_NORMAL || p->normal.left != wanted.left ||
        p->normal.top != wanted.top) return WTP_E_MOVE;
    if (p->normal.right != wanted.right || p->normal.bottom != wanted.bottom)
        return WTP_E_MOVE;
    return WTP_OK;
}
