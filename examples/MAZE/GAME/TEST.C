/*
 * TEST.C - Tandy Maze rules and renderer regression.
 *
 * Host: gcc -x c -std=c89 -DHOSTMAIN TEST.C (see TEST.PY; ASan/UBSan).
 * Native: Microsoft C 6 /G0 as a Windows app (BUILD.PY --main TEST.C)
 * that writes C:\MAZETEST.LOG. The renderer's 8088 build uses inline
 * assembly where the host uses C, and int is 16 bits there: the replay
 * checksum must match between the two.
 */
#ifdef HOSTMAIN
#define MAZE_HOST
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#else
#define WINVER 0x0300
#include <windows.h>
#endif
#include "GAME.H"
#include "VIEW.H"

#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)

static unsigned long ck;
static void mixin(unsigned long v)
{
    ck = (ck * 31UL + v) & 0xFFFFFFFFUL;
}

/* ---- maze structure ----------------------------------------------------- */
static int checkmaze(void)
{
    int x, y, open = 0, exits = 0, d, ok;
    /* cells open, outer wall closed except the exit */
    for (y = 0; y < msize; ++y)
        for (x = 0; x < msize; ++x) {
            if ((x & 1) && (y & 1)) CHECK(grid[y][x] == B_OPEN);
            if (!(x & 1) && !(y & 1)) CHECK(grid[y][x] == B_WALL);
            if (x == 0 || y == 0 || x == msize - 1 || y == msize - 1) {
                if (grid[y][x] == B_EXIT) ++exits;
                else CHECK(grid[y][x] == B_WALL);
            } else CHECK(grid[y][x] != B_EXIT);
            if (grid[y][x] == B_OPEN) ++open;
        }
    CHECK(exits == 1);
    CHECK(grid[ey][ex] == B_EXIT);
    /* perfect maze: n*n cells joined by n*n-1 passages, all connected */
    CHECK(open == 2 * ncell * ncell - 1);
    bfs(1, 1);
    for (y = 1; y < msize; y += 2)
        for (x = 1; x < msize; x += 2) CHECK(dist[y][x] != 0xFFFFu);
    /* the exit opens off a boundary cell, at par - 1 from the start */
    ok = 0;
    for (d = 0; d < 4; ++d) {
        x = ex + ddx[d]; y = ey + ddy[d];
        if (x > 0 && y > 0 && x < msize - 1 && y < msize - 1 &&
            grid[y][x] == B_OPEN && (int)dist[y][x] + 1 == par) ok = 1;
    }
    CHECK(ok);
    CHECK(par >= msize - 2);            /* at least across the maze      */
    return 0;
}

/* Walk the shortest path with the real controls; must take par moves. */
static int walkpar(void)
{
    int steps = 0, d, best, bd, x, y, guard = 0;
    bfs(ex + (ex == 0 ? 1 : ex == msize - 1 ? -1 : 0),
        ey + (ey == 0 ? 1 : ey == msize - 1 ? -1 : 0));
    while (!(gev & EV_EXIT) && guard++ < 4000) {
        best = 0x7FFF; bd = -1;
        for (d = 0; d < 4; ++d) {
            x = px + ddx[d]; y = py + ddy[d];
            if (blk(x, y) == B_EXIT) { bd = d; best = -1; break; }
            if (blk(x, y) == B_OPEN && (int)dist[y][x] < best) {
                best = (int)dist[y][x]; bd = d;
            }
        }
        CHECK(bd >= 0);
        while (pdir != bd) act(((bd - pdir) & 3) == 3 ? A_LEFT : A_RIGHT);
        CHECK(act(A_FWD));
        ++steps;
    }
    CHECK(gev & EV_EXIT);
    CHECK(moves == steps && moves == par);
    return 0;
}

