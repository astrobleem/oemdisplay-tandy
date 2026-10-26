/* WDWIN.C - Win16 adapter for the WDCORE window-positioning core.
 * See WDWIN.H.  Windows 3.0 APIs only.
 *
 * Top-level windows are enumerated with GetWindow(GW_CHILD) and
 * GW_HWNDNEXT from the desktop, so no EnumWindows callback (and no
 * MakeProcInstance or EXPORTS entry) is needed.
 */
#include "WDWIN.H"
#include "WTPLACE.H"

#define WDW_FLAGS   (SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOSIZE)
/* More than WD_MAXWIN so the core can see, and count, overflow. */
#define WDW_SNAPMAX (WD_MAXWIN + 8)

static WD wdw_wd;
static int wdw_on;
static WDU16 wdw_excl[WDW_EXMAX];
static unsigned wdw_nexcl;
static WDSNAP wdw_snap[WDW_SNAPMAX];
static WDMOVE wdw_move[WD_MAXWIN];
static unsigned wdw_more;
static int wdw_dirty;

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

/* Gather eligible top-level windows, retaining every previously moved one
 * even on overflow. Count excess windows rather than forgetting owners. */
static unsigned wdw_collect(void)
{
    unsigned n = 0;
    unsigned i;
    int tracked;
    HWND h;
    LONG style;
    RECT r;
    char cls[WDW_CLSMAX];
    WDSNAP *s;
    WTPLACEMENT place;

    wdw_more = 0;
    for (h = GetWindow(GetDesktopWindow(), GW_CHILD);
         h != 0;
         h = GetWindow(h, GW_HWNDNEXT)) {
        tracked = WDFind(&wdw_wd, (unsigned)h);
        if (GetWindowTask(h) == GetCurrentTask()) {
            continue;           /* our own windows, never moved */
        }
        if (GetClassName(h, cls, WDW_CLSMAX) <= 0 ||
            WTPlaceInit(h, &place) != WTP_OK) {
            continue;
        }
        /* A reused handle is a new window, so its eligibility must be
         * checked afresh. Only the actual moved identity owns recovery. */
        if (tracked >= 0 &&
            (wdw_wd.ent[tracked].task != (WDU16)place.task ||
             wdw_wd.ent[tracked].inst != place.instance ||
             wdw_wd.ent[tracked].cls != wdw_hash(cls))) {
            tracked = -1;
        }
        if (!IsWindowVisible(h) && tracked < 0) {
            continue;
        }
        style = GetWindowLong(h, GWL_STYLE);
        /* Icon-title and menu helper windows have no application caption.
         * Do not guess their undocumented class numbers on Windows 3.0. */
        if (tracked < 0 &&
            ((style & WS_CHILD) || (style & WS_CAPTION) != WS_CAPTION)) {
            continue;
        }
        if (tracked < 0 && wdw_excluded(wdw_hash(cls))) {
            continue;
        }
        if (WTPlaceGet(h, &place) != WTP_OK) {
            continue;
        }
        if (place.flags & WTP_KNOWN) {
            r = place.normal;
        } else {
            GetWindowRect(h, &r);
            if (!IsWindow(h)) continue;
        }
        if (n == WDW_SNAPMAX) {
            if (wdw_more < 65535u) {
                wdw_more++;
            }
            if (WDFind(&wdw_wd, (unsigned)h) < 0) {
                continue;
            }
            /* Never forget a previously moved window when new foreground
             * windows fill the snapshot. Displace an untracked entry. */
            for (i = n; i > 0; i--) {
                if (WDFind(&wdw_wd, wdw_snap[i-1].hwnd) < 0) {
                    break;
                }
            }
            if (i == 0) {
                continue;
            }
            s = &wdw_snap[i-1];
        } else {
            s = &wdw_snap[n++];
        }
        s->hwnd = (WDU16)h;
        s->task = (WDU16)place.task;
        s->inst = place.instance;
        s->cls = wdw_hash(cls);
        s->owner = (WDU16)GetWindow(h, GW_OWNER);
        s->x = wdw_s16((long)r.left);
        s->y = wdw_s16((long)r.top);
        s->wid = wdw_s16((long)r.right - (long)r.left);
        s->ht = wdw_s16((long)r.bottom - (long)r.top);
        s->state = (unsigned char)place.state;
        s->normal = (unsigned char)((place.flags & WTP_SAVED) != 0);
    }
    return n;
}

