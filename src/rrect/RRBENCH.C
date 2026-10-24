/* RRBENCH.C - RoundRect/Rectangle timing and raster probe (MIT).
 * Windows 3.0 real mode, small model, /G0. Draws on the screen DC with the
 * cursor hidden, times each batch with GetTickCount (about 55 ms), dumps the
 * 32 KB B800h frame buffer after each batch (C:\RBnn.BIN) and, when the
 * driver is a test-only RRTRACE build, saves its Output call table
 * (C:\TRnn.BIN, 20-byte records, see src/rrect/RRPATCH.PY). The last stage
 * stages start CALC.EXE, REVERSI.EXE and PBRUSH.EXE in turn, time three full
 * client repaints each (InvalidateRect + UpdateWindow), dump, and close them.
 * The cursor_overlap stage draws Calculator-sized keys with the arrow cursor
 * visible over them, then moves it to the bottom-right corner before the
 * dump, so cursor save/restore is part of the compared frame.
 * The visible_steps stage (version 4) draws 14 mixed shapes with the arrow
 * cursor shown over the first ones and saves the frame after every single
 * call (C:\RVnn.BIN), so rows a driver holds back or copies early show up
 * between calls, not only in the final frame. It covers pen and no-pen
 * fills, XOR, hollow, clipped, partly and fully off-screen shapes.
 * Log: C:\RRBENCH.LOG, one KEY=value per line.
 * If C:\RRECT\RRSHOTS.ON exists (screenshot runs only), only the application
 * stages run; each logs REPAINT_START before its first timed repaint and
 * HOLD after its dump, then keeps its window up for 30 s so that the host
 * runner can take 86Box screenshots. Timings from such runs are not used.
 * Command line: an optional batch count multiplier digit (default 1).
 */
#define WINVER 0x0300
#include <windows.h>

static HFILE logFile;
static HDC dc;
static int width, height, seq = 0, mult = 1, shots = 0;
static HPEN blackPen, nullPen;
static HBRUSH white, gray, hollow, ltgray;
static HWND lastApp = NULL;
static char trbuf[4 + 64 * 20];
static int xr = 0, panx = 0, pany = 0, hardware = 0;
static void line(char *key, long value);

static void cursorpos(int x, int y) { SetCursorPos(x + panx, y + pany); }

static void setpan(void)
{
    int in[2], out[6], enabled = 1;
    if (hardware) Escape(dc, 0x5861, 2, (LPSTR)&enabled, NULL);
    in[0] = panx; in[1] = pany;
    line("PAN_RESULT", Escape(dc, 0x5860, 4, (LPSTR)in, (LPSTR)out));
    line("PAN_X", out[0]); line("PAN_Y", out[1]);
}

static void putnum(char *b, int *n, long v)
{
    char d[12];
    int k = 0;
    if (v < 0) { b[(*n)++] = '-'; v = -v; }
    do { d[k++] = (char)('0' + v % 10); v /= 10; } while (v);
    while (k) b[(*n)++] = d[--k];
}

static void line(char *key, long value)
{
    char b[100];
    int n = 0;
    while (*key) b[n++] = *key++;
    b[n++] = '=';
    putnum(b, &n, value);
    b[n++] = '\r';
    b[n++] = '\n';
    _lwrite(logFile, b, n);
}

static void flush(void)
{
    _lclose(logFile);
    logFile = _lopen("C:\\RRBENCH.LOG", OF_WRITE);
    _llseek(logFile, 0L, 2);
}

static void numname(char *name, int at, int v)
{
    name[at] = (char)('0' + v / 10);
    name[at + 1] = (char)('0' + v % 10);
}

static void dump(void)
{
    HFILE h;
    char n[] = "C:\\RB00.BIN";
    numname(n, 5, seq);
    h = _lcreat(n, 0);
    line("DUMP_CREATED", h != HFILE_ERROR);
    if (h != HFILE_ERROR) {
        line("DUMP_BYTES", _lwrite(h, (LPSTR)0xb8000000L, 0x8000U));
        _lclose(h);
    }
}

