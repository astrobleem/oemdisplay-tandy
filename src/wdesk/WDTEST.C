/* WDTEST.C - host unit tests for the pure WDESK positioning core.
 *
 * Drives WDCORE.C through a mock OS (a table of fake windows) and checks
 * the contract in WDCORE.H.  This file does not depend on the WD_FAULT_*
 * switches of WDCORE.C; those are applied from the outside to prove that
 * the tests catch regressions.  Build and run it with the host compiler
 * wrapper (-x c is required for the upper-case .C extension).
 */
#include <stdio.h>
#include <string.h>
#include "WDCORE.H"

#define SCR_W       320L
#define SCR_H       200L
#define WS_W        2048L
#define WS_H        2048L
#define FAKE_MAX    40
#define NSTEPS      600

typedef struct FWIN {
    WDU16 hwnd;
    WDU16 task;
    WDU16 inst;
    WDU16 cls;
    WDU16 owner;
    WDI16 x;
    WDI16 y;
    WDI16 wid;
    WDI16 ht;
    unsigned char state;
    int visible;
    int moves;                  /* moves received in this operation */
} FWIN;

static FWIN g_os[FAKE_MAX];
static FWIN g_dummy;            /* returned for unknown hwnds */
static int g_nos = 0;
static int g_apply_calls = 0;
static long g_moved = 0;
static WDSNAP g_snap[FAKE_MAX];
static int g_checks = 0;
static int g_fails = 0;
static const char *g_test = "setup";

static const int g_px[6] = {10, 120, -40, 250, 33, 180};
static const int g_py[6] = {5, 60, -20, 130, 90, 0};
static const int g_pw[6] = {100, 80, 60, 50, 120, 70};
static const int g_ph[6] = {60, 40, 90, 70, 50, 80};

