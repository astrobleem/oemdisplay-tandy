/*
 * MAZE.C - Tandy Maze for Windows 3.0 real mode on an 8088.
 *
 * A first-person maze: arrow keys move one square or turn 90 degrees.
 * Each level is a new random maze with an exit in the outer wall; mazes
 * grow from 4x4 to 15x15 cells. A map fills in as you look around.
 * MAZE.EXE /S is the TSHELL screen saver (see SAVER.H): the same view,
 * walking itself with one hand on the wall.
 *
 * Drawing: on the Tandy drivers each GDI call costs about 8 ms and each
 * screen pixel about 35 us on an 8088 (EX/HX class, 16 colours), so the
 * view is composed in a byte buffer (VIEW.H) and drawn with one BitBlt,
 * and only the latest position is drawn when keys arrive faster than
 * frames. Unknown bitmap formats fall back to plain FillRect drawing.
 */
#define WINVER 0x0300
#include <windows.h>
#include <conio.h>
#pragma intrinsic(outp)

static HDC gdc;                         /* GDI fallback target, if set   */
static int gox, goy;                    /* its offset                    */
static void gdirect(int y, int n, int x0, int x1, int sh, int fl);
#define GDIHOOK
#include "GAME.H"
#include "VIEW.H"

/* ---- view bitmap -------------------------------------------------------- */
static HDC vdc;                         /* memory DC holding the view    */
static HBITMAP vbm, vold;
static HGLOBAL vmem;
static unsigned char FAR *vbuf;
static int gdipath;                     /* 1: draw with FillRect         */
static int forcegdi;                    /* /G: always use the fallback   */
static int hasgray, accok;
static COLORREF accrgb;
static HBRUSH gbr[NSHADE];              /* fallback brushes              */
static HBRUSH mapseen, mapacc;          /* map brushes                   */
static HBITMAP checkbits;

static unsigned long brender, bsetbits, bblit, bhud, bmap;

/* Fallback: one FillRect per block of rows, edges as 1-pixel rects. */
static void gdirect(int y, int n, int x0, int x1, int sh, int fl)
{
    RECT r;
    SetRect(&r, gox + x0, goy + y, gox + x1, goy + y + n);
    FillRect(gdc, &r, gbr[sh]);
    if (fl & SP_L) {
        SetRect(&r, gox + x0, goy + y, gox + x0 + 1, goy + y + n);
        FillRect(gdc, &r, GetStockObject(BLACK_BRUSH));
    }
    if (fl & SP_R) {
        SetRect(&r, gox + x1 - 1, goy + y, gox + x1, goy + y + n);
        FillRect(gdc, &r, GetStockObject(BLACK_BRUSH));
    }
}

/* Read back what a solid brush looks like in a compatible bitmap, so the
   buffer uses this driver's own colour bits. Returns 0 on any failure. */
static int sample(HDC d, COLORREF c, int idx)
{
    HDC m;
    HBITMAP b, o;
    HBRUSH br;
    BITMAP bi;
    RECT r;
    unsigned char bits[64];
    int y, p, ok = 0;

    m = CreateCompatibleDC(d);
    if (!m) return 0;
    b = CreateCompatibleBitmap(d, 16, 8);
    if (b) {
        o = SelectObject(m, b);
        br = CreateSolidBrush(c);
        if (o && br) {
            SetRect(&r, 0, 0, 16, 8);
            FillRect(m, &r, br);
            GetObject(b, sizeof(bi), (LPSTR)&bi);
            if (bi.bmPlanes == 4 && bi.bmBitsPixel == 1 &&
                bi.bmWidthBytes == 2 &&
                GetBitmapBits(b, 64L, (LPSTR)bits) == 64L) {
                for (y = 0; y < 8; ++y)
                    for (p = 0; p < 4; ++p)
                        colr[idx][y][p] = bits[(y * 4 + p) * 2];
                ok = 1;
            }
        }
        if (br) DeleteObject(br);
        if (o) SelectObject(m, o);
        DeleteObject(b);
    }
    DeleteDC(m);
    return ok;
}

