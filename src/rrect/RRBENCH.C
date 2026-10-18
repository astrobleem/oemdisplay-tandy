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
 * Log: C:\RRBENCH.LOG, one KEY=value per line.
 * Command line: an optional batch count multiplier digit (default 1).
 */
#define WINVER 0x0300
#include <windows.h>

static HFILE logFile;
static HDC dc;
static int width, height, seq = 0, mult = 1;
static HPEN blackPen, nullPen;
static HBRUSH white, gray, hollow, ltgray;
static HWND lastApp = NULL;
static char trbuf[4 + 64 * 20];

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
        rgn = CreateRectRgn(40, 30, width - 40, height - 30);
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
        InvalidateRect(w, NULL, TRUE);
        t0 = GetTickCount();
        UpdateWindow(w);
        t1 = GetTickCount();
        line("REPAINT_MS", (long)(t1 - t0));
    }
    savetrace();
    dump();
    flush();
    PostMessage(w, WM_CLOSE, 0, 0L);
    pump(400);
}

/* Calculator-sized keys drawn with the arrow cursor visible over them. */
static void cursorstage(void)
{
    int c, shown = 0;
    seq++;
    clear();
    SetCursor(LoadCursor(NULL, IDC_ARROW));
    do { c = ShowCursor(TRUE); shown++; } while (c < 0 && shown < 40);
    SetCursorPos(40, 10);
    pump(20);
    seq--;
    batch("cursor_overlap", 1, 26, 15, 8, 8, blackPen, ltgray, R2_COPYPEN, 20, 30, 20, 0);
    SetCursorPos(width - 1, height - 1);
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
    if (cmd && cmd[0] >= '1' && cmd[0] <= '9') mult = cmd[0] - '0';
    logFile = _lcreat("C:\\RRBENCH.LOG", 0);
    if (logFile == HFILE_ERROR) return 1;
    dc = GetDC(NULL);
    width = GetSystemMetrics(SM_CXSCREEN);
    height = GetSystemMetrics(SM_CYSCREEN);
    line("VERSION", 2);
    line("SCREEN_WIDTH", width);
    line("SCREEN_HEIGHT", height);
    line("NUMCOLORS", GetDeviceCaps(dc, NUMCOLORS));
    line("CURVECAPS", GetDeviceCaps(dc, CURVECAPS));
    line("POLYGONALCAPS", GetDeviceCaps(dc, POLYGONALCAPS));
    line("MULTIPLIER", mult);
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
