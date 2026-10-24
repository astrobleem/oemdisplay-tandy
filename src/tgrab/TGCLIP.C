/* TGCLIP.EXE - put a grabbed Tandy DOS graphics screen on the Clipboard as
 * a bitmap (Windows 3.0 real mode; MIT).
 *
 * Windows 3.0 real-mode WINOLDAP copies a full-screen DOS program's screen
 * to the Clipboard only as OEM text. For the Tandy 16-colour modes 8 and 9,
 * TANDYGR.GR2 writes the screen to a 4-bit BMP file and hands WINOLDAP one
 * text line instead:   TANDYGR <path of the BMP>
 * TGCLIP sits in the Clipboard viewer chain (start it from WIN.INI load=).
 * When that line appears it reads the BMP, makes a device bitmap with
 * CreateDIBitmap, replaces the Clipboard contents with it (CF_BITMAP) and
 * deletes the file. Paintbrush's Edit > Paste then pastes the picture.
 * Any other Clipboard contents are left alone. Started once by hand, it
 * also adds itself to WIN.INI [windows] load= (WriteProfileString), so it
 * starts with Windows from then on. C, small model, 8086.
 */
#include <windows.h>

#define WM_TGCHECK (WM_USER + 1)

static HWND hwndNext;
static BOOL fBusy;
static char szPrefix[] = "TANDYGR ";

long FAR PASCAL WndProc(HWND, unsigned, WORD, LONG);

/* Path from the Clipboard's OEM text if it is our line, else FALSE. */
static BOOL GetGrabPath(HWND hwnd, char *path, int cb)
{
    HANDLE h;
    LPSTR p;
    int i, n;
    BOOL ok = FALSE;

    if (!IsClipboardFormatAvailable(CF_OEMTEXT))
        return FALSE;
    if (!OpenClipboard(hwnd))
        return FALSE;
    h = GetClipboardData(CF_OEMTEXT);
    if (h && (p = GlobalLock(h)) != NULL) {
        for (i = 0; szPrefix[i] && p[i] == szPrefix[i]; i++)
            ;
        if (szPrefix[i] == 0) {
            p += i;
            for (n = 0; n < cb - 1 && p[n] > ' '; n++)
                path[n] = p[n];
            path[n] = 0;
            ok = n > 0;
        }
        GlobalUnlock(h);
    }
    CloseClipboard();
    return ok;
}

/* Read the whole BMP file into a global block. */
static HANDLE ReadFileBlock(char *path)
{
    OFSTRUCT of;
    int fh;
    long size;
    HANDLE h;
    LPSTR p;
    long done;
    WORD part;

    fh = OpenFile(path, &of, OF_READ);
    if (fh == -1)
        return NULL;
    size = _llseek(fh, 0L, 2);
    _llseek(fh, 0L, 0);
    if (size < 54L || size > 65000L) {
        _lclose(fh);
        return NULL;
    }
    h = GlobalAlloc(GMEM_MOVEABLE, size);
    if (!h) {
        _lclose(fh);
        return NULL;
    }
    p = GlobalLock(h);
    for (done = 0; done < size; done += part) {
        part = (WORD)((size - done) > 16384L ? 16384L : (size - done));
        if (_lread(fh, p + (WORD)done, part) != part) {
            GlobalUnlock(h);
            GlobalFree(h);
            _lclose(fh);
            return NULL;
        }
    }
    GlobalUnlock(h);
    _lclose(fh);
    return h;
}

static void ConvertGrab(HWND hwnd)
{
    char path[128];
    HANDLE hFile;
    LPSTR p;
    LPBITMAPINFOHEADER bih;
    HBITMAP hbm;
    HDC hdc;
    OFSTRUCT of;
    DWORD off;

    if (!GetGrabPath(hwnd, path, sizeof(path)))
        return;
    hFile = ReadFileBlock(path);
    if (!hFile)
        return;
    p = GlobalLock(hFile);
    if (p[0] != 'B' || p[1] != 'M') {
        GlobalUnlock(hFile);
        GlobalFree(hFile);
        return;
    }
    off = *(DWORD FAR *)(p + 10);
    bih = (LPBITMAPINFOHEADER)(p + 14);
    hdc = GetDC(NULL);
    hbm = CreateDIBitmap(hdc, bih, CBM_INIT, p + (WORD)off,
                         (LPBITMAPINFO)bih, DIB_RGB_COLORS);
    ReleaseDC(NULL, hdc);
    GlobalUnlock(hFile);
    GlobalFree(hFile);
    if (!hbm)
        return;
    fBusy = TRUE;
    if (OpenClipboard(hwnd)) {
        EmptyClipboard();
        SetClipboardData(CF_BITMAP, hbm);
        CloseClipboard();
        OpenFile(path, &of, OF_DELETE);
    } else {
        DeleteObject(hbm);
    }
    fBusy = FALSE;
}

long FAR PASCAL WndProc(HWND hwnd, unsigned msg, WORD wParam, LONG lParam)
{
    switch (msg) {
    case WM_CREATE:
        hwndNext = SetClipboardViewer(hwnd);
        return 0;
    case WM_CHANGECBCHAIN:
        if ((HWND)wParam == hwndNext)
            hwndNext = (HWND)LOWORD(lParam);
        else if (hwndNext)
            SendMessage(hwndNext, msg, wParam, lParam);
        return 0;
    case WM_DRAWCLIPBOARD:
        if (hwndNext)
            SendMessage(hwndNext, msg, wParam, lParam);
        if (!fBusy)
            PostMessage(hwnd, WM_TGCHECK, 0, 0L);
        return 0;
    case WM_TGCHECK:
        ConvertGrab(hwnd);
        return 0;
    case WM_DESTROY:
        ChangeClipboardChain(hwnd, hwndNext);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

/* Add this program to WIN.INI load= unless TGCLIP is already listed. */
static void Register(HANDLE hInst)
{
    char load[256], self[128];
    int i, n, m;

    GetProfileString("windows", "load", "", load, sizeof(load));
    for (i = 0; load[i]; i++) {
        if ((load[i] | 0x20) == 't' && (load[i + 1] | 0x20) == 'g' &&
            (load[i + 2] | 0x20) == 'c' && (load[i + 3] | 0x20) == 'l' &&
            (load[i + 4] | 0x20) == 'i' && (load[i + 5] | 0x20) == 'p')
            return;
    }
    m = GetModuleFileName(hInst, self, sizeof(self));
    n = lstrlen(load);
    if (m <= 0 || n + m + 2 > (int)sizeof(load))
        return;
    if (n > 0)
        load[n++] = ' ';
    lstrcpy(load + n, self);
    WriteProfileString("windows", "load", load);
}

int PASCAL WinMain(HANDLE hInst, HANDLE hPrev, LPSTR lpCmd, int nShow)
{
    WNDCLASS wc;
    MSG msg;
    HWND hwnd;

    if (hPrev)
        return 0;                       /* one copy is enough */
    Register(hInst);
    wc.style = 0;
    wc.lpfnWndProc = WndProc;
    wc.cbClsExtra = 0;
    wc.cbWndExtra = 0;
    wc.hInstance = hInst;
    wc.hIcon = NULL;
    wc.hCursor = NULL;
    wc.hbrBackground = NULL;
    wc.lpszMenuName = NULL;
    wc.lpszClassName = "TGClip";
    if (!RegisterClass(&wc))
        return 0;
    hwnd = CreateWindow("TGClip", "TGCLIP", WS_OVERLAPPED, 0, 0, 0, 0,
                        NULL, NULL, hInst, NULL);
    if (!hwnd)
        return 0;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return msg.wParam;
}
