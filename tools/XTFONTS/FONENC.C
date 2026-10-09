/* Original complete-byte Win16 font probe; 8086/8088 MSC6 small model.
 * Stock SYS/FIX/OEM: all 00..FF bytes in twelve 64-glyph pages.
 * Use only with our fonts. Never atlas privately owned Microsoft fonts.
 */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static HINSTANCE instance;
static HFILE logfile;
static int page;
static int stocks[3] = { SYSTEM_FONT, SYSTEM_FIXED_FONT, OEM_FIXED_FONT };
static char initials[3] = { 'S', 'F', 'O' };
static void number(char *key, long value)
{
    char text[100], digits[12];
    int n = 0, count = 0;
    unsigned long magnitude;
    while (*key) text[n++] = *key++;
    text[n++] = '=';
    if (value < 0) { text[n++] = '-'; magnitude = (unsigned long)(-value); }
    else magnitude = (unsigned long)value;
    do { digits[count++] = (char)('0' + magnitude % 10); magnitude /= 10; }
    while (magnitude);
    while (count) text[n++] = digits[--count];
    text[n++] = '\r'; text[n++] = '\n';
    _lwrite(logfile, text, n);
}
static void filename(char *out, int current, char *extension)
{
    strcpy(out, "C:\\S0.BIN");
    out[3] = initials[current / 4];
    out[4] = (char)('0' + current % 4);
    strcpy(out + 6, extension);
}
static void capture(void)
{
    char name[20];
    HFILE f;
    filename(name, page, "BIN");
    f = _lcreat(name, 0);
    number("CAPTURE_PAGE", page);
    if (f == HFILE_ERROR) number("CAPTURE_ERROR", 1);
    else {
        number("CAPTURE_BYTES", _lwrite(f, (void FAR *)0xb8000000L, 32768U));
        _lclose(f);
    }
}
static void fontmetrics(HDC dc, int stock)
{
    TEXTMETRIC tm;
    int widths[256];
    HFONT old;
    HFILE f;
    char name[20], face[64];
    int i;
    old = SelectObject(dc, GetStockObject(stock));
    number("STOCK", stock);
    if (!GetTextMetrics(dc, &tm)) number("METRICS_ERROR", 1);
    else {
        number("HEIGHT", tm.tmHeight); number("ASCENT", tm.tmAscent);
        number("INTERNAL", tm.tmInternalLeading); number("EXTERNAL", tm.tmExternalLeading);
        number("AVERAGE", tm.tmAveCharWidth); number("MAXIMUM", tm.tmMaxCharWidth);
        number("FIRST", (unsigned char)tm.tmFirstChar); number("LAST", (unsigned char)tm.tmLastChar);
        number("DEFAULT", (unsigned char)tm.tmDefaultChar); number("CHARSET", (unsigned char)tm.tmCharSet);
    }
    GetTextFace(dc, sizeof(face), face);
    _lwrite(logfile, face, strlen(face)); _lwrite(logfile, "\r\n", 2);
    for (i = 0; i < 256; i++) widths[i] = -1;
    number("WIDTH_QUERY", GetCharWidth(dc, (unsigned char)tm.tmFirstChar,
        (unsigned char)tm.tmLastChar, widths + (unsigned char)tm.tmFirstChar));
    for (i = 0; i < (int)(unsigned char)tm.tmFirstChar; i++) GetCharWidth(dc, i, i, widths + i);
    for (i = (int)(unsigned char)tm.tmLastChar + 1; i < 256; i++) GetCharWidth(dc, i, i, widths + i);
    strcpy(name, "C:\\SWIDTH.BIN");
    name[3] = (char)(stock == SYSTEM_FONT ? 'S' : stock == SYSTEM_FIXED_FONT ? 'F' : 'O');
    f = _lcreat(name, 0);
    if (f != HFILE_ERROR) { _lwrite(f, (void FAR *)widths, sizeof(widths)); _lclose(f); }
    SelectObject(dc, old);
}
LONG FAR PASCAL WindowProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    PAINTSTRUCT ps;
    HDC dc;
    HFONT old;
    RECT rc;
    POINT origin;
    char code;
    int i;
    if (msg == WM_PAINT) {
        dc = BeginPaint(hwnd, &ps);
        GetClientRect(hwnd, &rc);
        FillRect(dc, &rc, GetStockObject(WHITE_BRUSH));
        SetTextColor(dc, RGB(0,0,0)); SetBkColor(dc, RGB(255,255,255));
        old = SelectObject(dc, GetStockObject(stocks[page / 4]));
        for (i = 0; i < 64; i++) {
            code = (char)((page % 4) * 64 + i);
            TextOut(dc, 2 + (i % 8) * 16, 2 + (i / 8) * 16, &code, 1);
        }
        SelectObject(dc, old);
        EndPaint(hwnd, &ps);
        return 0;
    }
    if (msg == WM_TIMER) {
        capture(); page++;
        if (page == 12) {
            KillTimer(hwnd, 1); number("DONE", 1); _lclose(logfile);
            ExitWindows(0L, 0); DestroyWindow(hwnd);
        } else { InvalidateRect(hwnd, NULL, TRUE); UpdateWindow(hwnd); }
        return 0;
    }
    if (msg == WM_CREATE) {
        origin.x = 0; origin.y = 0; ClientToScreen(hwnd, &origin);
        number("CLIENT_X", origin.x); number("CLIENT_Y", origin.y);
        GetClientRect(hwnd, &rc);
        number("CLIENT_WIDTH", rc.right); number("CLIENT_HEIGHT", rc.bottom);
    }
    if (msg == WM_DESTROY) { PostQuitMessage(0); return 0; }
    wp = wp;
    return DefWindowProc(hwnd, msg, wp, lp);
}
int PASCAL WinMain(HINSTANCE current, HINSTANCE previous, LPSTR command, int show)
{
    WNDCLASS wc;
    HWND hwnd;
    HDC dc;
    MSG msg;
    int i;
    instance = current; command = command; show = show;
    logfile = _lcreat("C:\\FONENC.LOG", 0);
    if (logfile == HFILE_ERROR) return 1;
    number("SCREEN_WIDTH", GetSystemMetrics(SM_CXSCREEN));
    number("SCREEN_HEIGHT", GetSystemMetrics(SM_CYSCREEN));
    dc = GetDC(NULL);
    for (i = 0; i < 3; i++) fontmetrics(dc, stocks[i]);
    ReleaseDC(NULL, dc);
    if (!previous) {
        memset(&wc, 0, sizeof(wc)); wc.lpfnWndProc = WindowProc;
        wc.hInstance = current; wc.hCursor = LoadCursor(NULL, IDC_ARROW);
        wc.hbrBackground = GetStockObject(WHITE_BRUSH); wc.lpszClassName = "XTFONENC";
        if (!RegisterClass(&wc)) return 2;
    }
    hwnd = CreateWindow("XTFONENC", "XT encoding", WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU,
        0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN),
        NULL, NULL, current, NULL);
    if (!hwnd) return 3;
    ShowWindow(hwnd, SW_SHOW); UpdateWindow(hwnd); SetTimer(hwnd, 1, 500, NULL);
    while (GetMessage(&msg, NULL, 0, 0)) { TranslateMessage(&msg); DispatchMessage(&msg); }
    return msg.wParam;
}