static void freebrushes(void)
{
    int i;
    for (i = 0; i < NSHADE; ++i)
        if (gbr[i]) { DeleteObject(gbr[i]); gbr[i] = NULL; }
    if (mapseen) { DeleteObject(mapseen); mapseen = NULL; }
    if (mapacc) { DeleteObject(mapacc); mapacc = NULL; }
    if (checkbits) { DeleteObject(checkbits); checkbits = NULL; }
}

static void viewfree(void)
{
    if (vdc) {
        if (vold) SelectObject(vdc, vold);
        DeleteDC(vdc);
    }
    if (vbm) DeleteObject(vbm);
    if (vbuf) GlobalUnlock(vmem);
    if (vmem) GlobalFree(vmem);
    vdc = NULL; vbm = vold = NULL; vmem = NULL; vbuf = NULL;
    freebrushes();
    gdc = NULL;
}

static void makebrushes(void)
{
    static const COLORREF fr[5] = {
        RGB(255,255,255), RGB(192,192,192), RGB(160,160,160),
        RGB(128,128,128), RGB(80,80,80) };
    static const COLORREF si[6] = {
        RGB(192,192,192), RGB(160,160,160), RGB(128,128,128),
        RGB(96,96,96), RGB(80,80,80), RGB(64,64,64) };
    static unsigned short check[8] = {
        0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55 };
    int i;
    for (i = 0; i < 5; ++i) gbr[SH_FRONT + i] = CreateSolidBrush(fr[i]);
    for (i = 0; i < 6; ++i) gbr[SH_SIDE + i] = CreateSolidBrush(si[i]);
    gbr[SH_CEIL] = CreateSolidBrush(RGB(0, 0, 0));
    gbr[SH_EDGE] = CreateSolidBrush(RGB(0, 0, 0));
    gbr[SH_FLOOR] = CreateSolidBrush(RGB(64, 64, 64));
    gbr[SH_MARK] = CreateSolidBrush(RGB(192, 192, 192));
    gbr[SH_EXITF] = CreateSolidBrush(accok ? accrgb : RGB(255, 255, 255));
    gbr[SH_EXITS] = CreateSolidBrush(accok ? accrgb : RGB(192, 192, 192));
    /* map: seen squares in gray, or a checker where there is no gray */
    if (hasgray) mapseen = CreateSolidBrush(RGB(128, 128, 128));
    else {
        checkbits = CreateBitmap(8, 8, 1, 1, (LPSTR)check);
        if (checkbits) mapseen = CreatePatternBrush(checkbits);
    }
    mapacc = CreateSolidBrush(accok ? accrgb : RGB(0, 0, 0));
}

/* Fallback path: first accent colour the device shows as a colour. */
static void nearacc(HDC d, const COLORREF *acc)
{
    COLORREF black = GetNearestColor(d, RGB(0, 0, 0));
    COLORREF white = GetNearestColor(d, RGB(255, 255, 255));
    COLORREF n;
    int i;
    for (i = 0; i < 5; ++i) {
        n = GetNearestColor(d, acc[i]);
        if (n != black && n != white) { accok = 1; accrgb = acc[i]; return; }
    }
}