/* Send the moves as one deferred batch. Read back each target and retry
 * only an unconfirmed one individually. Windows 3.0's positioning APIs
 * do not return success values. Returns the verified target count. */
static int wdw_apply(unsigned n)
{
    unsigned i;
    unsigned moved = 0;
    HDWP hdwp;
    WDMOVE *m;
    int ok;
    int idx;
    int failed = 0;
    unsigned pass, j, k;
    int changed;
    WDMOVE parent;
    RECT r;
    WTPLACEMENT place;

    if (n == 0) {
        return 0;
    }
    /* USER may move an owned popup with its owner. Include its absolute
     * target even when WDPlan omitted it as a no-op, and include nested
     * owned windows in the same closure. Verify these targets too. */
    for (pass = 0; pass < wdw_wd.count; pass++) {
        changed = 0;
        for (i = 0; i < wdw_wd.count; i++) {
            WDENT *e = &wdw_wd.ent[i];
            if (e->state != WD_ST_NORMAL || !e->owner) continue;
            for (j = 0; j < n; j++)
                if (wdw_move[j].hwnd == e->hwnd) break;
            if (j < n) continue;
            for (j = 0; j < n; j++)
                if (wdw_move[j].hwnd == e->owner) break;
            if (j == n) continue;
            wdw_move[n].hwnd = e->hwnd;
            wdw_move[n].x = e->sx; wdw_move[n].y = e->sy;
            n++; changed = 1;
        }
        if (!changed) break;
    }
    /* Parent first even when the z-order enumeration found the dialog
     * first. Absolute child targets then work with USER implementations
     * that move owned popups automatically as well as ones that do not. */
    for (pass = 0; pass < n; pass++) {
        changed = 0;
        for (i = 0; i < n; i++) {
            idx = WDFind(&wdw_wd, wdw_move[i].hwnd);
            if (idx < 0) continue;
            for (j = i + 1; j < n; j++) {
                if (wdw_move[j].hwnd == wdw_wd.ent[idx].owner) {
                    parent = wdw_move[j];
                    for (k = j; k > i; k--) wdw_move[k] = wdw_move[k-1];
                    wdw_move[i] = parent;changed = 1;break;
                }
            }
        }
        if (!changed) break;
    }
    hdwp = BeginDeferWindowPos((int)n);
    ok = (hdwp != 0);
    for (i = 0; ok && i < n; i++) {
        m = &wdw_move[i];
        hdwp = DeferWindowPos(hdwp, (HWND)m->hwnd, (HWND)0,
                              m->x, m->y, 0, 0, WDW_FLAGS);
        ok = (hdwp != 0);
    }
    /* EndDeferWindowPos is also void in the Windows 3.0 contract. Verify
     * USER's result and retry only targets that still need a move. */
    if (ok) (void)EndDeferWindowPos(hdwp);
    for (i = 0; i < n; i++) {
        m = &wdw_move[i];
        if (!IsWindow((HWND)m->hwnd)) {
            continue;
        }
        ok = WTPlaceInit((HWND)m->hwnd, &place) == WTP_OK &&
             WTPlaceGet((HWND)m->hwnd, &place) == WTP_OK &&
             place.state == WTP_NORMAL && (place.flags & WTP_KNOWN);
        if (!ok || place.normal.left != m->x || place.normal.top != m->y) {
            r.left = m->x; r.top = m->y;
            r.right = m->x; r.bottom = m->y;
            if (WTPlaceInit((HWND)m->hwnd, &place) == WTP_OK)
                (void)WTPlaceSetNormal((HWND)m->hwnd, &place, &r, WTP_MOVE_ONLY);
            ok = WTPlaceGet((HWND)m->hwnd, &place) == WTP_OK &&
                 place.state == WTP_NORMAL && (place.flags & WTP_KNOWN);
        }
        if (ok && place.normal.left == m->x && place.normal.top == m->y) {
            moved++;
        } else {
            failed = 1;
            idx = WDFind(&wdw_wd, m->hwnd);
            /* WDPlan optimistically records the command. Roll its known
             * screen coordinate back to USER's actual position on failure,
             * preserving the logical target for a retry, not a user drag. */
            for (j = 0; idx >= 0 && j < WDW_SNAPMAX; j++) {
                if (wdw_snap[j].hwnd == m->hwnd) {
                    wdw_wd.ent[idx].sx = wdw_snap[j].x;
                    wdw_wd.ent[idx].sy = wdw_snap[j].y;
                    break;
                }
            }
            if (idx >= 0 && ok) {
                wdw_wd.ent[idx].sx = wdw_s16((long)place.normal.left);
                wdw_wd.ent[idx].sy = wdw_s16((long)place.normal.top);
            }
        }
    }
    return failed ? WD_E_MOVE : (int)moved;
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
    if (wdw_wd.dropped) {
        return WD_E_FULL;
    }
    r = WDSetViewport(&wdw_wd, x, y);
    if (r < 0) {
        return r;
    }
    if (r) wdw_dirty = 1;
    n = WDPlan(&wdw_wd, wdw_move, WD_MAXWIN);
    if (n) wdw_dirty = 1;
    return wdw_apply(n);
}

