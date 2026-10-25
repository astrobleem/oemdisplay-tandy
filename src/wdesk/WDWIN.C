/* WDWIN.C - Win16 adapter for the WDCORE window-positioning core.
 * See WDWIN.H.  Windows 3.0 APIs only.
 *
 * Top-level windows are enumerated with GetWindow(GW_CHILD) and
 * GW_HWNDNEXT from the desktop, so no EnumWindows callback (and no
 * MakeProcInstance or EXPORTS entry) is needed.
 */
#include "WDWIN.H"

#define WDW_FLAGS   (SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOSIZE)
/* More than WD_MAXWIN so the core can see, and count, overflow. */
#define WDW_SNAPMAX (WD_MAXWIN + 8)

static WD wdw_wd;
static int wdw_on;
static WDU16 wdw_excl[WDW_EXMAX];
static unsigned wdw_nexcl;
static WDSNAP wdw_snap[WDW_SNAPMAX];
static WDMOVE wdw_move[WD_MAXWIN];

/* Case-insensitive 16-bit hash of a class name. */
static WDU16 wdw_hash(LPCSTR s)
{
    WDU16 h = 0;
    unsigned c;

    while (*s) {
        c = (unsigned char)*s;
        if (c >= 'a' && c <= 'z') {
            c = c - 'a' + 'A';
        }
        h = (WDU16)(h * 31u + c);
        s++;
    }
    return h;
}

/* Nonzero when the string ends within WDW_CLSMAX characters. */
static int wdw_name_ok(LPCSTR s)
{
    int n;

    for (n = 0; n < WDW_CLSMAX; n++) {
        if (s[n] == '\0') {
            return 1;
        }
    }
    return 0;
}

static int wdw_excluded(WDU16 h)
{
    unsigned i;

    for (i = 0; i < wdw_nexcl; i++) {
        if (wdw_excl[i] == h) {
            return 1;
        }
    }
    return 0;
}

/* Clamp a long to the 16-bit signed range. */
static WDI16 wdw_s16(long v)
{
    if (v < -32768L) {
        return (WDI16)-32768L;
    }
    if (v > 32767L) {
        return (WDI16)32767L;
    }
    return (WDI16)v;
}

/* Gather eligible top-level windows into wdw_snap; returns the count.
 * Stops at WDW_SNAPMAX so the core sees at most one overflow entry. */
static unsigned wdw_collect(void)
{
    unsigned n = 0;
    HWND h;
    RECT r;
    char cls[WDW_CLSMAX];
    WDSNAP *s;

    for (h = GetWindow(GetDesktopWindow(), GW_CHILD);
         h != 0 && n < WDW_SNAPMAX;
         h = GetWindow(h, GW_HWNDNEXT)) {
        if (!IsWindowVisible(h)) {
            continue;
        }
        if (GetWindowLong(h, GWL_STYLE) & WS_CHILD) {
            continue;
        }
        if (GetWindowTask(h) == GetCurrentTask()) {
            continue;           /* our own windows, never moved */
        }
        GetClassName(h, cls, WDW_CLSMAX);
        if (wdw_excluded(wdw_hash(cls))) {
            continue;
        }
        GetWindowRect(h, &r);
        s = &wdw_snap[n];
        s->hwnd = (WDU16)h;
        s->task = (WDU16)GetWindowTask(h);
        s->inst = GetWindowWord(h, GWW_HINSTANCE);
        s->cls = wdw_hash(cls);
        s->owner = (WDU16)GetWindow(h, GW_OWNER);
        s->x = wdw_s16((long)r.left);
        s->y = wdw_s16((long)r.top);
        s->wid = wdw_s16((long)r.right - (long)r.left);
        s->ht = wdw_s16((long)r.bottom - (long)r.top);
        if (IsIconic(h)) {
            s->state = WD_ST_ICONIC;
        } else if (IsZoomed(h)) {
            s->state = WD_ST_ZOOMED;
        } else {
            s->state = WD_ST_NORMAL;
        }
        n++;
    }
    return n;
}

/* Send the moves in wdw_move[0 .. n-1] as one deferred batch.  If the
 * batch cannot be built or ended, every move is retried individually
 * with SetWindowPos.  Returns the number of windows moved. */