/* Set up the view for a w x h area. Returns 1; gdipath tells the path. */
static int viewinit(HDC d, int w, int h)
{
    static const COLORREF acc[5] = {
        RGB(0,255,0), RGB(0,255,255), RGB(255,0,255), RGB(255,0,0),
        RGB(0,0,255) };
    BITMAP bi;
    int i, y, p, ok;

    viewfree();
    gdipath = 1;
    hasgray = accok = 0;
    vw = w; vh = h;
    ok = !forcegdi &&
         sample(d, RGB(0, 0, 0), C_BLACK) &&
         sample(d, RGB(64, 64, 64), C_DARK) &&
         sample(d, RGB(128, 128, 128), C_LIGHT) &&
         sample(d, RGB(255, 255, 255), C_WHITE);
    if (ok) {
        /* first accent colour that is neither black nor white */
        for (i = 0; i < 5; ++i) {
            if (!sample(d, acc[i], C_ACC)) { ok = 0; break; }
            if (!samecol(C_ACC, C_BLACK) && !samecol(C_ACC, C_WHITE)) {
                accok = 1; accrgb = acc[i];
                sample(d, RGB(GetRValue(acc[i]) / 2, GetGValue(acc[i]) / 2,
                              GetBValue(acc[i]) / 2), C_ACCDK);
                break;
            }
        }
        if (!accok) {
            for (y = 0; y < 8; ++y)
                for (p = 0; p < 4; ++p) colr[C_ACCDK][y][p] = colr[C_ACC][y][p];
        }
        /* edges are cleared bits: black must be all zero */
        for (y = 0; y < 8 && ok; ++y)
            for (p = 0; p < 4; ++p)
                if (colr[C_BLACK][y][p]) ok = 0;
    }
    gscale = GetDeviceCaps(d, HORZRES) >= 640 ? 2 : 1;
    vdc = CreateCompatibleDC(d);
    if (vdc) vbm = CreateCompatibleBitmap(d, w, h + HUDH);
    if (vbm) vold = SelectObject(vdc, vbm);
    if (!vold) {                        /* no memory bitmap: draw direct */
        if (vdc) DeleteDC(vdc);
        if (vbm) DeleteObject(vbm);
        vdc = NULL; vbm = NULL; vold = NULL;
        ok = 0;
    }
    if (ok) {
        GetObject(vbm, sizeof(bi), (LPSTR)&bi);
        if (bi.bmPlanes != 4 || bi.bmBitsPixel != 1 || (bi.bmWidthBytes & 1) ||
            bi.bmWidthBytes * 8 < w) ok = 0;
    }
    if (ok) {
        vmem = GlobalAlloc(GMEM_MOVEABLE,
                           (DWORD)bi.bmWidthBytes * 4 * (h + HUDH));
        if (vmem) vbuf = (unsigned char FAR *)GlobalLock(vmem);
        if (!vbuf) ok = 0;
    }
    if (ok) {
        viewsize(w, h, bi.bmWidthBytes, vbuf);
        hasgray = makeshades();
        gdipath = 0;
    } else {
        /* keep the geometry, draw through GDI */
        if (vbuf) GlobalUnlock(vmem);
        if (vmem) GlobalFree(vmem);
        vbuf = NULL; vmem = NULL;
        viewsize(w, h, 0, NULL);
        hasgray = GetDeviceCaps(d, NUMCOLORS) >= 16;
        nearacc(d, acc);
    }
    makebrushes();
    return 1;
}

/* Compose the view (render) and put it on screen at (x,y). */
static void hudfill(void);

/* Compose the view and its status line in the bitmap. */
static void viewrender(void)
{
    if (!gdipath) {
        DWORD t = GetTickCount();
        render();
        hudfill();
        brender += GetTickCount() - t; t = GetTickCount();
        SetBitmapBits(vbm, (DWORD)rowb * 4 * bh, (LPSTR)vbuf);
        bsetbits += GetTickCount() - t;
    } else if (vdc) {
        gdc = vdc; gox = goy = 0;
        render();
        gdc = NULL;
    }
}

static void viewblank(void)             /* all black, for messages      */
{
    if (!gdipath) bgrows(0, vh, SH_CEIL);
    else if (vdc) PatBlt(vdc, 0, 0, vw, vh, BLACKNESS);
}

/* Put the view (and, on the fast path, its status line) on screen. */
static void viewshow(HDC d, int x, int y)
{
    DWORD t = GetTickCount();
    if (vdc) {
        BitBlt(d, x, y, vw, gdipath ? vh : bh, vdc, 0, 0, SRCCOPY);
        bblit += GetTickCount() - t;
    } else {
        gdc = d; gox = x; goy = y;
        render();
        gdc = NULL;
    }
}

#include "SOUND.H"

/* ---- game window ----------------------------------------------------- */
#define ST_PLAY 0
#define ST_DONE 1
static HWND mainw;
static int state, paused, mapon = 1;
static int demo, dpace;                 /* D: the computer walks         */
static int saverhud;                    /* /S: title and level only      */
static int cw, ch, cx, cy;              /* client size, character size   */
static int vx, vy;                      /* view position                 */
static int sidep, px0, pw;              /* side panel                    */
static int mx0, my0, mw, mh, mapfit;    /* map origin and cell size      */
static int hudy;
static DWORD played, lastt;             /* ms played this level          */
static int shownsec = -1, shownmoves = -1, showndir = -1;
static int drawn = 1;                   /* last action is on screen      */
static int needview, needhud, needpanel, needmap;
static int hres, vres, ncolors;
static int bench;                       /* /T: timed autopilot run       */
static unsigned long bframes, bviewms, bmaxms, ballms;
static DWORD bstart;

