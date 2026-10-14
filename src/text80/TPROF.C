/* TPROF.C - typing and redraw profiler for the text-mode drivers
 * (TXT40/TEXT80 measurement builds with T80PROF, escape 5450h).
 * Windows 3.0 real mode, C89, /G0 /Gw /AS.
 *
 *   TPROF TYPE <n>   a Notepad-like window (multiline EDIT, system font);
 *                    n characters are sent one at a time as WM_CHAR, all
 *                    resulting messages are processed, and the driver's
 *                    counters are read and reset around each character.
 *   TPROF LINES <n>  the same window; n times a letter and Return, so once
 *                    the edit control is full each Return scrolls it.
 *   TPROF SNAP       read and reset the counters once (around typing into
 *                    another program, e.g. Notepad) and exit.
 *   TPROF IDLE <s>   process messages for s seconds, then SNAP.
 *   TPROF NOTE <a> <b>  start Notepad; after a seconds reset the counters
 *                    and log READY (the harness then types into Notepad
 *                    with real keys); b seconds later read them and exit.
 *                    TPROF has no window and sleeps in GetMessage on a
 *                    timer, so it takes no CPU time from Notepad.
 * Every reading is logged raw to TPROF.LOG beside TPROF.EXE (times in 1/65536 BIOS
 * tick = 0.838 us; the host converts them). Without escape 5450h only the
 * wall time from GetCurrentTime is logged.
 */
#include <windows.h>

#define PROF_ESC 0x5450
#define QUERYESC 8
#define NSLOT 20
#define NRING 256
#define NXRING 64

typedef struct {
    WORD magic, version;
    DWORD stamp;
    DWORD count[NSLOT];
    DWORD total[NSLOT];
    WORD ri;
    BYTE cur, pad;
    BYTE ring[NRING][16];
    WORD xi, xpad;
    int xring[NXRING][16];   /* version 2: ExtTextOut trace */
} PROF;

static HANDLE hInst;
static HWND hMain, hEdit;
static PROF FAR *pb;
static HANDLE hpb;
static int bProf;
static char szLog[128];        /* TPROF.LOG beside TPROF.EXE */
static char line[200];

static void LogLine(LPSTR text)
{
    int fh;
    OFSTRUCT of;
    fh = OpenFile(szLog, &of, OF_WRITE);
    if (fh == -1)
        fh = OpenFile(szLog, &of, OF_CREATE | OF_WRITE);
    if (fh == -1)
        return;
    _llseek(fh, 0L, 2);
    _lwrite(fh, text, lstrlen(text));
    _lwrite(fh, "\r\n", 2);
    _lclose(fh);
}

static int Read(int reset)
{
    HDC hdc = GetDC(NULL);
    int r = 0;
    if (hdc) {
        r = Escape(hdc, PROF_ESC, sizeof(int), (LPSTR)&reset, (LPSTR)pb);
        ReleaseDC(NULL, hdc);
    }
    return r > 0;
}

static int Supported(void)
{
    HDC hdc = GetDC(NULL);
    int esc = PROF_ESC, r = 0;
    if (hdc) {
        r = Escape(hdc, QUERYESC, sizeof(int), (LPSTR)&esc, NULL);
        ReleaseDC(NULL, hdc);
    }
    return r > 0;
}

