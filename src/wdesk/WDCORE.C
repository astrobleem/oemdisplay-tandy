/* WDCORE.C - pure positioning/state core for the WDESK window mover.
 * See WDCORE.H and README.MD.  No Windows calls.
 *
 * Test-only fault switches (never defined in a real build):
 *   WD_FAULT_OWNER   shift owned windows twice during Home rescue
 *   WD_FAULT_REUSE   match windows by hwnd only (stale state on reuse)
 *   WD_FAULT_PIN     also move minimized/maximized windows
 */
#include "WDCORE.H"

static long wd_clamp(long v, long lo, long hi)
{
    if (v < lo) {
        return lo;
    }
    if (v > hi) {
        return hi;
    }
    return v;
}

static WDI16 wd_lcl(long v)
{
    return (WDI16)wd_clamp(v, WD_LMIN, WD_LMAX);
}

static WDI16 wd_size(long v)
{
    return (WDI16)wd_clamp(v, 0L, WD_SMAX);
}

int WDFind(const WD *wd, unsigned hwnd)
{
    unsigned i;

    for (i = 0; i < wd->count; i++) {
        if (wd->ent[i].hwnd == hwnd) {
            return (int)i;
        }
    }
    return -1;
}

int WDInit(WD *wd, long scrw, long scrh, long wsw, long wsh, long caph)
{
    wd->ready = 0;
    wd->count = 0;
    wd->dropped = 0;
    wd->ox = 0;
    wd->oy = 0;
    if (scrw < 1 || scrw > WD_SCR_MAX || scrh < 1 || scrh > WD_SCR_MAX) {
        return WD_E_RANGE;
    }
    if (wsw < scrw || wsw > WD_WS_MAX || wsh < scrh || wsh > WD_WS_MAX) {
        return WD_E_RANGE;
    }
    if (caph <= 0) {
        caph = WD_CAPH_DEF;
    }
    if (caph > scrh) {
        caph = scrh;
    }
    wd->scrw = (WDI16)scrw;
    wd->scrh = (WDI16)scrh;
    wd->wsw = (WDI16)wsw;
    wd->wsh = (WDI16)wsh;
    wd->caph = (WDI16)caph;
    wd->ready = 1;
    return WD_OK;
}

int WDSetViewport(WD *wd, long x, long y)
{
    WDI16 nx;
    WDI16 ny;

    if (!wd->ready) {
        return WD_E_STATE;
    }
    nx = (WDI16)wd_clamp(x, 0L, (long)wd->wsw - wd->scrw);
    ny = (WDI16)wd_clamp(y, 0L, (long)wd->wsh - wd->scrh);
    if (nx == wd->ox && ny == wd->oy) {
        return 0;
    }
    wd->ox = nx;
    wd->oy = ny;
    return 1;
}

/* Index of a tracked window matching the snapshot identity, else -1.  A
 * matching hwnd with a different task/instance/class is a reused handle:
 * the stale entry is returned with *stale set so the caller resets it. */
static int wd_match(const WD *wd, const WDSNAP *s, int *stale)
{
    int i = WDFind(wd, s->hwnd);

    *stale = 0;
    if (i < 0) {
        return -1;
    }
#ifndef WD_FAULT_REUSE
    if (wd->ent[i].task != s->task || wd->ent[i].inst != s->inst ||
        wd->ent[i].cls != s->cls) {
        *stale = 1;
    }
#endif
    return i;
}

/* Fill an entry as a brand-new window seen at the current viewport. */
static void wd_fresh(const WD *wd, WDENT *e, const WDSNAP *s)
{
    e->hwnd = s->hwnd;
    e->task = s->task;
    e->inst = s->inst;
    e->cls = s->cls;
    e->owner = s->owner;
    e->state = s->state;
    e->flags = WD_F_SEEN;
    if (s->state == WD_ST_NORMAL || s->normal) {
        e->flags = (unsigned char)(e->flags | WD_F_HASNORM);
        e->lx = wd_lcl((long)s->x + wd->ox);
        e->ly = wd_lcl((long)s->y + wd->oy);
        e->wid = wd_size(s->wid);
        e->ht = wd_size(s->ht);
        e->sx = s->x;
        e->sy = s->y;
    } else {
        /* No normal rectangle known.  Until the window is restored,
         * lx/ly hold the viewport origin at first sight: Windows will
         * restore it to a screen rectangle valid at that origin. */
        e->lx = wd->ox;
        e->ly = wd->oy;
        e->wid = 0;
        e->ht = 0;
        e->sx = 0;
        e->sy = 0;
    }
}