static void text(HDC d, int x, int y, LPSTR s)
{
    TextOut(d, x, y, s, lstrlen(s));
}

/* Height whose square-celled view (width = height * 3*hres / 4*vres)
   has about the pixel budget for this colour depth. */
static int viewheight(int colours, int hr, int vr)
{
    long budget = colours >= 16 ? 7000L : colours >= 4 ? 12000L : 20000L;
    int h = 16;
    while (h < 200 && (long)(h + 2) * (h + 2) * 3 * hr / (4L * vr) <= budget)
        h += 2;
    return h;
}

static void layout(HDC d)
{
    TEXTMETRIC tm;
    int want, h, w;
    long t;

    GetTextMetrics(d, &tm);
    cx = tm.tmAveCharWidth; cy = tm.tmHeight;
    hres = GetDeviceCaps(d, HORZRES); vres = GetDeviceCaps(d, VERTRES);
    ncolors = GetDeviceCaps(d, NUMCOLORS);
    /* View size by pixel budget: on an 8088 these drivers take about
       45 us per 16-colour pixel and 5 us per mono pixel to draw. */
    want = viewheight(ncolors, hres, vres);
    h = ch - cy - 8;
    if (h > want) h = want;
    if (h < 16) h = 16;
    h &= ~1;
    /* square cells on a 4:3 monitor: width follows height */
    t = (long)h * 3 * hres / (4L * vres);
    w = (int)t & ~1;
    if (w > cw - 8) w = (cw - 8) & ~1;
    if (w < 16) w = 16;
    /* Blits aligned to 16 screen pixels are much cheaper on these
       drivers; the client area starts after the window border. */
    {
        POINT o;
        o.x = o.y = 0;
        ClientToScreen(mainw, &o);
        vx = 16 - (o.x & 15); vy = 4;
        if (vx + w > cw) vx = (16 - (o.x & 15)) & 15;
        sidep = cw - (vx + w + 8) >= 11 * cx;
        if (!sidep) vx = (((o.x + (cw - w) / 2) & ~15) - o.x);
        while (vx < 0) vx += 16;
    }
    hudy = vy + h + 2;
    px0 = vx + w + 8;
    pw = cw - px0 - 4;
    viewinit(d, w, h);
}

/* Map cells: square on the monitor, as big as fits (at most 4 rows). */
static void maplayout(void)
{
    int top = vy + 4 * cy + 4, bottom = ch - 5 * cy - 4, avail, aw;
    mapfit = 0;
    if (!sidep || !mapon) return;
    avail = bottom - top;
    for (mh = 4; mh >= 1; --mh) {
        mw = (int)((long)mh * 3 * hres / (4L * vres));
        if (mw < 1) mw = 1;
        aw = msize * mw;
        if (aw <= pw && msize * mh <= avail) break;
    }
    if (mh < 1) return;
    mapfit = 1;
    mx0 = px0 + (pw - msize * mw) / 2;
    if (mx0 < px0) mx0 = px0;
    my0 = top;
}

static void mapcell(HDC d, int x, int y)
{
    RECT r;
    HBRUSH b;
    if (!mapfit) return;
    SetRect(&r, mx0 + x * mw, my0 + y * mh,
            mx0 + x * mw + mw, my0 + y * mh + mh);
    if (x == px && y == py && state == ST_PLAY) b = mapacc;
    else if (grid[y][x] == B_EXIT && seen[y][x]) b = mapacc;
    else if (grid[y][x] != B_OPEN || !seen[y][x])
        b = GetStockObject(BLACK_BRUSH);
    else if (seen[y][x] == 1) b = GetStockObject(WHITE_BRUSH);
    else b = mapseen;
    FillRect(d, &r, b);
}