/* Save the RRTRACE table (if the driver has one) to C:\TRnn.BIN. */
static void savetrace(void)
{
    HFILE h = HFILE_ERROR;
    char n[] = "C:\\TR00.BIN";
    int start = 0, got, total = -1, lost = 0;
    numname(n, 5, seq);
    for (;;) {
        got = Escape(dc, 0x7F01, 2, (LPSTR)&start, (LPSTR)trbuf);
        if (got <= 0) break;
        total = *(int *)trbuf;
        lost = *(int *)(trbuf + 2);
        if (h == HFILE_ERROR) h = _lcreat(n, 0);
        if (got == 1) break;
        _lwrite(h, (LPSTR)(trbuf + 4), (got - 1) * 20);
        start += got - 1;
    }
    if (h != HFILE_ERROR) _lclose(h);
    line("TRACE_RECORDS", total);
    line("TRACE_LOST", lost);
}

static void resettrace(void)
{
    int z = 0;
    Escape(dc, 0x7F02, 2, (LPSTR)&z, (LPSTR)trbuf);
}

static void clear(void)
{
    RECT r;
    r.left = 0; r.top = 0; r.right = width; r.bottom = height;
    line("CLEAR_SUCCESS", FillRect(dc, &r, white) != 0);
}

/* kind: 1 RoundRect, 2 Rectangle, 3 Ellipse. */
static void batch(char *name, int kind, int w, int h, int ew, int eh, HPEN pen, HBRUSH brush,
                  int rop2, int count, int dx, int dy, int clip)
{
    DWORD t0, t1;
    int i, ok = 0, x, y, cols;
    HPEN op;
    HBRUSH ob;
    HRGN rgn = NULL;
    seq++;
    clear();
    op = SelectObject(dc, pen);
    ob = SelectObject(dc, brush);
    SetROP2(dc, rop2);
    if (clip) {
        rgn = CreateRectRgn(40 + panx, 30 + pany, width - 40 + panx, height - 30 + pany);
        SelectClipRgn(dc, rgn);
    }
    line("STAGE", seq);
    _lwrite(logFile, "NAME=", 5);
    _lwrite(logFile, name, lstrlen(name));
    _lwrite(logFile, "\r\n", 2);
    line("KIND", kind);
    line("W", w); line("H", h); line("EW", ew); line("EH", eh);
    line("ROP2", rop2); line("COUNT", count * mult); line("CLIPPED", clip);
    flush();
    resettrace();
    cols = dx > 0 ? (width - w) / dx : 1;
    if (cols < 1) cols = 1;
    t0 = GetTickCount();
    for (i = 0; i < count * mult; i++) {
        int j = i % count;
        x = 4 + (j % cols) * dx;
        y = 4 + (j / cols) * dy;
        if (kind == 1) ok += RoundRect(dc, x, y, x + w, y + h, ew, eh) != 0;
        else if (kind == 2) ok += Rectangle(dc, x, y, x + w, y + h) != 0;
        else ok += Ellipse(dc, x, y, x + w, y + h) != 0;
    }
    t1 = GetTickCount();
    if (clip) {
        SelectClipRgn(dc, NULL);
        DeleteObject(rgn);
    }
    SetROP2(dc, R2_COPYPEN);
    SelectObject(dc, op);
    SelectObject(dc, ob);
    line("ELAPSED_MS", (long)(t1 - t0));
    line("API_SUCCESSES", ok);
    savetrace();
    dump();
    flush();
}

static void pump(int n)
{
    MSG m;
    while (n-- > 0)
        if (PeekMessage(&m, NULL, 0, 0, PM_REMOVE)) {
            TranslateMessage(&m);
            DispatchMessage(&m);
        }
}

/* Screenshot runs: keep the current screen up for 30 s. */
static void hold(void)
{
    DWORD t = GetTickCount();
    line("HOLD", seq);
    flush();
    while (GetTickCount() - t < 30000L) pump(10);
}

/* Start an application, wait for its window to become active, time three
 * full client repaints, dump, close it. */
