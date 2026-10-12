/* MIT, Copyright (c) 2026 Windows XT contributors.
 * Private native qualification helper, never a runtime ZIP member.
 * Observe display caps, yield briefly, then request normal Windows exit.
 * No callbacks, window automation, proprietary patches or forced shutdown.
 */
#define WINVER 0x0300
#include <windows.h>
#include <stdio.h>

int PASCAL WinMain(HANDLE instance, HANDLE previous, LPSTR command, int show)
{
    FILE *log;
    HDC dc;
    DWORD started;
    DWORD version;
    MSG message;
    int width;
    int height;
    int colors;
    (void)instance;
    (void)previous;
    (void)command;
    (void)show;
    width = GetSystemMetrics(SM_CXSCREEN);
    height = GetSystemMetrics(SM_CYSCREEN);
    dc = GetDC((HWND)0);
    colors = dc ? GetDeviceCaps(dc, NUMCOLORS) : -1;
    if (dc)
        ReleaseDC((HWND)0, dc);
    log = fopen("C:\\JREXIT.LOG", "a");
    if (!log)
        return 2;
    version = GetVersion();
    fprintf(log, "WINDOWS_VERSION=%u.%u\n", (unsigned)(version & 255L),
        (unsigned)((version >> 8) & 255L));
    fprintf(log, "WINDOWS_ENTERED width=%d height=%d colors=%d\n",
        width, height, colors);
    fprintf(log, "NORMAL_EXIT_REQUESTED=1\n");
    fclose(log);
    started = GetTickCount();
    while ((DWORD)(GetTickCount() - started) < 3000L) {
        if (PeekMessage(&message, (HWND)0, 0, 0, PM_REMOVE)) {
            TranslateMessage(&message);
            DispatchMessage(&message);
        } else {
            Yield();
        }
    }
    if (!ExitWindows(0L, 0)) {
        log = fopen("C:\\JREXIT.LOG", "a");
        if (log) {
            fprintf(log, "EXIT_REFUSED=1\n");
            fclose(log);
        }
        return 1;
    }
    return 0;
}