static void mapall(HDC d)
{
    int x, y;
    RECT r;
    if (!mapfit) return;
    SetRect(&r, mx0, my0, mx0 + msize * mw, my0 + msize * mh);
    FillRect(d, &r, GetStockObject(BLACK_BRUSH));
    for (y = 0; y < msize; ++y)
        for (x = 0; x < msize; ++x)
            if (seen[y][x] || (x == px && y == py)) mapcell(d, x, y);
}

/* A thin frame around the view and its status line. */
static void frame(HDC d)
{
    RECT r;
    int x0 = vx - 2, y0 = vy - 2, x1 = vx + vw + 1, y1 = vy + vh + HUDH + 1;
    HBRUSH b = gbr[SH_FRONT + 1];
    if (x0 < 0 || y0 < 0 || !b) return;
    SetRect(&r, x0, y0, x1 + 1, y0 + 1); FillRect(d, &r, b);
    SetRect(&r, x0, y1, x1 + 1, y1 + 1); FillRect(d, &r, b);
    SetRect(&r, x0, y0, x0 + 1, y1); FillRect(d, &r, b);
    SetRect(&r, x1, y0, x1 + 1, y1); FillRect(d, &r, b);
}

static void panel(HDC d)
{
    char s[40];
    RECT r;
    frame(d);
    if (!sidep) {                       /* narrow screens: help below    */
        int y = vy + vh + HUDH + 4;
        if (y + 4 * cy > ch) return;
        text(d, (cw - 11 * cx) / 2, y, "ARROWS WALK");
        text(d, (cw - 11 * cx) / 2, y + cy, "N NEW");
        text(d, (cw - 11 * cx) / 2, y + 2 * cy, "D DEMO");
        text(d, (cw - 11 * cx) / 2, y + 3 * cy, "P PAUSE");
        return;
    }
    SetRect(&r, px0, 0, cw, ch);
    FillRect(d, &r, GetStockObject(BLACK_BRUSH));
    text(d, px0, vy, "TANDY MAZE");
    wsprintf(s, "LEVEL %d", level);
    text(d, px0, vy + cy + 2, s);
    wsprintf(s, "PAR %d", par);
    text(d, px0, vy + 2 * cy + 2, s);
    if (!mapon) text(d, px0, vy + 4 * cy + 4, "MAP OFF");
    text(d, px0, ch - 5 * cy - 2, "ARROWS WALK");
    text(d, px0, ch - 4 * cy - 2, "M MAP N NEW");
    text(d, px0, ch - 3 * cy - 2, "D DEMO");
    text(d, px0, ch - 2 * cy - 2, soundok ? "P PAUSE S SND" : "P PAUSE");
    maplayout();
    mapall(d);
}

static int seconds(void)
{
    return (int)(played / 1000UL);
}

/* Status line text: moves, facing, time (or a message). */
static void hudtext(char *l, char *c, char *rt)
{
    static const char dirs[] = "NESW";
    int sec = seconds();
    l[0] = c[0] = rt[0] = 0;
    if (saverhud) wsprintf(c, "LEVEL %d", level);
    else if (paused) lstrcpy(l, "PAUSED - P");
    else if (state == ST_DONE) lstrcpy(l, demo ? "DEMO" : "ENTER: NEXT");
    else {
        wsprintf(l, "%d", moves);
        if (demo) lstrcpy(c, "DEMO");
        else { c[0] = dirs[pdir]; c[1] = 0; }
        wsprintf(rt, "%d:%02d", sec / 60, sec % 60);
    }
    shownsec = sec; shownmoves = moves; showndir = pdir;
}

/* Fast path: status line into the buffer (no GDI). */
static void hudfill(void)
{
    char l[16], c[16], rt[12];
    int y = vh + 1;
    hudtext(l, c, rt);
    hudclear();
    textat(0, y, l, SH_FRONT);
    /* the middle field only when it clears both sides (160 is narrow) */
    if (textw(l) + textw(c) + textw(rt) + 4 * 6 * gscale <= vw)
        textat((vw - textw(c)) / 2, y, c, SH_FRONT);
    textat(vw - textw(rt), y, rt, SH_FRONT);
}