#define CHECK(expr) \
    do { \
        g_checks++; \
        if (!(expr)) { \
            g_fails++; \
            printf("FAIL [%s] %s:%d: %s\n", \
                   g_test, __FILE__, __LINE__, #expr); \
        } \
    } while (0)

static long clampl(long v, long lo, long hi)
{
    if (v < lo) {
        return lo;
    }
    if (v > hi) {
        return hi;
    }
    return v;
}

/* Non-zero when a window's caption strip is usable on a screen whose
 * origin is (0,0): top edge inside the screen and at least
 * min(w, WD_GRABW) pixels of the window horizontally on screen. */
static int reachable(long x, long y, long w, long caph)
{
    long need = w < WD_GRABW ? w : WD_GRABW;
    long left = x > 0 ? x : 0;
    long right = x + w < SCR_W ? x + w : SCR_W;

    return y >= 0 && y <= SCR_H - caph && right - left >= need;
}

static const WDENT *ent_for(const WD *wd, unsigned hwnd)
{
    int i = WDFind(wd, hwnd);

    if (i < 0) {
        return NULL;
    }
    return &wd->ent[i];
}

/* ---- mock OS ---------------------------------------------------------- */

static int os_index(unsigned hwnd)
{
    int i;

    for (i = 0; i < g_nos; i++) {
        if (g_os[i].hwnd == hwnd) {
            return i;
        }
    }
    return -1;
}

static FWIN *os_win(unsigned hwnd)
{
    int k = os_index(hwnd);

    if (k < 0) {
        printf("FAIL [%s] no fake window %u\n", g_test, hwnd);
        g_fails++;
        return &g_dummy;
    }
    return &g_os[k];
}

static void os_clear(void)
{
    g_nos = 0;
    g_apply_calls = 0;
    g_moved = 0;
}

/* A new normal, visible, unowned window with identity (1,1,1). */
static void os_open(unsigned hwnd, long x, long y, long w, long h)
{
    FWIN *f;

    CHECK(g_nos < FAKE_MAX);
    if (g_nos >= FAKE_MAX) {
        return;
    }
    f = &g_os[g_nos];
    g_nos++;
    f->hwnd = (WDU16)hwnd;
    f->task = 1;
    f->inst = 1;
    f->cls = 1;
    f->owner = 0;
    f->x = (WDI16)x;
    f->y = (WDI16)y;
    f->wid = (WDI16)w;
    f->ht = (WDI16)h;
    f->state = WD_ST_NORMAL;
    f->visible = 1;
    f->moves = 0;
}

static void os_close(unsigned hwnd)
{
    int k = os_index(hwnd);
    int i;

    CHECK(k >= 0);
    if (k < 0) {
        return;
    }
    for (i = k; i < g_nos - 1; i++) {
        g_os[i] = g_os[i + 1];
    }
    g_nos--;
}

static void os_move_by_user(unsigned hwnd, long x, long y)
{
    FWIN *f = os_win(hwnd);

    f->x = (WDI16)x;
    f->y = (WDI16)y;
}

static void os_resize(unsigned hwnd, long w, long h)
{
    FWIN *f = os_win(hwnd);

    f->wid = (WDI16)w;
    f->ht = (WDI16)h;
}

static void os_set_rect(unsigned hwnd, long x, long y, long w, long h)
{
    FWIN *f = os_win(hwnd);

    f->x = (WDI16)x;
    f->y = (WDI16)y;
    f->wid = (WDI16)w;
    f->ht = (WDI16)h;
}

static void os_set_state(unsigned hwnd, int st)
{
    FWIN *f = os_win(hwnd);

    f->state = (unsigned char)st;
}

static void os_set_owner(unsigned hwnd, unsigned owner)
{
    FWIN *f = os_win(hwnd);

    f->owner = (WDU16)owner;
}

static void os_set_ident(unsigned hwnd, unsigned task, unsigned inst,
                         unsigned cls)
{
    FWIN *f = os_win(hwnd);

    f->task = (WDU16)task;
    f->inst = (WDU16)inst;
    f->cls = (WDU16)cls;
}

static void os_set_visible(unsigned hwnd, int v)
{
    FWIN *f = os_win(hwnd);

    f->visible = v;
}

/* Build WDSNAP[] from the visible fake windows, in table order. */
static unsigned snap_now(void)
{
    unsigned n = 0;
    int i;

    for (i = 0; i < g_nos; i++) {
        if (g_os[i].visible) {
            g_snap[n].hwnd = g_os[i].hwnd;
            g_snap[n].task = g_os[i].task;
            g_snap[n].inst = g_os[i].inst;
            g_snap[n].cls = g_os[i].cls;
            g_snap[n].owner = g_os[i].owner;
            g_snap[n].x = g_os[i].x;
            g_snap[n].y = g_os[i].y;
            g_snap[n].wid = g_os[i].wid;
            g_snap[n].ht = g_os[i].ht;
            g_snap[n].state = g_os[i].state;
            n++;
        }
    }
    return n;
}

static void os_begin_op(void)
{
    int i;

    for (i = 0; i < g_nos; i++) {
        g_os[i].moves = 0;
    }
}

/* Apply moves to the fake screen.  Moving a pinned window is a failure. */
static void os_apply(const WDMOVE *mv, unsigned n)
{
    unsigned i;
    FWIN *f;

    g_apply_calls++;
    for (i = 0; i < n; i++) {
        f = os_win(mv[i].hwnd);
        CHECK(f->state == WD_ST_NORMAL);
        f->x = mv[i].x;
        f->y = mv[i].y;
        f->moves++;
        g_moved++;
    }
}

/* ---- driver helpers --------------------------------------------------- */

static void fresh(WD *wd)
{
    memset(wd, 0, sizeof(*wd));
    CHECK(WDInit(wd, SCR_W, SCR_H, WS_W, WS_H, 0L) == WD_OK);
    os_clear();
}

/* Snapshot, begin an operation and reconcile. */
static void recon(WD *wd)
{
    unsigned cnt = snap_now();

    os_begin_op();
    CHECK(WDReconcile(wd, g_snap, cnt) == WD_OK);
}

/* Reconcile and plan at the current viewport.  Returns moves applied. */
static int sync_op(WD *wd)
{
    WDMOVE mv[WD_MAXWIN];
    unsigned n;

    recon(wd);
    n = WDPlan(wd, mv, WD_MAXWIN);
    if (n > 0) {
        os_apply(mv, n);
    }
    return (int)n;
}

/* reconcile, WDSetViewport, WDPlan, apply.  Returns 1 when the origin
 * changed. */
static int pan_to(WD *wd, long x, long y)
{
    WDMOVE mv[WD_MAXWIN];
    unsigned n;
    int ch;

    recon(wd);
    ch = WDSetViewport(wd, x, y);
    n = WDPlan(wd, mv, WD_MAXWIN);
    if (n > 0) {
        os_apply(mv, n);
    }
    return ch;
}

/* reconcile, WDHome, WDPlan, apply.  Returns moves applied. */
static unsigned home_op(WD *wd)
{
    WDMOVE mv[WD_MAXWIN];
    unsigned n;

    recon(wd);
    CHECK(WDHome(wd) == WD_OK);
    n = WDPlan(wd, mv, WD_MAXWIN);
    if (n > 0) {
        os_apply(mv, n);
    }
    return n;
}

/* reconcile, WDShutdown, apply.  Returns moves applied. */
static unsigned shutdown_op(WD *wd)
{
    WDMOVE mv[WD_MAXWIN];
    unsigned n;

    recon(wd);
    n = WDShutdown(wd, mv, WD_MAXWIN);
    if (n > 0) {
        os_apply(mv, n);
    }
    return n;
}

/* ---- tests ------------------------------------------------------------ */

static void test_repeated_pans(void)
{
    WD wd;
    unsigned long seed = 12345UL;
    long tx;
    long ty;
    int step;
    int i;

    g_test = "test_repeated_pans";
    fresh(&wd);
    for (i = 0; i < 6; i++) {
        os_open((unsigned)(i + 1), g_px[i], g_py[i], g_pw[i], g_ph[i]);
    }
    sync_op(&wd);
    CHECK(wd.count == 6);
    for (step = 0; step < NSTEPS; step++) {
        if (step % 10 == 9) {
            tx = 0L;
            ty = 0L;
        } else {
            seed = (seed * 1103515245UL + 12345UL) & 0x7fffffffUL;
            tx = (long)((seed >> 8) % 2601UL) - 300L;
            seed = (seed * 1103515245UL + 12345UL) & 0x7fffffffUL;
            ty = (long)((seed >> 8) % 2401UL) - 200L;
        }
        pan_to(&wd, tx, ty);
        CHECK(wd.ox == clampl(tx, 0L, WS_W - SCR_W));
        CHECK(wd.oy == clampl(ty, 0L, WS_H - SCR_H));
        CHECK(wd.count == 6);
        for (i = 0; i < 6; i++) {
            FWIN *f = os_win((unsigned)(i + 1));

            CHECK(f->x == g_px[i] - wd.ox);
            CHECK(f->y == g_py[i] - wd.oy);
            if (step % 10 == 9) {
                CHECK(f->x == g_px[i] && f->y == g_py[i]);
            }
        }
    }
}

static void test_spacing_and_size(void)
{
    WD wd;
    unsigned long seed = 987654UL;
    long tx;
    long ty;
    int step;
    int i;
    int j;
    const WDENT *e;

    g_test = "test_spacing_and_size";
    fresh(&wd);
    for (i = 0; i < 6; i++) {
        os_open((unsigned)(i + 1), g_px[i], g_py[i], g_pw[i], g_ph[i]);
    }
    sync_op(&wd);
    for (step = 0; step < 300; step++) {
        seed = (seed * 1103515245UL + 12345UL) & 0x7fffffffUL;
        tx = (long)((seed >> 8) % 2601UL) - 300L;
        seed = (seed * 1103515245UL + 12345UL) & 0x7fffffffUL;
        ty = (long)((seed >> 8) % 2401UL) - 200L;
        pan_to(&wd, tx, ty);
        for (i = 0; i < 6; i++) {
            FWIN *fi = os_win((unsigned)(i + 1));

            CHECK(fi->wid == g_pw[i] && fi->ht == g_ph[i]);
            e = ent_for(&wd, (unsigned)(i + 1));
            CHECK(e != NULL && e->wid == g_pw[i] && e->ht == g_ph[i]);
            CHECK(e != NULL && e->lx == g_px[i] && e->ly == g_py[i]);
            for (j = i + 1; j < 6; j++) {
                FWIN *fj = os_win((unsigned)(j + 1));

                CHECK(fi->x - fj->x == g_px[i] - g_px[j]);
                CHECK(fi->y - fj->y == g_py[i] - g_py[j]);
            }
        }
    }
}

static void test_edges_and_extremes(void)
{
    static const long tx[4] = {0L, 2000000000L, 1000L, -2000000000L};
    static const long ty[4] = {0L, 2000000000L, 700L, 5L};
    WD wd;
    long exp_x;
    long exp_y;
    int i;

    g_test = "test_edges_and_extremes";
    memset(&wd, 0, sizeof(wd));
    CHECK(WDSetViewport(&wd, 5L, 5L) == WD_E_STATE);
    CHECK(WDReconcile(&wd, g_snap, 0) == WD_E_STATE);
    CHECK(WDHome(&wd) == WD_E_STATE);

    CHECK(WDInit(&wd, SCR_W, SCR_H, WS_W, WS_H, 0L) == WD_OK);
    CHECK(wd.ready == 1);
    CHECK(wd.caph == WD_CAPH_DEF);
    CHECK(WDInit(&wd, 4096L, 4096L, 4096L, 4096L, -5L) == WD_OK);
    CHECK(wd.ready == 1 && wd.caph == WD_CAPH_DEF);
    CHECK(WDInit(&wd, SCR_W, SCR_H, WS_W, WS_H, 0L) == WD_OK);

    CHECK(WDInit(&wd, 0L, SCR_H, WS_W, WS_H, 0L) == WD_E_RANGE);
    CHECK(wd.ready == 0);
    CHECK(WDSetViewport(&wd, 5L, 5L) == WD_E_STATE);
    CHECK(WDInit(&wd, -1L, SCR_H, WS_W, WS_H, 0L) == WD_E_RANGE);
    CHECK(wd.ready == 0);
    CHECK(WDInit(&wd, SCR_W, 4097L, WS_W, WS_H, 0L) == WD_E_RANGE);
    CHECK(wd.ready == 0);
    CHECK(WDInit(&wd, 4097L, SCR_H, WS_W, WS_H, 0L) == WD_E_RANGE);
    CHECK(wd.ready == 0);
    CHECK(WDInit(&wd, SCR_W, SCR_H, 100L, WS_H, 0L) == WD_E_RANGE);
    CHECK(wd.ready == 0);
    CHECK(WDInit(&wd, SCR_W, SCR_H, WS_W, 100L, 0L) == WD_E_RANGE);
    CHECK(wd.ready == 0);
    CHECK(WDInit(&wd, SCR_W, SCR_H, 4097L, WS_H, 0L) == WD_E_RANGE);
    CHECK(wd.ready == 0);
    CHECK(WDSetViewport(&wd, 5L, 5L) == WD_E_STATE);
    CHECK(WDReconcile(&wd, g_snap, 0) == WD_E_STATE);

    fresh(&wd);
    CHECK(WDSetViewport(&wd, -2000000000L, -2000000000L) == 0);
    CHECK(wd.ox == 0 && wd.oy == 0);
    CHECK(WDSetViewport(&wd, 2000000000L, 2000000000L) == 1);
    CHECK(wd.ox == 1728 && wd.oy == 1848);
    CHECK(WDSetViewport(&wd, -2000000000L, 2000000000L) == 1);
    CHECK(wd.ox == 0 && wd.oy == 1848);
    CHECK(WDSetViewport(&wd, 2000000000L, -2000000000L) == 1);
    CHECK(wd.ox == 1728 && wd.oy == 0);

    /* Extreme stored values, plus a window far off-screen. */
    fresh(&wd);
    os_open(1, -32768L, -32768L, -32768L, 32767L);
    os_open(2, 32767L, 32767L, 32767L, -32768L);
    os_open(3, -3000L, -2500L, 100L, 80L);
    CHECK(sync_op(&wd) == 2);
    CHECK(os_win(3)->x == -3000 && os_win(3)->y == -2500);
    {
        const WDENT *e1 = ent_for(&wd, 1);
        const WDENT *e2 = ent_for(&wd, 2);

        CHECK(e1 != NULL && e1->wid == 0 && e1->ht == WD_SMAX);
        CHECK(e1 != NULL && e1->lx == WD_LMIN && e1->ly == WD_LMIN);
        CHECK(e2 != NULL && e2->wid == WD_SMAX && e2->ht == 0);
        CHECK(e2 != NULL && e2->lx == WD_LMAX && e2->ly == WD_LMAX);
    }
    for (i = 0; i < 4; i++) {
        pan_to(&wd, tx[i], ty[i]);
        exp_x = clampl(-32768L, WD_LMIN, WD_LMAX) - wd.ox;
        exp_y = clampl(-32768L, WD_LMIN, WD_LMAX) - wd.oy;
        CHECK(exp_x >= -32768L && exp_x <= 32767L);
        CHECK(exp_y >= -32768L && exp_y <= 32767L);
        CHECK((long)os_win(1)->x == exp_x);
        CHECK((long)os_win(1)->y == exp_y);
        exp_x = clampl(32767L, WD_LMIN, WD_LMAX) - wd.ox;
        exp_y = clampl(32767L, WD_LMIN, WD_LMAX) - wd.oy;
        CHECK(exp_x >= -32768L && exp_x <= 32767L);
        CHECK(exp_y >= -32768L && exp_y <= 32767L);
        CHECK((long)os_win(2)->x == exp_x);
        CHECK((long)os_win(2)->y == exp_y);
        CHECK(os_win(3)->x == -3000L - wd.ox);
        CHECK(os_win(3)->y == -2500L - wd.oy);
    }
}

static void test_open_close(void)
{
    WD wd;

    g_test = "test_open_close";
    fresh(&wd);
    os_open(1, 10L, 10L, 50L, 50L);
    os_open(2, 70L, 10L, 50L, 50L);
    os_open(3, 130L, 10L, 50L, 50L);
    os_open(4, 190L, 10L, 50L, 50L);
    sync_op(&wd);
    CHECK(wd.count == 4);

    os_close(2);
    sync_op(&wd);
    CHECK(WDFind(&wd, 2) == -1);
    CHECK(wd.count == 3);
    CHECK(wd.ent[0].hwnd == 1 && wd.ent[1].hwnd == 3);
    CHECK(wd.ent[2].hwnd == 4);

    os_close(1);
    sync_op(&wd);
    CHECK(WDFind(&wd, 1) == -1 && wd.count == 2);
    CHECK(wd.ent[0].hwnd == 3 && wd.ent[1].hwnd == 4);

    os_set_visible(3, 0);
    sync_op(&wd);
    CHECK(WDFind(&wd, 3) == -1 && wd.count == 1);
    os_set_visible(3, 1);
    sync_op(&wd);
    CHECK(WDFind(&wd, 3) >= 0 && wd.count == 2);
}

/* Shared body: window 1 is panned to (100,60), closed, and a new window
 * with the same hwnd appears at the same screen spot after the viewport
 * has moved back to (0,0) without a reconcile.  which: 0 task, 1 inst,
 * 2 class. */
static void reuse_case(int which)
{
    static const char *names[3] = {
        "test_handle_reuse (task)",
        "test_handle_reuse (inst)",
        "test_handle_reuse (class)"
    };
    WD wd;
    const WDENT *e;
    unsigned task = 1;
    unsigned inst = 1;
    unsigned cls = 1;

    g_test = names[which];
    fresh(&wd);
    os_open(1, 10L, 5L, 100L, 60L);
    os_open(2, 200L, 30L, 50L, 50L);
    sync_op(&wd);
    pan_to(&wd, 100L, 60L);             /* hwnd 1 screen now (-90,-55) */
    os_close(1);
    CHECK(WDSetViewport(&wd, 0L, 0L) == 1);
    if (which == 0) {
        task = 99;
    }
    if (which == 1) {
        inst = 7;
    }
    if (which == 2) {
        cls = 7;
    }
    os_open(1, -90L, -55L, 100L, 60L);
    os_set_ident(1, task, inst, cls);
    /* Window 2 was left displaced by the direct viewport change, so it
     * may legitimately be moved; window 1 must not be. */
    sync_op(&wd);
    CHECK(os_win(1)->moves == 0);
    e = ent_for(&wd, 1);
    CHECK(e != NULL && e->lx == -90 && e->ly == -55);
    CHECK(os_win(1)->x == -90 && os_win(1)->y == -55);
    CHECK(wd.count == 2);
}

static void test_handle_reuse(void)
{
    WD wd;
    const WDENT *e;
    int idx;

    reuse_case(0);
    reuse_case(1);
    reuse_case(2);

    g_test = "test_handle_reuse (same identity)";
    fresh(&wd);
    os_open(5, 50L, 40L, 100L, 80L);
    os_open(6, 0L, 0L, 40L, 40L);
    sync_op(&wd);
    pan_to(&wd, 100L, 60L);
    idx = WDFind(&wd, 5);
    os_move_by_user(5, -20L, -10L);
    sync_op(&wd);
    CHECK(WDFind(&wd, 5) == idx && wd.count == 2);
    e = ent_for(&wd, 5);
    CHECK(e != NULL && e->lx == 80 && e->ly == 50);
}

static void test_user_move_resize(void)
{
    WD wd;
    const WDENT *e;
    int before;

    g_test = "test_user_move_resize";
    fresh(&wd);
    os_open(7, 50L, 40L, 100L, 80L);
    sync_op(&wd);
    pan_to(&wd, 500L, 300L);            /* screen now (-450,-260) */
    os_move_by_user(7, -400L, -200L);   /* drag while displaced */
    before = g_apply_calls;
    CHECK(sync_op(&wd) == 0);
    CHECK(g_apply_calls == before);
    e = ent_for(&wd, 7);
    CHECK(e != NULL && e->lx == 100 && e->ly == 100);
    CHECK(e != NULL && e->wid == 100 && e->ht == 80);
    pan_to(&wd, 0L, 0L);
    CHECK(os_win(7)->x == 100 && os_win(7)->y == 100);

    os_resize(7, 150L, 120L);
    CHECK(sync_op(&wd) == 0);
    e = ent_for(&wd, 7);
    CHECK(e != NULL && e->lx == 100 && e->ly == 100);
    CHECK(e != NULL && e->wid == 150 && e->ht == 120);
    CHECK(os_win(7)->x == 100 && os_win(7)->y == 100);
    CHECK(os_win(7)->wid == 150 && os_win(7)->ht == 120);

    /* Left edge dragged 20 px right: top-left changes, adopted as a move. */
    os_set_rect(7, 120L, 100L, 130L, 120L);
    CHECK(sync_op(&wd) == 0);
    e = ent_for(&wd, 7);
    CHECK(e != NULL && e->lx == 120 && e->wid == 130);
    pan_to(&wd, 10L, 0L);
    CHECK(os_win(7)->x == 110 && os_win(7)->y == 100);
}

static void minimize_case(void)
{
    WD wd;
    const WDENT *e;
    int before;

    g_test = "test_minimize_maximize (minimize)";
    fresh(&wd);
    os_open(8, 50L, 40L, 100L, 80L);
    sync_op(&wd);
    pan_to(&wd, 100L, 50L);             /* fake screen now (-50,-10) */
    os_set_state(8, WD_ST_ICONIC);
    CHECK(sync_op(&wd) == 0);
    before = g_apply_calls;
    pan_to(&wd, 300L, 200L);            /* pinned: no move */
    CHECK(g_apply_calls == before);
    CHECK(os_win(8)->moves == 0);
    e = ent_for(&wd, 8);
    CHECK(e != NULL && e->lx == 50 && e->ly == 40);
    CHECK(e != NULL && e->wid == 100 && e->ht == 80);
    CHECK(e != NULL && e->state == WD_ST_ICONIC);
    os_set_state(8, WD_ST_NORMAL);      /* restored at stale (-50,-10) */
    CHECK(sync_op(&wd) == 1);
    CHECK(os_win(8)->moves == 1);
    CHECK(os_win(8)->x == 50 - 300 && os_win(8)->y == 40 - 200);
    CHECK(sync_op(&wd) == 0);
}

static void zoom_case(void)
{
    WD wd;
    const WDENT *e;
    int before;

    g_test = "test_minimize_maximize (maximize)";
    fresh(&wd);
    pan_to(&wd, 300L, 200L);
    os_open(9, 30L, 20L, 100L, 80L);
    sync_op(&wd);                       /* logical (330,220) */
    os_set_rect(9, 0L, 0L, 320L, 200L);
    os_set_state(9, WD_ST_ZOOMED);
    CHECK(sync_op(&wd) == 0);
    before = g_apply_calls;
    pan_to(&wd, 400L, 250L);            /* pinned: no move */
    CHECK(g_apply_calls == before);
    CHECK(os_win(9)->moves == 0);
    e = ent_for(&wd, 9);
    CHECK(e != NULL && e->lx == 330 && e->ly == 220);
    CHECK(e != NULL && e->wid == 100 && e->ht == 80);
    CHECK(e != NULL && e->state == WD_ST_ZOOMED);
    os_set_rect(9, 30L, 20L, 100L, 80L);
    os_set_state(9, WD_ST_NORMAL);
    CHECK(sync_op(&wd) == 1);
    CHECK(os_win(9)->x == 330 - 400 && os_win(9)->y == 220 - 250);
}

static void zoom_open_case(void)
{
    WD wd;
    const WDENT *e;
    int before;

    g_test = "test_minimize_maximize (opened maximized)";
    fresh(&wd);
    pan_to(&wd, 400L, 250L);
    os_open(10, 0L, 0L, 320L, 200L);
    os_set_state(10, WD_ST_ZOOMED);
    CHECK(sync_op(&wd) == 0);
    e = ent_for(&wd, 10);
    CHECK(e != NULL && e->lx == 400 && e->ly == 250);
    before = g_apply_calls;
    pan_to(&wd, 450L, 260L);
    CHECK(g_apply_calls == before);
    os_set_rect(10, 60L, 30L, 100L, 80L);
    os_set_state(10, WD_ST_NORMAL);
    CHECK(sync_op(&wd) == 1);
    e = ent_for(&wd, 10);
    CHECK(e != NULL && e->lx == 460 && e->ly == 280);
    CHECK(os_win(10)->x == 10 && os_win(10)->y == 20);
}

static void first_iconic_case(void)
{
    WD wd;
    const WDENT *e;
    int before;

    g_test = "test_minimize_maximize (first seen iconic)";
    fresh(&wd);
    pan_to(&wd, 100L, 50L);
    os_open(11, 30L, 20L, 100L, 80L);
    os_set_state(11, WD_ST_ICONIC);
    CHECK(sync_op(&wd) == 0);
    e = ent_for(&wd, 11);
    CHECK(e != NULL && e->lx == 100 && e->ly == 50);
    before = g_apply_calls;
    pan_to(&wd, 200L, 120L);
    CHECK(g_apply_calls == before);
    os_set_state(11, WD_ST_NORMAL);     /* restored at its own rect */
    CHECK(sync_op(&wd) == 1);
    e = ent_for(&wd, 11);
    CHECK(e != NULL && e->lx == 130 && e->ly == 70);
    CHECK(os_win(11)->x == -70 && os_win(11)->y == -50);
}

static void test_minimize_maximize(void)
{
    minimize_case();
    zoom_case();
    zoom_open_case();
    first_iconic_case();
}

static void test_owner_dialog(void)
{
    static const long sx[6] = {50L, 700L, 0L, 300L, 1000L, 0L};
    static const long sy[6] = {30L, 400L, 0L, 10L, 1000L, 0L};
    WD wd;
    int i;

    g_test = "test_owner_dialog (pan)";
    fresh(&wd);
    os_open(20, 100L, 60L, 200L, 150L);
    os_open(21, 150L, 90L, 120L, 100L);
    os_set_owner(21, 20);
    os_open(22, 250L, 80L, 60L, 40L);
    os_set_owner(22, 20);
    sync_op(&wd);
    for (i = 0; i < 6; i++) {
        pan_to(&wd, sx[i], sy[i]);
        CHECK(os_win(20)->moves == 1);
        CHECK(os_win(21)->moves == 1);
        CHECK(os_win(22)->moves == 1);
        CHECK(os_win(21)->x - os_win(20)->x == 50);
        CHECK(os_win(21)->y - os_win(20)->y == 30);
        CHECK(os_win(22)->x - os_win(20)->x == 150);
        CHECK(os_win(22)->y - os_win(20)->y == 20);
    }

    g_test = "test_owner_dialog (home, far owner)";
    fresh(&wd);
    os_open(20, -5000L, -4000L, 200L, 150L);
    os_open(21, -4900L, -3950L, 120L, 100L);
    os_set_owner(21, 20);
    os_open(22, -4850L, -3980L, 60L, 40L);
    os_set_owner(22, 20);
    sync_op(&wd);
    CHECK(home_op(&wd) == 3);
    CHECK(os_win(20)->moves == 1 && os_win(21)->moves == 1);
    CHECK(os_win(22)->moves == 1);
    CHECK(os_win(21)->x - os_win(20)->x == 100);
    CHECK(os_win(21)->y - os_win(20)->y == 50);
    CHECK(os_win(22)->x - os_win(20)->x == 150);
    CHECK(os_win(22)->y - os_win(20)->y == 20);
    CHECK(reachable(os_win(20)->x, os_win(20)->y, os_win(20)->wid,
                    wd.caph));
    CHECK(reachable(os_win(21)->x, os_win(21)->y, os_win(21)->wid,
                    wd.caph));
    CHECK(reachable(os_win(22)->x, os_win(22)->y, os_win(22)->wid,
                    wd.caph));
}

static void test_home_shutdown(void)
{
    WD wd;
    WDMOVE mv[WD_MAXWIN];
    unsigned n;
    int i;

    g_test = "test_home_shutdown";
    fresh(&wd);
    os_open(1, 50L, 40L, 100L, 80L);
    os_open(2, 400L, 300L, 60L, 50L);
    os_open(3, -200L, -150L, 300L, 200L);
    os_open(4, 1500L, 1200L, 120L, 90L);
    sync_op(&wd);
    pan_to(&wd, 1500L, 1000L);
    CHECK(!reachable(os_win(3)->x, os_win(3)->y, os_win(3)->wid,
                     wd.caph));
    home_op(&wd);
    CHECK(wd.ox == 0 && wd.oy == 0);
    for (i = 1; i <= 4; i++) {
        FWIN *f = os_win((unsigned)i);

        CHECK(reachable(f->x, f->y, f->wid, wd.caph));
        CHECK(f->moves <= 1);
    }

    /* Already reachable at (0,0): Home emits nothing. */
    CHECK(WDHome(&wd) == WD_OK);
    CHECK(WDPlan(&wd, mv, WD_MAXWIN) == 0);

    /* Strand again, then shut down. */
    pan_to(&wd, 1500L, 1000L);
    n = shutdown_op(&wd);
    CHECK(n >= 1);
    CHECK(wd.count == 0 && wd.ready == 1);
    CHECK(WDFind(&wd, 1) == -1);
    for (i = 1; i <= 4; i++) {
        FWIN *f = os_win((unsigned)i);

        CHECK(reachable(f->x, f->y, f->wid, wd.caph));
    }
    sync_op(&wd);
    CHECK(wd.count == 4);
}

/* A minimized window with a stored normal rect far off-screen: Home
 * rescues the stored rect, emits nothing for it, and a later restore is
 * placed reachably. */
static void test_home_iconic(void)
{
    WD wd;

    g_test = "test_home_shutdown (iconic rescue)";
    fresh(&wd);
    os_open(5, -2000L, -1500L, 100L, 80L);
    sync_op(&wd);
    os_set_state(5, WD_ST_ICONIC);
    CHECK(sync_op(&wd) == 0);
    home_op(&wd);
    CHECK(os_win(5)->moves == 0);
    CHECK(os_win(5)->x == -2000);
    os_set_state(5, WD_ST_NORMAL);
    CHECK(sync_op(&wd) == 1);
    CHECK(reachable(os_win(5)->x, os_win(5)->y, os_win(5)->wid,
                    wd.caph));
}

static void test_no_op_pans(void)
{
    WD wd;
    WDMOVE mv[WD_MAXWIN];
    int before;
    long before_moved;

    g_test = "test_no_op_pans";
    fresh(&wd);
    before = g_apply_calls;
    CHECK(WDSetViewport(&wd, 0L, 0L) == 0);
    CHECK(WDPlan(&wd, mv, WD_MAXWIN) == 0);
    CHECK(WDSetViewport(&wd, 300L, 200L) == 1);
    CHECK(WDPlan(&wd, mv, WD_MAXWIN) == 0);
    CHECK(pan_to(&wd, 300L, 200L) == 0);
    CHECK(sync_op(&wd) == 0);
    CHECK(g_apply_calls == before);

    os_open(1, 50L, 40L, 100L, 80L);
    os_open(2, 200L, 100L, 60L, 40L);
    sync_op(&wd);
    before = g_apply_calls;
    before_moved = g_moved;
    CHECK(WDSetViewport(&wd, 300L, 200L) == 0);
    CHECK(WDPlan(&wd, mv, WD_MAXWIN) == 0);
    CHECK(pan_to(&wd, 300L, 200L) == 0);
    CHECK(sync_op(&wd) == 0);
    CHECK(g_apply_calls == before && g_moved == before_moved);

    fresh(&wd);
    os_open(3, 50L, 40L, 100L, 80L);
    os_set_state(3, WD_ST_ICONIC);
    os_open(4, 60L, 50L, 100L, 80L);
    os_set_state(4, WD_ST_ZOOMED);
    sync_op(&wd);
    before = g_apply_calls;
    CHECK(pan_to(&wd, 100L, 50L) == 1);
    CHECK(g_apply_calls == before);
    CHECK(os_win(3)->moves == 0 && os_win(4)->moves == 0);
}

static void test_table_full(void)
{
    WD wd;
    WDMOVE mv[WD_MAXWIN];
    int seen[WD_MAXWIN + 4];
    unsigned n;
    int i;
    int k;

    g_test = "test_table_full";
    fresh(&wd);
    for (i = 0; i < WD_MAXWIN + 3; i++) {
        os_open((unsigned)(i + 1), 10L * i, 5L * i, 30L, 20L);
    }
    sync_op(&wd);
    CHECK(wd.count == WD_MAXWIN);
    CHECK(wd.dropped == 3);
    for (i = 0; i < WD_MAXWIN; i++) {
        CHECK(wd.ent[i].hwnd == (WDU16)(i + 1));
    }
    for (i = WD_MAXWIN; i < WD_MAXWIN + 3; i++) {
        CHECK(WDFind(&wd, (unsigned)(i + 1)) == -1);
    }

    pan_to(&wd, 100L, 50L);
    CHECK(wd.dropped == 3);
    for (i = WD_MAXWIN; i < WD_MAXWIN + 3; i++) {
        CHECK(os_win((unsigned)(i + 1))->moves == 0);
        CHECK(os_win((unsigned)(i + 1))->x == 10 * i);
    }

    /* Partial plans: 5 then the remainder, no loss, no duplicates. */
    recon(&wd);
    CHECK(WDSetViewport(&wd, 200L, 100L) == 1);
    for (k = 0; k < WD_MAXWIN + 4; k++) {
        seen[k] = 0;
    }
    n = WDPlan(&wd, mv, 5);
    CHECK(n == 5);
    os_apply(mv, n);
    for (k = 0; k < (int)n; k++) {
        seen[mv[k].hwnd]++;
    }
    n = WDPlan(&wd, mv, WD_MAXWIN);
    CHECK(n == WD_MAXWIN - 5);
    os_apply(mv, n);
    for (k = 0; k < (int)n; k++) {
        seen[mv[k].hwnd]++;
    }
    CHECK(WDPlan(&wd, mv, WD_MAXWIN) == 0);
    for (i = 1; i <= WD_MAXWIN; i++) {
        CHECK(seen[i] == 1);
    }
    CHECK(seen[25] == 0 && seen[26] == 0 && seen[27] == 0);
    for (i = 0; i < WD_MAXWIN; i++) {
        CHECK(os_win((unsigned)(i + 1))->x == 10 * i - 200);
        CHECK(os_win((unsigned)(i + 1))->y == 5 * i - 100);
    }
}

static void test_sizes(void)
{
    g_test = "test_sizes";
    printf("sizeof(WDENT) = %lu, sizeof(WD) = %lu\n",
           (unsigned long)sizeof(WDENT), (unsigned long)sizeof(WD));
    CHECK(sizeof(WDENT) == 24 && sizeof(WDI16) == 2);
}

/* Regression: an owned window whose owner is later in the table must
 * still follow its owner's Home shift (offset stays (50,20)). */
static void test_owner_chain(void)
{
    WD wd;

    g_test = "owner_chain";
    fresh(&wd);
    os_open(30, -5000L, -4000L, 200L, 150L);
    os_open(32, -4850L, -3930L, 60L, 40L);
    os_set_owner(32, 31);
    os_open(31, -4900L, -3950L, 120L, 100L);
    os_set_owner(31, 30);
    sync_op(&wd);
    home_op(&wd);
    CHECK(os_win(32)->x - os_win(31)->x == 50);
    CHECK(os_win(32)->y - os_win(31)->y == 20);
}

int main(void)
{
    test_repeated_pans();
    test_spacing_and_size();
    test_edges_and_extremes();
    test_open_close();
    test_handle_reuse();
    test_user_move_resize();
    test_minimize_maximize();
    test_owner_dialog();
    test_home_shutdown();
    test_home_iconic();
    test_no_op_pans();
    test_table_full();
    test_sizes();
    test_owner_chain();
    if (g_fails) {
        printf("FAILED: %d checks, %d failed\n", g_checks, g_fails);
        return 1;
    }
    printf("PASS: %d checks, 0 failed\n", g_checks);
    return 0;
}