static void app(char *name, char *exe)
{
    HWND w = NULL;
    int i;
    DWORD t0, t1, ts;
    char title[40];
    seq++;
    clear();
    line("STAGE", seq);
    _lwrite(logFile, "NAME=", 5);
    _lwrite(logFile, name, lstrlen(name));
    _lwrite(logFile, "\r\n", 2);
    flush();
    ts = GetTickCount();
    line("WINEXEC", WinExec(exe, SW_SHOWNORMAL));
    for (i = 0; i < 2000 && w == NULL; i++) {
        pump(4);
        w = GetActiveWindow();
        if (w == lastApp || !IsWindow(w)) w = NULL;
    }
    lastApp = w;
    line("APP_FOUND", w != NULL);
    if (w != NULL) {
        i = GetWindowText(w, title, sizeof(title) - 1);
        _lwrite(logFile, "TITLE=", 6);
        _lwrite(logFile, title, i);
        _lwrite(logFile, "\r\n", 2);
    }
    if (w == NULL) { flush(); return; }
    UpdateWindow(w);
    pump(200);
    t1 = GetTickCount();
    line("LAUNCH_TO_PAINTED_MS", (long)(t1 - ts));
    for (i = 0; i < 3; i++) {
        resettrace();
        if (shots && i == 0) { line("REPAINT_START", seq); flush(); }
        InvalidateRect(w, NULL, TRUE);
        t0 = GetTickCount();
        UpdateWindow(w);
        t1 = GetTickCount();
        line("REPAINT_MS", (long)(t1 - t0));
    }
    savetrace();
    dump();
    flush();
    if (shots) hold();
    PostMessage(w, WM_CLOSE, 0, 0L);
    pump(400);
}

/* One visible_steps shape: kind 1 RoundRect, 2 Rectangle, 3 Ellipse. */
typedef struct { int kind, x, y, w, h, e, pen, brush, rop, clip; } STEP;
static STEP steps[] = {
    {1, 10, 10, 26, 15, 8, 1, 3, R2_COPYPEN, 0},     /* Calculator key under the cursor */
    {1, 40, 10, 26, 15, 8, 0, 1, R2_COPYPEN, 0},     /* no pen: fill only */
    {1, 25, 15, 26, 15, 8, 1, 3, R2_XORPEN, 0},      /* XOR over the first two */
    {1, 70, 10, 26, 15, 8, 1, 2, R2_COPYPEN, 0},     /* hollow: outline only */
    {1, 85, 8, 40, 20, 10, 1, 3, R2_COPYPEN, 1},     /* clipped to 90,12-110,20 */
    {1, -10, -6, 30, 16, 8, 1, 3, R2_COPYPEN, 0},    /* off the top-left corner */
    {1, -1, 120, 30, 16, 8, 0, 1, R2_COPYPEN, 0},    /* off the left edge, no pen */
    {1, 10, -40, 30, 16, 8, 1, 3, R2_COPYPEN, 0},    /* entirely above the screen */
    {1, 400, 50, 30, 16, 8, 1, 3, R2_COPYPEN, 0},    /* entirely right of it */
    {3, 130, 10, 20, 14, 0, 1, 1, R2_COPYPEN, 0},    /* Ellipse */
    {2, 160, 10, 26, 15, 0, 1, 3, R2_COPYPEN, 0},    /* Rectangle */
    {1, 10, 40, 60, 30, 12, 1, 0, R2_COPYPEN, 0},    /* large, white */
    {1, 50, 50, 26, 15, 8, 0, 1, R2_XORPEN, 0},      /* no pen, XOR */
    {1, 0, 0, 0, 0, 8, 1, 3, R2_COPYPEN, 2}          /* bottom-right corner (set below) */
};
#define NSTEPS (sizeof(steps) / sizeof(steps[0]))