static void hud(HDC d)
{
    char l[16], c[16], rt[12];
    RECT r;
    if (!gdipath) {
        DWORD t = GetTickCount();
        hudfill();
        SetBitmapBits(vbm, (DWORD)rowb * 4 * bh, (LPSTR)vbuf);
        BitBlt(d, vx, vy + vh, vw, HUDH, vdc, 0, vh, SRCCOPY);
        bblit += GetTickCount() - t;
        return;
    }
    hudtext(l, c, rt);
    SetRect(&r, vx, hudy, vx + vw, hudy + cy);
    FillRect(d, &r, GetStockObject(BLACK_BRUSH));
    text(d, vx, hudy, l);
    text(d, vx + (vw - lstrlen(c) * cx) / 2, hudy, c);
    text(d, vx + vw - lstrlen(rt) * cx, hudy, rt);
}

/* Level complete: a black view with the results. */
static void donescreen(void)
{
    char s[6][16];
    int i, y, sec = seconds(), n = 0;
    wsprintf(s[n++], "LEVEL %d", level);
    lstrcpy(s[n++], "COMPLETE!");
    wsprintf(s[n++], "MOVES %d", moves);
    wsprintf(s[n++], "PAR %d", par);
    wsprintf(s[n++], "TIME %d:%02d", sec / 60, sec % 60);
    if (moves <= par) lstrcpy(s[n++], "PERFECT");
    viewblank();
    if (!gdipath) {
        y = (vh - n * 9) / 2;
        if (y < 0) y = 0;
        for (i = 0; i < n; ++i, y += 9)
            textat((vw - textw(s[i])) / 2, y, s[i],
                   (i == 1 || i == 5) && accok ? SH_EXITF : SH_FRONT);
        hudfill();
        SetBitmapBits(vbm, (DWORD)rowb * 4 * bh, (LPSTR)vbuf);
        return;
    }
    if (!vdc) return;
    SetBkMode(vdc, TRANSPARENT);
    SetTextColor(vdc, RGB(255, 255, 255));
    SelectObject(vdc, GetStockObject(SYSTEM_FIXED_FONT));
    y = (vh - n * cy) / 2;
    if (y < 0) y = 0;
    for (i = 0; i < n; ++i, y += cy)
        text(vdc, (vw - lstrlen(s[i]) * cx) / 2, y, s[i]);
}

static void prep(HDC d)
{
    SelectObject(d, GetStockObject(SYSTEM_FIXED_FONT));
    SetBkColor(d, RGB(0, 0, 0));
    SetTextColor(d, RGB(255, 255, 255));
}

/* Bring the screen up to date, most visible first. */
static void update(void)
{
    HDC d;
    int i;
    if (IsIconic(mainw) || !cw) return;
    d = GetDC(mainw);
    if (!d) { InvalidateRect(mainw, NULL, FALSE); return; }
    prep(d);
    if (needview) {
        DWORD t0 = GetTickCount(), dt;
        if (state == ST_DONE) donescreen(); else viewrender();
        viewshow(d, vx, vy);
        needview = 0;
        drawn = 1;
        dt = GetTickCount() - t0;
        bviewms += dt;
        if (dt > bmaxms) bmaxms = dt;
    }
    soundtick();                        /* end notes the draw outlasted  */
    if (needpanel) {
        panel(d);
        needpanel = needmap = 0;
        nnew = 0; newfull = 0;
    }
    if (needmap) {
        DWORD t = GetTickCount();
        if (newfull) mapall(d);
        else for (i = 0; i < nnew; ++i) mapcell(d, newx[i], newy[i]);
        mapcell(d, px, py);
        nnew = 0; newfull = 0; needmap = 0;
        bmap += GetTickCount() - t;
    }
    if (needhud || moves != shownmoves || pdir != showndir ||
        seconds() != shownsec) {
        DWORD t = GetTickCount();
        hud(d); needhud = 0;
        bhud += GetTickCount() - t;
    }
    ReleaseDC(mainw, d);
    sounds_now();                       /* sound starts with the picture */
}

static void clockrun(int on)
{
    DWORD t = GetTickCount();
    if (lastt && !on) played += t - lastt;
    lastt = on ? t : 0;
}

static int seconds_due(void);
static void benchtick(HWND w);

static int running(void)
{
    return state == ST_PLAY && !paused && !IsIconic(mainw);
}