static void wd_update(const WD *wd, WDENT *e, const WDSNAP *s)
{
    unsigned char prev = e->state;

    e->owner = s->owner;
    e->flags = (unsigned char)(e->flags | WD_F_SEEN);
    e->state = s->state;
    if (s->state != WD_ST_NORMAL) {
        if (s->normal) {
            if (!(e->flags & WD_F_HASNORM) || s->x != e->sx || s->y != e->sy) {
                e->lx = wd_lcl((long)s->x + wd->ox);
                e->ly = wd_lcl((long)s->y + wd->oy);
            }
            e->wid = wd_size(s->wid); e->ht = wd_size(s->ht);
            e->sx = s->x; e->sy = s->y;
            e->flags = (unsigned char)(e->flags | WD_F_HASNORM);
        }
        return;                 /* pinned: keep last normal rectangle */
    }
    e->wid = wd_size(s->wid);
    e->ht = wd_size(s->ht);
    if (prev != WD_ST_NORMAL) {
        if (!(e->flags & WD_F_HASNORM)) {
            e->lx = wd_lcl((long)s->x + e->lx);
            e->ly = wd_lcl((long)s->y + e->ly);
            e->flags = (unsigned char)(e->flags | WD_F_HASNORM);
        }
        /* Windows restored it to its old screen rectangle; remember
         * that, WDPlan moves it back to its logical place if needed. */
        e->sx = s->x;
        e->sy = s->y;
        return;
    }
    if (s->x != e->sx || s->y != e->sy) {
        e->lx = wd_lcl((long)s->x + wd->ox);
        e->ly = wd_lcl((long)s->y + wd->oy);
        e->sx = s->x;
        e->sy = s->y;
    }
}

int WDReconcile(WD *wd, const WDSNAP *snap, unsigned n)
{
    unsigned i;
    unsigned out;
    int idx;
    int stale;

    if (!wd->ready) {
        return WD_E_STATE;
    }
    wd->dropped = 0;
    for (i = 0; i < wd->count; i++) {
        wd->ent[i].flags = (unsigned char)(wd->ent[i].flags & ~WD_F_SEEN);
    }
    for (i = 0; i < n; i++) {
        idx = wd_match(wd, &snap[i], &stale);
        if (idx >= 0 && !stale) {
            wd_update(wd, &wd->ent[idx], &snap[i]);
        } else if (idx >= 0) {
            wd_fresh(wd, &wd->ent[idx], &snap[i]);
        } else if (wd->count < WD_MAXWIN) {
            wd_fresh(wd, &wd->ent[wd->count], &snap[i]);
            wd->count++;
        } else {
            wd->dropped++;
        }
    }
    out = 0;
    for (i = 0; i < wd->count; i++) {
        if (wd->ent[i].flags & WD_F_SEEN) {
            if (out != i) {
                wd->ent[out] = wd->ent[i];
            }
            out++;
        }
    }
    wd->count = (WDU16)out;
    return WD_OK;
}

unsigned WDPlan(WD *wd, WDMOVE *out, unsigned max)
{
    unsigned i;
    unsigned n = 0;
    WDENT *e;
    WDI16 dx;
    WDI16 dy;

    for (i = 0; i < wd->count && n < max; i++) {
        e = &wd->ent[i];
#ifndef WD_FAULT_PIN
        if (e->state != WD_ST_NORMAL || !(e->flags & WD_F_HASNORM)) {
            continue;
        }
#else
        if (!(e->flags & WD_F_HASNORM)) {
            continue;
        }
#endif
        dx = (WDI16)((long)e->lx - wd->ox);
        dy = (WDI16)((long)e->ly - wd->oy);
        if (dx != e->sx || dy != e->sy) {
            out[n].hwnd = e->hwnd;
            out[n].x = dx;
            out[n].y = dy;
            n++;
            e->sx = dx;
            e->sy = dy;
        }
    }
    return n;
}