static void framedump(int k, int marker)
{
    HFILE h;
    char n[] = "C:\\RV00.BIN";
    if (marker) n[4] = 'M';
    numname(n, 5, k);
    h = _lcreat(n, 0);
    line("STEP_DUMP_CREATED", h != HFILE_ERROR);
    if (h != HFILE_ERROR) {
        line("STEP_DUMP_BYTES", _lwrite(h, (LPSTR)0xb8000000L, 0x8000U));
        _lclose(h);
    }
}

static void stepdump(int k) { framedump(k, 0); }

/* Actual ordinal-8 calls exercise incomplete/interleaved marker streams.
 * A nonzero device type is mapped to the real driver shadow. A zeroed
 * six-byte physical pen is solid index 0; draw mode starts with R2_COPYPEN.
 * The malformed-batch case uses valid 65-point storage rejected only by
 * the bounded gate's conservative 64-point limit.
 */
static void markerstage(void)
{
    typedef int (FAR PASCAL *OUTPROC)(LPSTR,int,int,POINT FAR *,LPSTR,LPSTR,LPSTR,RECT FAR *);
    OUTPROC output;
    POINT pts[65];
    int device = 1, memory = 0, mode[16], pen[3], k, i, ok = 0, a, b, at;
    DWORD t0 = GetTickCount();
    output = (OUTPROC)GetProcAddress(GetModuleHandle("DISPLAY"), MAKEINTRESOURCE(8));
    for (i = 0; i < 16; i++) mode[i] = 0;
    for (i = 0; i < 3; i++) pen[i] = 0;
    mode[0] = R2_COPYPEN; mode[1] = OPAQUE;
    pts[0].x = 0; pts[0].y = pany + 144;
    for (i = 1; i < 65; i++) { pts[i].x = panx + 4; pts[i].y = panx + 45; }
    seq++;
    line("STAGE", seq);
    _lwrite(logFile, "NAME=marker_steps\r\n", 19);
    line("KIND", 5); line("COUNT", 8);
    line("RAW_OUTPUT_FOUND", output != NULL);
    if (!output) { flush(); return; }
    for (k = 1; k <= 8; k++) {
        clear();
        pts[0].y = pany + 144;
        output((LPSTR)&device,80,0,NULL,NULL,NULL,NULL,NULL);
        a = output((LPSTR)&device,4,2,pts,(LPSTR)pen,NULL,(LPSTR)mode,NULL);
        pts[0].y++;
        b = output((LPSTR)&device,4,2,pts,(LPSTR)pen,NULL,(LPSTR)mode,NULL);
        at = (144 / 4) * 160 + 2;
        if (hardware) at += ((pany / 4) * 160 + panx / 2) & 8191;
        at &= 8191;
        line("ROWS_VISIBLE_BEFORE_SETTLE", (((BYTE FAR *)0xb8000000L)[at] & 15) == 0);
        if (k == 1) output((LPSTR)&device,81,0,NULL,NULL,NULL,NULL,NULL);
        if (k == 2) {
            output((LPSTR)&device,80,0,NULL,NULL,NULL,NULL,NULL);
            output((LPSTR)&device,81,0,NULL,NULL,NULL,NULL,NULL);
        }
        if (k == 3) SetPixel(dc, 100, 144, RGB(0,0,0));
        if (k == 4) output((LPSTR)&memory,81,0,NULL,NULL,NULL,NULL,NULL);
        if (k == 5) output((LPSTR)&device,79,0,NULL,NULL,NULL,NULL,NULL);
        if (k == 6) setpan();
        if (k == 7) {
            pts[0].y++;
            output((LPSTR)&device,4,65,pts,(LPSTR)pen,NULL,(LPSTR)mode,NULL);
        }
        if (k == 8) GetPixel(dc, 4, 144);
        ok += a != 0 && b != 0;
        framedump(k, 1);
    }
    line("ELAPSED_MS", GetTickCount() - t0);
    line("API_SUCCESSES", ok); line("STEP_DUMPS", 8);
    dump(); flush();
}