static void startlevel(int lv)
{
    clockrun(0);
    played = 0;
    newlevel(lv);
    state = ST_PLAY;
    gev = 0;
    needview = needpanel = needhud = 1;
    sfx(SFX_LEVEL);
    if (running()) clockrun(1);
}

static void pause(int on)
{
    clockrun(0);
    paused = on;
    soundstop();
    if (running()) clockrun(1);
    needhud = 1;
}

/* Handle what the last action did; drawing waits until no keys are
   queued. */
static void afterev(void)
{
    unsigned e = gev;
    gev = 0;
    if (e & EV_EXIT) {
        clockrun(0);
        state = ST_DONE;
        sfx(SFX_EXIT);
        needview = needhud = needmap = 1;
        return;
    }
    if (e & EV_BUMP) sfx(SFX_BUMP);
    if (e & EV_STEP) sfx(SFX_STEP);
    if (e & EV_TURN) sfx(SFX_TURN);
    if (e & (EV_STEP | EV_TURN)) { needview = needmap = 1; drawn = 0; }
}

static void doact(int a)
{
    act(a);
    afterev();
}

static void setdemo(int on)
{
    demo = on;
    dpace = 0;
    needhud = 1;
}

static int keysqueued(void)
{
    MSG m;
    return PeekMessage(&m, NULL, WM_KEYDOWN, WM_KEYDOWN, PM_NOREMOVE);
}

LONG FAR PASCAL WndProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    PAINTSTRUCT ps;
    HDC d;
    int rep;

    switch (m) {
    case WM_CREATE:
        mainw = w;
        soundinit();
        newgame(bench ? 12345UL : GetTickCount() ^ 0x5A17UL);
        startlevel(1);
        if (!SetTimer(w, 1, 55, NULL)) return -1L;
        return 0;

    case WM_SIZE:
        cw = LOWORD(lp); ch = HIWORD(lp);
        if (!cw || !ch) return 0;
        d = GetDC(w);
        if (!d) return 0;
        prep(d);
        layout(d);
        ReleaseDC(w, d);
        needview = needpanel = needhud = 1;
        InvalidateRect(w, NULL, TRUE);
        return 0;

    case WM_PAINT:
        BeginPaint(w, &ps);
        EndPaint(w, &ps);
        needview = needpanel = needhud = 1;
        update();
        return 0;

    case WM_SETCURSOR:
        if (LOWORD(lp) == HTCLIENT) { SetCursor(NULL); return 1L; }
        break;

    case WM_KEYDOWN:
        rep = (lp & 0x40000000L) != 0;
        if (wp == 'P' && !rep && state == ST_PLAY) {
            pause(!paused);
            update();
            return 0;
        }
        if (paused) return 0;
        if (state == ST_DONE) {
            if (demo && !rep) setdemo(0);
            if ((wp == VK_RETURN || wp == VK_SPACE) && !rep) {
                startlevel(level + 1);
                update();
            }
            return 0;
        }
        if (wp == 'D' && !rep) { setdemo(!demo); update(); return 0; }
        if (demo) setdemo(0);           /* any other key takes over      */
        /* a held key walks one square per frame shown */
        if (rep && !drawn) return 0;
        if (wp == VK_UP) doact(A_FWD);
        else if (wp == VK_DOWN) doact(A_BACK);
        else if (wp == VK_LEFT) doact(A_LEFT);
        else if (wp == VK_RIGHT) doact(A_RIGHT);
        else if (wp == 'M' && !rep) {
            mapon = !mapon; needpanel = 1;
        } else if (wp == 'N' && !rep) {
            startlevel(level);
        } else if (wp == 'S' && !rep && soundok) {
            soundstop(); sound = !sound;
        } else return 0;
        if (!keysqueued()) update();
        return 0;

    case WM_TIMER:
        soundtick();
        if (bench) { benchtick(w); return 0; }
        if (demo && !paused && drawn && !IsIconic(w)) {
            if (running()) seconds_due();   /* keep the clock going      */
            /* a step every few ticks; a finished level waits ~2 s */
            if (state == ST_DONE) {
                if (++dpace >= 36) {
                    dpace = 0;
                    startlevel(level + 1);
                    update();
                }
            } else if (++dpace >= 3) {
                dpace = 0;
                autopilot();
                afterev();
                update();
            }
            return 0;
        }
        if (running() && seconds_due()) update();
        return 0;

    case WM_KILLFOCUS:
        if (state == ST_PLAY && !paused) { pause(1); update(); }
        return 0;

    case WM_DESTROY:
        KillTimer(w, 1);
        soundclose();
        viewfree();
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(w, m, wp, lp);
}