int WDWinInit(int wsw, int wsh)
{
    return WDWinInitView(wsw, wsh, GetSystemMetrics(SM_CXSCREEN),
                         GetSystemMetrics(SM_CYSCREEN));
}

int WDWinInitView(int wsw, int wsh, int vieww, int viewh)
{
    int r;

    if (wdw_on) {
        return WD_E_STATE;
    }
    if (!WTPlaceAvailable()) return WD_E_STATE;
    wdw_on = 0;
    wdw_nexcl = 0;
    r = WDInit(&wdw_wd, (long)vieww,
               (long)viewh, (long)wsw,
               (long)wsh, (long)GetSystemMetrics(SM_CYCAPTION));
    if (r != WD_OK) {
        return r;
    }
    wdw_on = 1;
    wdw_dirty = 0;
    (void)WDWinExclude((LPCSTR)"#32768");
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
    (void)WDReconcile(&wdw_wd, wdw_snap, n);
    if ((long)wdw_wd.dropped + wdw_more > 65535L) {
        wdw_wd.dropped = 65535u;
    } else {
        wdw_wd.dropped = (WDU16)(wdw_wd.dropped + wdw_more);
    }
    return WD_OK;
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
    unsigned i;
    HWND h;
    WTPLACEMENT place;

    r = WDWinReconcile();
    if (r != WD_OK) {
        return r;
    }
    wdw_dirty = 1;
    r = WDHome(&wdw_wd);
    if (r != WD_OK) {
        return r;
    }
    n = WDPlan(&wdw_wd, wdw_move, WD_MAXWIN);
    r = wdw_apply(n);
    if (r < 0) return r;
    /* Pinned windows keep their visible state. Repair USER's saved normal
     * rectangle before forgetting the logical target, so a later restore
     * remains reachable without showing/activating an icon or hidden app. */
    for (i = 0; i < wdw_wd.count; i++) {
        RECT target;
        WDENT *e = &wdw_wd.ent[i];
        h = (HWND)e->hwnd;
        if (IsWindow(h) && (IsIconic(h) || IsZoomed(h))) {
            if (!(e->flags & WD_F_HASNORM)) return WD_E_MOVE;
            target.left = e->lx; target.top = e->ly;
            target.right = target.left; target.bottom = target.top;
            if (WTPlaceInit(h, &place) != WTP_OK ||
                WTPlaceSetNormal(h, &place, &target, WTP_MOVE_ONLY) != WTP_OK)
                return WD_E_MOVE;
            e->sx = place.normal.left; e->sy = place.normal.top;
        }
    }
    wdw_dirty = 0;
    return r;
}

int WDWinPrepareShutdown(void)
{
    return wdw_on && wdw_dirty ? WDWinHome() : WD_OK;
}

int WDWinShutdown(void)
{
    int result;

    if (!wdw_on) {
        return WD_OK;
    }
    result = WDWinPrepareShutdown();
    if (result < 0) {
        return result;          /* owner must keep recovery alive */
    }
    wdw_on = 0;
    return WD_OK;
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