static void stepstage(void)
{
    int k, c, shown = 0, ok = 0;
    HPEN pens[2];
    HBRUSH brushes[4];
    HPEN op;
    HBRUSH ob;
    HRGN rgn;
    DWORD t0, t1;
    STEP *s;
    pens[0] = nullPen; pens[1] = blackPen;
    brushes[0] = white; brushes[1] = gray; brushes[2] = hollow; brushes[3] = ltgray;
    steps[NSTEPS - 1].x = width - 15;
    steps[NSTEPS - 1].y = height - 8;
    steps[NSTEPS - 1].w = 30;
    steps[NSTEPS - 1].h = 16;
    steps[NSTEPS - 1].clip = 0;
    seq++;
    clear();
    SetCursor(LoadCursor(NULL, IDC_ARROW));
    do { c = ShowCursor(TRUE); shown++; } while (c < 0 && shown < 40);
    cursorpos(30, 22);
    pump(20);
    line("STAGE", seq);
    _lwrite(logFile, "NAME=visible_steps\r\n", 20);
    line("KIND", 4);
    line("COUNT", NSTEPS);
    flush();
    resettrace();
    t0 = GetTickCount();
    for (k = 0; k < NSTEPS; k++) {
        s = &steps[k];
        op = SelectObject(dc, pens[s->pen]);
        ob = SelectObject(dc, brushes[s->brush]);
        SetROP2(dc, s->rop);
        rgn = NULL;
        if (s->clip == 1) {
            rgn = CreateRectRgn(90 + panx, 12 + pany, 110 + panx, 20 + pany);
            SelectClipRgn(dc, rgn);
        }
        if (s->kind == 1) ok += RoundRect(dc, s->x, s->y, s->x + s->w, s->y + s->h, s->e, s->e) != 0;
        else if (s->kind == 2) ok += Rectangle(dc, s->x, s->y, s->x + s->w, s->y + s->h) != 0;
        else ok += Ellipse(dc, s->x, s->y, s->x + s->w, s->y + s->h) != 0;
        if (rgn) {
            SelectClipRgn(dc, NULL);
            DeleteObject(rgn);
        }
        SetROP2(dc, R2_COPYPEN);
        SelectObject(dc, op);
        SelectObject(dc, ob);
        stepdump(k + 1);
    }
    t1 = GetTickCount();
    line("ELAPSED_MS", (long)(t1 - t0));
    line("API_SUCCESSES", ok);
    line("STEP_DUMPS", NSTEPS);
    savetrace();
    cursorpos(width - 1, height - 1);
    pump(20);
    dump();
    while (shown-- > 0) ShowCursor(FALSE);
    SetCursor(NULL);
    flush();
}

/* Calculator-sized keys drawn with the arrow cursor visible over them. */
static void cursorstage(void)
{
    int c, shown = 0;
    seq++;
    clear();
    SetCursor(LoadCursor(NULL, IDC_ARROW));
    do { c = ShowCursor(TRUE); shown++; } while (c < 0 && shown < 40);
    cursorpos(40, 10);
    pump(20);
    seq--;
    batch("cursor_overlap", 1, 26, 15, 8, 8, blackPen, ltgray, R2_COPYPEN, 20, 30, 20, 0);
    cursorpos(width - 1, height - 1);
    pump(20);
    dump();
    while (shown-- > 0) ShowCursor(FALSE);
    SetCursor(NULL);
    flush();
}