/* one reading: label, then counts/totals of every slot, then the flushes */
static void Dump(LPSTR label, DWORD t0)
{
    int i, n;
    BYTE FAR *e;
    wsprintf(line, "%s stamp=%lu wall=%lu", label, pb->stamp, pb->stamp - t0);
    LogLine(line);
    for (i = 0; i < NSLOT; i++) {
        if (pb->count[i] == 0 && pb->total[i] == 0)
            continue;
        wsprintf(line, " S %d %lu %lu", i, pb->count[i], pb->total[i]);
        LogLine(line);
    }
    n = pb->count[0] < (DWORD)NRING ? (int)pb->count[0] : NRING;
    for (i = 0; i < n; i++) {
        e = pb->ring[(pb->ri - n + i) & (NRING - 1)];
        wsprintf(line, " F %d %d %d %d %lu %d", *(int FAR *)(e + 0), *(int FAR *)(e + 2),
                 *(int FAR *)(e + 4), *(int FAR *)(e + 6), *(DWORD FAR *)(e + 8), (int)e[12]);
        LogLine(line);
    }
    /* ExtTextOut trace: clip l t r b, opaque l t r b, options, count,
       bounds rowfirst rowlast colfirst collast, dirty, font version,
       font pixel height, fixed width (0 = variable pitch) */
    if (pb->version >= 2) {
        n = pb->count[10] < (DWORD)NXRING ? (int)pb->count[10] : NXRING;
        for (i = 0; i < n; i++) {
            int FAR *x = pb->xring[(pb->xi - n + i) & (NXRING - 1)];
            wsprintf(line, " X %d %d %d %d  %d %d %d %d  %d %d  %d %d %d %d  %d  %d %d %d",
                     x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9],
                     x[10], x[11], x[12], x[13], x[14] & 0xFF, (x[14] >> 8) & 0xFF,
                     x[15] & 0xFF, (x[15] >> 8) & 0xFF);
            LogLine(line);
        }
    }
}

static void Pump(void)
{
    MSG msg;
    while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
}

