#define WINVER 0x0300
#include <windows.h>

#define LOG_PATH "C:\\W16API.LOG"
#define CALLBACK_COOKIE 0x13579BDFL
#define LOG_LIMIT 64

static HFILE g_log = (HFILE)-1;
static HWND g_probe_window = (HWND)0;
static unsigned g_all_count = 0;
static unsigned g_logged_count = 0;
static unsigned g_stop_count = 0;
static int g_cookie_ok = 1;
static int g_probe_seen = 0;
static int g_stop_mode = 0;

static void put_text(const char FAR *text)
{
    if (g_log != (HFILE)-1 && text != (const char FAR *)0)
        _lwrite(g_log, (const void _huge *)text, (UINT)lstrlen(text));
}

static void put_hex(unsigned long value, unsigned digits)
{
    static const char hex[] = "0123456789ABCDEF";
    char buffer[8];
    unsigned i;

    for (i = 0; i < digits; ++i) {
        buffer[digits - i - 1] = hex[(unsigned)(value & 0x0F)];
        value >>= 4;
    }
    _lwrite(g_log, (const void _huge *)buffer, (UINT)digits);
}

static void put_decimal(unsigned value)
{
    char buffer[6];
    unsigned used = 0;

    do {
        buffer[used++] = (char)('0' + (value % 10));
        value /= 10;
    } while (value != 0 && used < sizeof(buffer));
    while (used != 0) {
        --used;
        _lwrite(g_log, (const void _huge *)&buffer[used], 1);
    }
}

static void put_newline(void)
{
    put_text("\r\n");
}

static void log_window(const char FAR *tag, HWND hwnd, LPARAM cookie)
{
    put_text(tag);
    put_text(" hwnd=0x");
    put_hex((unsigned long)(WORD)hwnd, 4);
    put_text(" lParam=0x");
    put_hex((unsigned long)cookie, 8);
    put_newline();
}

BOOL FAR PASCAL EnumProc(HWND hwnd, LPARAM cookie)
{
    if (g_stop_mode) {
        ++g_stop_count;
        if (g_stop_count <= LOG_LIMIT)
            log_window("STOP callback", hwnd, cookie);
        return FALSE;
    }

    ++g_all_count;
    if (cookie != (LPARAM)CALLBACK_COOKIE)
        g_cookie_ok = 0;
    if (hwnd == g_probe_window)
        g_probe_seen = 1;
    if (g_logged_count < LOG_LIMIT) {
        log_window("ENUM callback", hwnd, cookie);
        ++g_logged_count;
    }
    return TRUE;
}

int PASCAL WinMain(HINSTANCE instance, HINSTANCE previous,
                   LPSTR command_line, int show_command)
{
    DWORD version;
    WORD low_version;
    FARPROC thunk;
    BOOL enum_result;
    int failures = 0;

    (void)previous;
    (void)command_line;
    (void)show_command;

    g_log = _lcreat(LOG_PATH, 0);
    if (g_log == (HFILE)-1)
        return 2;

    put_text("Native Win16 API fixture\r\n");
    version = GetVersion();
    put_text("GetVersion DWORD=0x");
    put_hex(version, 8);
    put_newline();
    low_version = (WORD)(version & 0xFFFFL);
    put_text("Windows version major=");
    put_decimal((unsigned)(low_version & 0x00FF));
    put_text(" minor=");
    put_decimal((unsigned)((low_version >> 8) & 0x00FF));
    put_newline();

    /* STATIC is a system window class; keep this top-level probe hidden. */
    g_probe_window = CreateWindow("STATIC", "W16API probe", 0L,
                                  0, 0, 1, 1,
                                  (HWND)0, (HMENU)0, instance,
                                  (void FAR *)0);
    if (g_probe_window == (HWND)0) {
        put_text("FAIL CreateWindow\r\n");
        failures = 1;
    } else {
        thunk = MakeProcInstance((FARPROC)EnumProc, instance);
        if (thunk == (FARPROC)0) {
            put_text("FAIL MakeProcInstance\r\n");
            failures = 1;
        } else {
            put_text("EnumWindows all-pass begin\r\n");
            enum_result = EnumWindows((WNDENUMPROC)thunk,
                                      (LPARAM)CALLBACK_COOKIE);
            put_text("EnumWindows all-pass result=");
            put_decimal((unsigned)enum_result);
            put_text(" callbacks=");
            put_decimal(g_all_count);
            put_text(" cookie_ok=");
            put_decimal((unsigned)g_cookie_ok);
            put_text(" probe_seen=");
            put_decimal((unsigned)g_probe_seen);
            put_newline();
            if (!enum_result || g_all_count == 0 || !g_cookie_ok ||
                !g_probe_seen)
                failures = 1;

            g_stop_mode = 1;
            g_stop_count = 0;
            put_text("EnumWindows stop-on-first begin\r\n");
            enum_result = EnumWindows((WNDENUMPROC)thunk,
                                      (LPARAM)CALLBACK_COOKIE);
            put_text("EnumWindows stop result=");
            put_decimal((unsigned)enum_result);
            put_text(" callbacks=");
            put_decimal(g_stop_count);
            put_newline();
            if (enum_result || g_stop_count != 1)
                failures = 1;

            FreeProcInstance(thunk);
        }
        DestroyWindow(g_probe_window);
    }

    put_text(failures ? "RESULT=FAIL\r\n" : "RESULT=PASS\r\n");
    _lclose(g_log);
    g_log = (HFILE)-1;
    /* This one-shot startup probe should leave Windows and return to DOS. */
    ExitWindows(0L, 0);
    return failures ? 1 : 0;
}