static int movement(void)
{
    int x, y, d, m;
    newgame(7UL);
    gev = 0;
    /* face a wall: forward bumps, does not count */
    for (d = 0; d < 4 && blk(px + ddx[pdir], py + ddy[pdir]) != B_WALL; ++d)
        act(A_RIGHT);
    CHECK(blk(px + ddx[pdir], py + ddy[pdir]) == B_WALL);
    x = px; y = py; m = moves; gev = 0;
    CHECK(!act(A_FWD));
    CHECK(px == x && py == y && moves == m && (gev & EV_BUMP) && bumps == 1);
    /* turns change facing only */
    d = pdir; gev = 0;
    act(A_LEFT); CHECK(pdir == ((d + 3) & 3) && moves == m);
    act(A_RIGHT); act(A_RIGHT); CHECK(pdir == ((d + 1) & 3));
    act(A_ABOUT); CHECK(pdir == ((d + 3) & 3));
    /* find an open way, step, then step back without turning */
    for (d = 0; d < 4 && blk(px + ddx[pdir], py + ddy[pdir]) != B_OPEN; ++d)
        act(A_RIGHT);
    x = px; y = py;
    CHECK(act(A_FWD) && moves == m + 1 && (px != x || py != y));
    d = pdir;
    CHECK(act(A_BACK) && px == x && py == y && pdir == d && moves == m + 2);
    return 0;
}

static void setcol(int c, int r, int g, int b, int i)
{
    int y;
    for (y = 0; y < 8; ++y) {
        colr[c][y][0] = (unsigned char)(r ? 0xFF : 0);
        colr[c][y][1] = (unsigned char)(g ? 0xFF : 0);
        colr[c][y][2] = (unsigned char)(b ? 0xFF : 0);
        colr[c][y][3] = (unsigned char)(i ? 0xFF : 0);
    }
}

static void pal16(void)
{
    setcol(C_BLACK, 0,0,0,0); setcol(C_DARK, 0,0,0,1);
    setcol(C_LIGHT, 1,1,1,0); setcol(C_WHITE, 1,1,1,1);
    setcol(C_ACC, 0,1,0,1); setcol(C_ACCDK, 0,1,0,0);
    makeshades();
}

static void palmono(void)
{
    setcol(C_BLACK, 0,0,0,0); setcol(C_DARK, 0,0,0,0);
    setcol(C_LIGHT, 1,1,1,1); setcol(C_WHITE, 1,1,1,1);
    setcol(C_ACC, 0,0,0,0); setcol(C_ACCDK, 0,0,0,0);
    makeshades();
}

/* ---- renderer bounds ---------------------------------------------------- */
#ifdef HOSTMAIN
/* Pixels right of the view (row padding) may only hold the background:
   nothing is drawn outside [0, vw). Returns the first bad row + 1. */
static int clipped(void)
{
    int y, p, x, bg;
    unsigned char bit, *row;
    for (y = 0; y < vh; ++y) {
        bg = y < vcy ? SH_CEIL : SH_FLOOR;
        for (p = 0; p < 4; ++p) {
            row = fb + rowoff[y] + p * rowb;
            for (x = vw; x < rowb * 8; ++x) {
                bit = (unsigned char)(0x80 >> (x & 7));
                if ((row[x >> 3] & bit) != (shade[bg][y & 7][p] & bit))
                    return y + 1;
            }
        }
    }
    return 0;
}