long FAR PASCAL WndProc(HWND hwnd, unsigned msg, WORD wParam, LONG lParam)
{
    RECT r;
    switch (msg) {
    case WM_SIZE:
        if (hEdit) {
            GetClientRect(hwnd, &r);
            MoveWindow(hEdit, 0, 0, r.right, r.bottom, TRUE);
        }
        return 0;
    case WM_SETFOCUS:
        if (hEdit)
            SetFocus(hEdit);
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

static int Num(LPSTR s)
{
    int n = 0;
    while (*s == ' ')
        s++;
    while (*s >= '0' && *s <= '9')
        n = n * 10 + (*s++ - '0');
    return n;
}

static LPSTR Skip(LPSTR s)
{
    while (*s == ' ')
        s++;
    while (*s >= '0' && *s <= '9')
        s++;
    return s;
}

/* Sleep in GetMessage; SetTimer takes at most 65535 ms, so long waits are
 * made of 30 s steps. */
static void Sleep(int seconds)
{
    MSG msg;
    WORD id;
    while (seconds > 0) {
        int step = seconds > 30 ? 30 : seconds;
        seconds -= step;
        id = SetTimer(NULL, 0, (WORD)step * 1000, NULL);
        if (!id)
            return;
        while (GetMessage(&msg, NULL, 0, 0)) {
            if (msg.message == WM_TIMER && msg.hwnd == NULL)
                break;
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
        KillTimer(NULL, id);
    }
}

static int Is(LPSTR cmd, LPSTR word)
{
    while (*word) {
        if ((*cmd | 0x20) != (*word | 0x20))
            return 0;
        cmd++;
        word++;
    }
    return *cmd == 0 || *cmd == ' ';
}

static void TypeTest(int n, int lines)
{
    static char text[] = "The quick brown fox jumps over the lazy dog 0123456789 ";
    int i;
    DWORD t0, w0, w1;
    char label[40];
    WNDCLASS wc;
    wc.style = 0;
    wc.lpfnWndProc = WndProc;
    wc.cbClsExtra = 0;
    wc.cbWndExtra = 0;
    wc.hInstance = hInst;
    wc.hIcon = NULL;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = COLOR_WINDOW + 1;
    wc.lpszMenuName = NULL;
    wc.lpszClassName = "TProf";
    if (!RegisterClass(&wc))
        return;
    /* An explicit place inside a 320x200 screen. (CW_USEDEFAULT with y = 0
       made Windows 3.0 show the window with nCmdShow 0, SW_HIDE: every
       earlier TYPE reading measured an invisible edit control, its text
       clipped to an empty rectangle; seen with the ExtTextOut trace.) */
    hMain = CreateWindow("TProf", "TPROF - typing", WS_OVERLAPPEDWINDOW | WS_VISIBLE,
                         8, 48, 296, 120, NULL, NULL, hInst, NULL);
    if (!hMain)
        return;
    hEdit = CreateWindow("edit", NULL, WS_CHILD | WS_VISIBLE | WS_VSCROLL | WS_HSCROLL | ES_MULTILINE |
                         ES_AUTOHSCROLL | ES_AUTOVSCROLL, 0, 0, 10, 10, hMain, (HMENU)1, hInst, NULL);
    SendMessage(hMain, WM_SIZE, 0, 0L);
    SetFocus(hEdit);
    UpdateWindow(hMain);
    Pump();
    if (bProf) {
        Read(1);
        t0 = pb->stamp;
    }
    w0 = GetCurrentTime();
    for (i = 0; i < n; i++) {
        if (lines) {
            /* a short line and Return: once the edit control is full, every
               Return scrolls it up one line (a screen-to-screen copy) */
            SendMessage(hEdit, WM_CHAR, 'a' + i % 26, 1L);
            SendMessage(hEdit, WM_CHAR, '\r', 1L);
        } else
            SendMessage(hEdit, WM_CHAR, text[i % (sizeof(text) - 1)], 1L);
        Pump();
        if (bProf) {
            Read(1);
            wsprintf(label, lines ? "LINE %d" : "CHAR %d", i);
            Dump(label, t0);
            /* logging is disk I/O: restart the clock and counters after it */
            Read(1);
            t0 = pb->stamp;
        }
    }
    w1 = GetCurrentTime();
    wsprintf(line, lines ? "LINES n=%d ms=%lu" : "TYPE n=%d ms=%lu", n, w1 - w0);
    LogLine(line);
    DestroyWindow(hMain);
}

int PASCAL WinMain(HANDLE hI, HANDLE hPrev, LPSTR lpCmd, int nShow)
{
    DWORD t0, w0;
    hInst = hI;
    {
        int n = GetModuleFileName(hI, szLog, sizeof(szLog) - 10);
        while (n > 0 && szLog[n - 1] != '\\' && szLog[n - 1] != ':')
            n--;
        lstrcpy(szLog + n, "TPROF.LOG");
    }
    hpb = GlobalAlloc(GMEM_FIXED, (DWORD)sizeof(PROF));
    if (!hpb)
        return 0;
    pb = (PROF FAR *)GlobalLock(hpb);
    bProf = Supported();
    wsprintf(line, "START cmd=%s prof=%d free=%lu size=%d", lpCmd, bProf, GetFreeSpace(0), (int)sizeof(PROF));
    LogLine(line);
    if (Is(lpCmd, "TYPE")) {
        TypeTest(Num(lpCmd + 4), 0);
    } else if (Is(lpCmd, "LINES")) {
        TypeTest(Num(lpCmd + 5), 1);
    } else if (Is(lpCmd, "IDLE")) {
        if (bProf)
            Read(1);
        t0 = bProf ? pb->stamp : 0;
        w0 = GetCurrentTime();
        while (GetCurrentTime() - w0 < (DWORD)Num(lpCmd + 4) * 1000L)
            Pump();
        if (bProf) {
            Read(1);
            Dump("IDLE", t0);
        }
    } else if (Is(lpCmd, "NOTE")) {
        int a = Num(lpCmd + 4), b = Num(Skip(lpCmd + 4));
        w0 = GetCurrentTime();
        WinExec("NOTEPAD.EXE", SW_SHOWNORMAL);
        Sleep(a);
        if (bProf)
            Read(1);
        t0 = bProf ? pb->stamp : 0;
        w0 = GetCurrentTime();
        LogLine("READY");
        Sleep(b);
        if (bProf) {
            Read(1);
            Dump("NOTE", t0);
        }
        wsprintf(line, "NOTE ms=%lu", GetCurrentTime() - w0);
        LogLine(line);
    } else if (bProf) {
        Read(1);
        Dump("SNAP", pb->stamp);
    }
    LogLine("END");
    GlobalUnlock(hpb);
    GlobalFree(hpb);
    return 0;
}