/* Shift needed to make the entry's caption reachable in the viewport. */
static void wd_reach(const WD *wd, const WDENT *e, long *dx, long *dy)
{
    long g = e->wid < WD_GRABW ? e->wid : WD_GRABW;
    long nx;
    long ny;

    if (g < 1) {
        g = 1;
    }
    if (g > wd->scrw) {
        g = wd->scrw;
    }
    nx = wd_clamp(e->lx, (long)wd->ox - (e->wid - g),
                  (long)wd->ox + wd->scrw - g);
    ny = wd_clamp(e->ly, wd->oy, (long)wd->oy + wd->scrh - wd->caph);
    *dx = nx - e->lx;
    *dy = ny - e->ly;
}

static void wd_shift(WDENT *e, long dx, long dy)
{
    e->lx = wd_lcl((long)e->lx + dx);
    e->ly = wd_lcl((long)e->ly + dy);
}

/* Move one entry's logical position by its owner group's shift and then
 * by whatever its own caption check needs; record the total shift. */
static void wd_rescue1(WD *wd, unsigned i, long gx, long gy,
                       WDI16 *shx, WDI16 *shy)
{
    long dx;
    long dy;

    wd_shift(&wd->ent[i], gx, gy);
#ifdef WD_FAULT_OWNER
    wd_shift(&wd->ent[i], gx, gy);
#endif
    wd_reach(wd, &wd->ent[i], &dx, &dy);
    wd_shift(&wd->ent[i], dx, dy);
    shx[i] = (WDI16)(gx + dx);
    shy[i] = (WDI16)(gy + dy);
}

int WDHome(WD *wd)
{
    WDI16 shx[WD_MAXWIN];
    WDI16 shy[WD_MAXWIN];
    unsigned char done[WD_MAXWIN];
    unsigned i;
    unsigned left = 0;
    int oi;
    int progress;

    if (!wd->ready) {
        return WD_E_STATE;
    }
    wd->ox = 0;
    wd->oy = 0;
    /* Roots (no tracked owner) are rescued first; windows without a
     * normal rectangle have nothing to rescue and shift by zero. */
    for (i = 0; i < wd->count; i++) {
        shx[i] = 0;
        shy[i] = 0;
        done[i] = 0;
        oi = wd->ent[i].owner ? WDFind(wd, wd->ent[i].owner) : -1;
        if (!(wd->ent[i].flags & WD_F_HASNORM)) {
            done[i] = 1;
        } else if (oi < 0) {
            wd_rescue1(wd, i, 0L, 0L, shx, shy);
            done[i] = 1;
        } else {
            left++;
        }
    }
    /* Owned windows follow their owner's total shift, so a dialog keeps
     * its place relative to its owner whatever the table order, then get
     * their own caption check.  Each entry is processed exactly once. */
    do {
        progress = 0;
        for (i = 0; i < wd->count; i++) {
            if (done[i]) {
                continue;
            }
            oi = WDFind(wd, wd->ent[i].owner);
            if (oi < 0 || !done[oi]) {
                continue;
            }
            wd_rescue1(wd, i, shx[oi], shy[oi], shx, shy);
            done[i] = 1;
            left--;
            progress = 1;
        }
    } while (progress && left);
    /* Owner cycles (not produced by Windows): rescue individually. */
    for (i = 0; i < wd->count; i++) {
        if (!done[i]) {
            wd_rescue1(wd, i, 0L, 0L, shx, shy);
        }
    }
    return WD_OK;
}

unsigned WDShutdown(WD *wd, WDMOVE *out, unsigned max)
{
    unsigned n = 0;

    if (WDHome(wd) == WD_OK) {
        n = WDPlan(wd, out, max);
    }
    wd->count = 0;
    wd->dropped = 0;
    return n;
}