int PASCAL WinMain(HANDLE inst, HANDLE prev, LPSTR cmd, int show)
{
    int hide = 0, c;
    HCURSOR oldcur;
    OFSTRUCT of;
    HFILE xf;
    char xrmode[2];
    xf = _lopen("C:\\XRPAN.INI", OF_READ);
    if (xf != HFILE_ERROR) {
        xrmode[0] = 'x'; xrmode[1] = 0;
        _lread(xf, (LPSTR)xrmode, 1); _lclose(xf);
        cmd = (LPSTR)xrmode;
    }
    if (cmd && (cmd[0] == 'x' || cmd[0] == 'y' || cmd[0] == 'z')) {
        xr = 1; panx = cmd[0] == 'z' ? 320 : (cmd[0] == 'y' ? 8 : 0); pany = cmd[0] == 'x' ? 0 : 56;
    }
    if (cmd && cmd[0] >= '1' && cmd[0] <= '9') mult = cmd[0] - '0';
    logFile = _lcreat("C:\\RRBENCH.LOG", 0);
    if (logFile == HFILE_ERROR) return 1;
    dc = GetDC(NULL);
    hardware = OpenFile("C:\\XRHARD.ON", &of, OF_EXIST) != HFILE_ERROR;
    width = GetSystemMetrics(SM_CXSCREEN);
    height = GetSystemMetrics(SM_CYSCREEN);
    line("VERSION", xr ? 5 : 4);
    if (xr) line("HARDWARE", hardware);
    line("LOGICAL_WIDTH", width); line("LOGICAL_HEIGHT", height);
    if (xr) { width = 320; height = 200; setpan(); SetViewportOrg(dc, panx, pany); }
    line("SCREEN_WIDTH", width);
    line("SCREEN_HEIGHT", height);
    line("NUMCOLORS", GetDeviceCaps(dc, NUMCOLORS));
    line("CURVECAPS", GetDeviceCaps(dc, CURVECAPS));
    line("POLYGONALCAPS", GetDeviceCaps(dc, POLYGONALCAPS));
    line("MULTIPLIER", mult);
    shots = OpenFile("C:\\RRECT\\RRSHOTS.ON", &of, OF_EXIST) != HFILE_ERROR;
    line("SHOTS", shots);
    white = GetStockObject(WHITE_BRUSH);
    gray = GetStockObject(GRAY_BRUSH);
    ltgray = GetStockObject(LTGRAY_BRUSH);
    hollow = GetStockObject(NULL_BRUSH);
    blackPen = GetStockObject(BLACK_PEN);
    nullPen = GetStockObject(NULL_PEN);
    SetMapMode(dc, MM_TEXT);
    SetBkMode(dc, OPAQUE);
    SetBkColor(dc, RGB(255, 255, 255));
    do { c = ShowCursor(FALSE); hide++; } while (c >= 0 && hide < 32);
    oldcur = SetCursor(NULL);
    flush();
    /* Calculator-sized keys first, then variants that exercise fallbacks. */
    if (!shots) {
        batch("roundrect_key", 1, 26, 15, 8, 8, blackPen, ltgray, R2_COPYPEN, 20, 30, 20, 0);
        batch("rectangle_key", 2, 26, 15, 0, 0, blackPen, ltgray, R2_COPYPEN, 20, 30, 20, 0);
        batch("roundrect_large", 1, 60, 30, 12, 12, blackPen, white, R2_COPYPEN, 6, 64, 36, 0);
        batch("roundrect_hollow", 1, 26, 15, 8, 8, blackPen, hollow, R2_COPYPEN, 20, 30, 20, 0);
        batch("roundrect_nopen", 1, 26, 15, 8, 8, nullPen, gray, R2_COPYPEN, 20, 30, 20, 0);
        batch("roundrect_xor", 1, 26, 15, 8, 8, blackPen, ltgray, R2_XORPEN, 20, 30, 20, 0);
        batch("roundrect_overlap", 1, 26, 15, 8, 8, blackPen, ltgray, R2_COPYPEN, 20, 6, 4, 0);
        batch("roundrect_clipped", 1, 26, 15, 8, 8, blackPen, ltgray, R2_COPYPEN, 20, 30, 20, 1);
        batch("ellipse_12", 3, 12, 12, 0, 0, blackPen, gray, R2_COPYPEN, 4, 20, 20, 0);
        cursorstage();
        stepstage();
        if (xr) markerstage();
        if (xr) { panx = pany = 0; SetViewportOrg(dc, 0, 0); setpan(); }
    }
    app("calc", "CALC.EXE");
    app("reversi", "REVERSI.EXE");
    app("pbrush", "PBRUSH.EXE");
    line("COMPLETE", 1);
    _lclose(logFile);
    ReleaseDC(NULL, dc);
    SetCursor(oldcur);
    while (hide-- > 0) ShowCursor(TRUE);
    return 0;
}