static int wdw_apply(unsigned n)
{
    unsigned i;
    unsigned moved = 0;
    HDWP hdwp;
    WDMOVE *m;
    int ok;

    if (n == 0) {
        return 0;
    }
    hdwp = BeginDeferWindowPos((int)n);
    ok = (hdwp != 0);
    for (i = 0; ok && i < n; i++) {
        m = &wdw_move[i];
        hdwp = DeferWindowPos(hdwp, (HWND)m->hwnd, (HWND)0,
                              m->x, m->y, 0, 0, WDW_FLAGS);
        ok = (hdwp != 0);
    }
    if (ok && EndDeferWindowPos(hdwp)) {
        return (int)n;
    }
    for (i = 0; i < n; i++) {
        m = &wdw_move[i];
        if (SetWindowPos((HWND)m->hwnd, (HWND)0, m->x, m->y, 0, 0,
                         WDW_FLAGS)) {
            moved++;
        }
    }
    return (int)moved;
}

/* Reconcile, set the origin, plan and apply.  Long arguments so that
 * relative pans cannot wrap. */
static int wdw_pan(long x, long y)
{
    int r;
    unsigned n;

    r = WDWinReconcile();
    if (r != WD_OK) {
        return r;
    }
    r = WDSetViewport(&wdw_wd, x, y);
    if (r < 0) {
        return r;
    }
    n = WDPlan(&wdw_wd, wdw_move, WD_MAXWIN);
    return wdw_apply(n);
}

int WDWinInit(int wsw, int wsh)
{
    int r;

    wdw_on = 0;
    wdw_nexcl = 0;
    r = WDInit(&wdw_wd, (long)GetSystemMetrics(SM_CXSCREEN),
               (long)GetSystemMetrics(SM_CYSCREEN), (long)wsw,
               (long)wsh, (long)GetSystemMetrics(SM_CYCAPTION));
    if (r != WD_OK) {
        return r;
    }
    wdw_on = 1;
    (void)WDWinExclude((LPCSTR)"#32768");
    (void)WDWinExclude((LPCSTR)"#32772");
    return WD_OK;
}

int WDWinExclude(LPCSTR classname)
{
    WDU16 h;

    if (classname == 0 || !wdw_name_ok(classname)) {
        return WD_E_RANGE;
    }
    h = wdw_hash(classname);
    if (wdw_excluded(h)) {
        return 0;
    }
    if (wdw_nexcl >= WDW_EXMAX) {
        return -1;
    }
    wdw_excl[wdw_nexcl] = h;
    wdw_nexcl++;
    return 0;
}

int WDWinReconcile(void)
{
    unsigned n;

    if (!wdw_on) {
        return WD_E_STATE;
    }
    n = wdw_collect();
    return WDReconcile(&wdw_wd, wdw_snap, n);
}

int WDWinPan(int x, int y)
{
    if (!wdw_on) {
        return WD_E_STATE;
    }
    return wdw_pan((long)x, (long)y);
}

int WDWinPanBy(int dx, int dy)
{
    if (!wdw_on) {
        return WD_E_STATE;
    }
    return wdw_pan((long)wdw_wd.ox + (long)dx,
                   (long)wdw_wd.oy + (long)dy);
}

int WDWinHome(void)
{
    int r;
    unsigned n;

    r = WDWinReconcile();
    if (r != WD_OK) {
        return r;
    }
    r = WDHome(&wdw_wd);
    if (r != WD_OK) {
        return r;
    }
    n = WDPlan(&wdw_wd, wdw_move, WD_MAXWIN);
    return wdw_apply(n);
}

void WDWinShutdown(void)
{
    unsigned n;

    if (!wdw_on) {
        return;
    }
    if (WDWinReconcile() == WD_OK) {
        n = WDShutdown(&wdw_wd, wdw_move, WD_MAXWIN);
        (void)wdw_apply(n);
    }
    wdw_on = 0;
}

void WDWinViewport(int *x, int *y)
{
    if (x != 0) {
        *x = wdw_on ? (int)wdw_wd.ox : 0;
    }
    if (y != 0) {
        *y = wdw_on ? (int)wdw_wd.oy : 0;
    }
}

unsigned WDWinDropped(void)
{
    return wdw_on ? (unsigned)wdw_wd.dropped : 0;
}