static int renderbounds(void)
{
    static const int sizes[][2] = {
        { 90, 76 }, { 64, 108 }, { 120, 100 }, { 168, 70 }, { 216, 90 },
        { 16, 16 }, { 18, 200 }, { 400, 200 }, { 34, 30 }, { 255, 61 }
    };
    int s, i, w, h, rb, n;
    unsigned char *b;
    for (s = 0; s < (int)(sizeof(sizes) / sizeof(sizes[0])); ++s) {
        w = sizes[s][0]; h = sizes[s][1];
        rb = ((w + 15) / 16) * 2;
        n = rb * 4 * (h + HUDH);
        b = (unsigned char *)malloc((size_t)n);   /* exact: ASan guards */
        CHECK(b != NULL);
        viewsize(w, h, rb, b);
        gscale = w > 160 ? 2 : 1;
        if (s & 1) palmono(); else pal16();
        newgame(99UL + (unsigned long)s);
        for (i = 0; i < 300; ++i) {
            memset(b + rb * 4 * h, 0xA5, (size_t)(rb * 4 * HUDH));
            render();
            for (n = rb * 4 * h; n < rb * 4 * (h + HUDH); ++n)
                CHECK(b[n] == 0xA5);
            CHECK(clipped() == 0);
            hudclear();
            textat(-3, h + 1, "123", SH_FRONT);
            textat(w - 4, h + 1, "WW:WW", SH_FRONT);
            textat(0, h + 3, "TOO LOW", SH_FRONT);
            textat(0, h + 1, "PAUSED - P 0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                   SH_EXITF);
            autopilot();
            if (gev & EV_EXIT) newlevel(level + 1 > 12 ? 1 : level + 1);
            gev = 0;
        }
        free(b);
    }
    return 0;
}
#endif

/* ---- replay: rules and frames, must match host and 8088 ----------------- */
static unsigned char rbuf[28 * 4 * (90 + HUDH)];

static unsigned long replay(int steps)
{
    int i, j, n, pass;
    ck = 0;
    for (pass = 0; pass < 2; ++pass) {
        if (pass == 0) {                /* 16-colour palette, 320 size  */
            pal16();
            viewsize(90, 76, 12, rbuf); gscale = 1;
        } else {                        /* mono dithers, 640 size        */
            palmono();
            viewsize(216, 90, 28, rbuf); gscale = 2;
        }
        newgame(4242UL + (unsigned long)pass);
        for (i = 0; i < steps; ++i) {
            autopilot();
            if (gev & EV_EXIT) newlevel(level + 1 > 12 ? 1 : level + 1);
            gev = 0;
            mixin((unsigned long)(px * 64 + py * 4 + pdir));
            if (i % 4 == 0) {
                render();
                hudclear();
                textat(0, vh + 1, "42", SH_FRONT);
                textat(vw - textw("1:05"), vh + 1, "1:05", SH_FRONT);
                n = rowb * 4 * bh;
                for (j = 0; j < n; ++j) mixin(rbuf[j]);
            }
        }
    }
    return ck;
}

static int tests(int seeds)
{
    int r, lv, s;
    for (lv = 1; lv <= 13; ++lv)
        for (s = 0; s < seeds; ++s) {
            newgame((unsigned long)s * 7919UL + (unsigned long)lv);
            if (lv > 1) newlevel(lv);
            CHECK(ncell == (lv + 3 > MAXN ? MAXN : lv + 3));
            r = checkmaze();
            if (r) return r;
            gev = 0;
            r = walkpar();
            if (r) return r;
        }
    /* the autopilot (screen saver) always finds the exit */
    for (lv = 1; lv <= 13; ++lv)
        for (s = 0; s < seeds; ++s) {
            int n = 0;
            newgame((unsigned long)s * 104729UL + (unsigned long)lv);
            if (lv > 1) newlevel(lv);
            gev = 0;
            while (!(gev & EV_EXIT) && n < 8 * MAXB * MAXB) {
                autopilot();
                ++n;
            }
            CHECK(gev & EV_EXIT);
        }
    r = movement();
    if (r) return r;
#ifdef HOSTMAIN
    r = renderbounds();
    if (r) return r;
#endif
    return 0;
}

#ifdef HOSTMAIN
int main(void)
{
    int r = tests(300);
    printf("%s line=%d replay=%lu\n", r ? "FAIL" : "PASS", r, replay(400));
    return r ? 1 : 0;
}
#else
LONG FAR PASCAL WndProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    return DefWindowProc(w, m, wp, lp);
}
LONG FAR PASCAL SaverProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    return DefWindowProc(w, m, wp, lp);
}
LONG FAR PASCAL QaProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    return DefWindowProc(w, m, wp, lp);
}

int PASCAL WinMain(HANDLE h, HANDLE old, LPSTR cmd, int show)
{
    int r = tests(3);
    HFILE f;
    char s[96];
    wsprintf(s, "%s line=%d replay=%lu\r\nCOMPLETE=1\r\n",
             (LPSTR)(r ? "FAIL" : "PASS"), r, replay(400));
    f = _lcreat("C:\\MAZETEST.LOG", 0);
    if (f != HFILE_ERROR) { _lwrite(f, s, lstrlen(s)); _lclose(f); }
    (void)h; (void)old; (void)cmd; (void)show;
    return r;
}
#endif