/* True when the clock display would change. */
static int seconds_due(void)
{
    DWORD t = GetTickCount();
    if (lastt) { played += t - lastt; lastt = t; }
    return seconds() != shownsec;
}

/* /T and /F: walk 40 squares by autopilot through the normal drawing
   path, then log the timing to MAZE.LOG beside the executable. */
static char blog[144];

static void benchtick(HWND w)
{
    char s[200];
    HFILE f;
    DWORD t0;
    if (!drawn || IsIconic(w)) return;
    if (!bstart) bstart = GetTickCount();
    if (bframes == 40) {
        wsprintf(s, "BENCH frames=%lu elapsed_ms=%lu view_ms=%lu "
                 "max_view_ms=%lu update_ms=%lu gdi=%d view=%dx%d "
                 "colors=%d level=%d\r\nrender=%lu setbits=%lu blit=%lu "
                 "hud=%lu map=%lu\r\nCOMPLETE=1\r\n",
                 bframes, GetTickCount() - bstart, bviewms, bmaxms, ballms,
                 gdipath, vw, vh, ncolors, level, brender, bsetbits, bblit,
                 bhud, bmap);
        f = _lcreat(blog, 0);
        if (f != HFILE_ERROR) { _lwrite(f, s, lstrlen(s)); _lclose(f); }
        ++bframes;
        DestroyWindow(w);
        return;
    }
    if (bframes > 40) return;
    t0 = GetTickCount();
    if (state == ST_DONE) startlevel(level + 1);
    autopilot();
    {
        unsigned e = gev; gev = 0;
        if (e & EV_EXIT) { state = ST_DONE; }
        needview = needmap = 1;
        drawn = 0;
    }
    update();
    ballms += GetTickCount() - t0;
    ++bframes;
}

#include "SAVER.H"

int PASCAL WinMain(HANDLE inst, HANDLE prev, LPSTR cmd, int show)
{
    WNDCLASS wc;
    HWND w;
    MSG msg;

    char c = (char)(cmd[0] == '/' ? cmd[1] : 0);
    int i, n;

    if (c == 'S' || c == 's' || c == 'A' || c == 'a' || c == 'B' ||
        c == 'b' || c == 'I' || c == 'i')
        return SaverMain(inst, prev, cmd, show);
    forcegdi = c == 'G' || c == 'g' || c == 'F' || c == 'f';
    bench = c == 'T' || c == 't' || c == 'F' || c == 'f' ||
            c == 'C' || c == 'c';
    if (bench) {
        GetModuleFileName(inst, blog, sizeof(blog));
        n = lstrlen(blog);
        for (i = n - 1; i >= 0 && blog[i] != '\\' && blog[i] != ':'; i--) ;
        blog[i + 1] = 0;
        lstrcat(blog, "MAZE.LOG");
    }
    if (FindWindow("TandyMazeSaver", NULL)) return 8;
    if (prev) {                         /* one game at a time            */
        w = FindWindow("TandyMaze", NULL);
        if (w) { BringWindowToTop(w); return 0; }
    } else {
        wc.style = 0;
        wc.lpfnWndProc = WndProc;
        wc.cbClsExtra = wc.cbWndExtra = 0;
        wc.hInstance = inst;
        wc.hIcon = NULL;
        wc.hCursor = NULL;
        wc.hbrBackground = GetStockObject(BLACK_BRUSH);
        wc.lpszMenuName = NULL;
        wc.lpszClassName = "TandyMaze";
        if (!RegisterClass(&wc)) return 1;
    }
    w = CreateWindow("TandyMaze", "Maze",
                     WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
                     0, 0, GetSystemMetrics(SM_CXSCREEN),
                     GetSystemMetrics(SM_CYSCREEN), NULL, NULL, inst, NULL);
    if (!w) return 2;
    ShowWindow(w, show);
    UpdateWindow(w);
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return (int)msg.wParam;
}
