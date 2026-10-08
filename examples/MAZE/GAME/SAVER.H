/*
 * SAVER.H - MAZE.EXE /S, the TSHELL screen saver, plus its diagnostics.
 *
 * The lifecycle is carried over unchanged from the previous Maze saver
 * (examples/MAZE/SAVER10, itself adapted from Matrix): TSHELL owns idle
 * timing; /S owns only its own input queue, drains held or repeated wake
 * input before closing, stops on any loss of activation, focus, capture
 * or screen ownership, and returns focus only while it still owns it.
 * No global hook, no password lock.
 *
 * What changed is drawing: the old raw B800 path (which only recognised
 * the pre-WINXT driver names) is gone. The saver draws the game's view
 * through GDI like any other window, walking the maze with its right
 * hand on the wall, a new maze at each exit.
 *
 * Diagnostics (disposable test sessions only; they write MAZE.LOG beside
 * the executable): /A lifecycle self-test, /I external input
 * observation, /B timed benchmark. /S is the saver.
 */
static HINSTANCE instance;
static HWND saver, qa, overlay;
static HWND previousActive, previousFocus;
static int saverMode, draining, returnFocus, mouseHeld, mouseGesture;
static BYTE initialKeys[256], downKeys[256];
static DWORD armStarted, lastInput;
static char wakeReason[40];
static HCURSOR previousCursor;
static HDC screenDC;
static int screenW, screenH, colors;
static int srunning, hidden, closing, testing, qaMode, testStep;
static int testFrames, activated, recovering, qaDrainStage;
static DWORD started, firstTick, drawMs, maxDraw, freeWarm, startup;
static DWORD restoreMs;
static unsigned long sticks, sframes;
static POINT origin;
static char logpath[144], driver[128], why[40];
static HGLOBAL snapshot;
static unsigned char FAR *snap;
static int svx, svy, pace;

static void logtext(char *s)
{
    HFILE f = _lopen(logpath, OF_WRITE);
    if (f == HFILE_ERROR) f = _lcreat(logpath, 0);
    if (f != HFILE_ERROR) {
        _llseek(f, 0L, 2);
        _lwrite(f, s, lstrlen(s));
        _lclose(f);
    }
}

static void detect(void)
{
    HDC dc;
    HMODULE mod;
    screenW = GetSystemMetrics(SM_CXSCREEN);
    screenH = GetSystemMetrics(SM_CYSCREEN);
    dc = GetDC(NULL);
    colors = dc ? GetDeviceCaps(dc, NUMCOLORS) : 0;
    if (dc) ReleaseDC(NULL, dc);
    mod = GetModuleHandle("DISPLAY");
    driver[0] = 0;
    if (mod) GetModuleFileName(mod, driver, sizeof(driver));
}

/* The saver draws only while it is the active, focused, capturing,
   topmost visible window. */
static int ownsScreen(void)
{
    HWND w;
    RECT r;
    if (GetActiveWindow() != saver) return 0;
    if (saverMode && (GetCapture() != saver || GetFocus() != saver)) return 0;
    for (w = GetWindow(saver, GW_HWNDPREV); w; w = GetWindow(w, GW_HWNDPREV))
        if (IsWindowVisible(w) && !IsIconic(w)) {
            GetWindowRect(w, &r);
            if (r.right > 0 && r.bottom > 0 && r.left < screenW &&
                r.top < screenH) return 0;
        }
    return 1;
}

/* One step of the walk and one frame. Each frame returns to GetMessage,
   so input, activation and shutdown always come first. */
static void saverframe(int full)
{
    DWORD t = GetTickCount();
    if (!srunning || !ownsScreen()) return;
    if (full) PatBlt(screenDC, 0, 0, screenW, screenH, BLACKNESS);
    else {
        autopilot();
        if (gev & EV_EXIT) newlevel(level < 12 ? level + 1 : 12);
        gev = 0;
    }
    if (!ownsScreen()) return;
    viewrender();
    if (!ownsScreen()) return;
    viewshow(screenDC, svx, svy);
    ++sframes;
    t = GetTickCount() - t;
    drawMs += t;
    if (t > maxDraw) maxDraw = t;
}

static void stop(HWND w, char *reason)
{
    char b[320];
    int focusBack = saverMode && returnFocus && GetActiveWindow() == w;
    DWORD elapsed = firstTick ? GetTickCount() - firstTick : 0UL;
    if (closing) return;
    closing = 1; srunning = 0; draining = 0;
    lstrcpy(why, reason);
    KillTimer(w, 1);
    if (saverMode && GetCapture() == w) ReleaseCapture();
    if (hidden) { SetCursor(previousCursor); ShowCursor(TRUE); hidden = 0; }
    if (testing) {
        wsprintf(b, "END reason=%s fast=0 gdi=%d width=%d colors=%d "
                 "ticks=%lu frames=%lu elapsed_ms=%lu draw_ms=%lu "
                 "max_draw_ms=%lu startup_ms=%lu restore_ms=%lu "
                 "free_warm=%lu free_end=%lu\r\n",
                 (LPSTR)why, gdipath, screenW, colors, sticks, sframes,
                 elapsed, drawMs, maxDraw, startup, restoreMs, freeWarm,
                 GetFreeSpace(0));
        logtext(b);
    }
    DestroyWindow(w);
    if (focusBack && IsWindow(previousActive) &&
        IsWindowVisible(previousActive) && IsWindowEnabled(previousActive)) {
        SetActiveWindow(previousActive);
        if (IsWindow(previousFocus) && IsWindowEnabled(previousFocus) &&
            (previousFocus == previousActive ||
             IsChild(previousActive, previousFocus)))
            SetFocus(previousFocus);
    }
}

static void beginWake(HWND w, char *reason)
{
    if (!saverMode) { stop(w, reason); return; }
    if (closing) return;
    if (!draining) {
        lstrcpy(wakeReason, reason);
        draining = 1; srunning = 0; returnFocus = 1;
        if (testing) logtext("DRAIN begin\r\n");
    }
    lastInput = GetTickCount();
}

static int keysHeld(void)
{
    int i;
    for (i = 3; i < 256; i++)
        if (i != VK_MBUTTON && downKeys[i]) {
            if (GetAsyncKeyState(i) & 0x8000) return 1;
            downKeys[i] = 0;
        }
    return 0;
}

static void noteMouse(UINT m, WPARAM wp)
{
    mouseHeld = wp & (MK_LBUTTON | MK_RBUTTON | MK_MBUTTON);
    if (m == WM_LBUTTONDOWN || m == WM_LBUTTONDBLCLK) mouseHeld |= MK_LBUTTON;
    if (m == WM_RBUTTONDOWN || m == WM_RBUTTONDBLCLK) mouseHeld |= MK_RBUTTON;
    if (m == WM_MBUTTONDOWN || m == WM_MBUTTONDBLCLK) mouseHeld |= MK_MBUTTON;
    if (m == WM_LBUTTONUP) mouseHeld &= ~MK_LBUTTON;
    if (m == WM_RBUTTONUP) mouseHeld &= ~MK_RBUTTON;
    if (m == WM_MBUTTONUP) mouseHeld &= ~MK_MBUTTON;
}

static int saverInput(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    int dx, dy, old;
    if (!saverMode) return 0;
    if (m >= WM_KEYFIRST && m <= WM_KEYLAST) {
        if (m == WM_KEYDOWN || m == WM_SYSKEYDOWN) {
            if (wp < 256) downKeys[wp] = 1;
            beginWake(w, "keyboard");
        } else if (m == WM_KEYUP || m == WM_SYSKEYUP) {
            old = wp < 256 ? initialKeys[wp] : 0;
            if (wp < 256) { downKeys[wp] = 0; initialKeys[wp] = 0; }
            /* Ignore only the release of a key already down when /S
               started, and only for 250 ms. New input always wakes. */
            if (!old || GetTickCount() - armStarted >= 250UL || draining)
                beginWake(w, "key-release");
        } else beginWake(w, "keyboard-char");
        return 1;
    }
    if (m >= WM_MOUSEFIRST && m <= WM_MOUSELAST) {
        if (m != WM_MOUSEMOVE) mouseGesture = 1;
        noteMouse(m, wp);
        dx = (int)LOWORD(lp) - origin.x;
        dy = (int)HIWORD(lp) - origin.y;
        if (m != WM_MOUSEMOVE || dx || dy)
            beginWake(w, m == WM_MOUSEMOVE ? "mouse-move" : "mouse-button");
        return 1;
    }
    return 0;
}

static void drainTick(HWND w)
{
    MSG msg;
    DWORD quiet = mouseGesture ? (DWORD)GetDoubleClickTime() : 110UL;
    if (quiet < 110UL) quiet = 110UL;
    if (GetActiveWindow() != w || GetCapture() != w || GetFocus() != w) {
        returnFocus = 0;
        stop(w, "drain-ownership-lost");
        return;
    }
    if (keysHeld() || mouseHeld) { lastInput = GetTickCount(); return; }
    /* Remove remaining own-window input without generating WM_CHAR or
       forwarding it anywhere. */
    while (PeekMessage(&msg, w, WM_KEYFIRST, WM_KEYLAST, PM_REMOVE))
        saverInput(w, msg.message, msg.wParam, msg.lParam);
    while (PeekMessage(&msg, w, WM_MOUSEFIRST, WM_MOUSELAST, PM_REMOVE))
        saverInput(w, msg.message, msg.wParam, msg.lParam);
    if (keysHeld() || mouseHeld || GetTickCount() - lastInput < quiet) return;
    if (testing) logtext("DRAIN released\r\n");
    stop(w, wakeReason);
}

static int initDraw(HWND w)
{
    TEXTMETRIC tm;
    int h, wd, want;
    long t;
    screenDC = GetDC(w);
    if (!screenDC) return 0;
    if (!ownsScreen()) return 0;
    SelectObject(screenDC, GetStockObject(SYSTEM_FIXED_FONT));
    GetTextMetrics(screenDC, &tm);
    want = viewheight(colors, GetDeviceCaps(screenDC, HORZRES),
                      GetDeviceCaps(screenDC, VERTRES));
    h = want & ~1;
    t = (long)h * 3 * GetDeviceCaps(screenDC, HORZRES) /
        (4L * GetDeviceCaps(screenDC, VERTRES));
    wd = (int)t & ~1;
    if (wd > screenW) wd = screenW & ~1;
    viewinit(screenDC, wd, h);
    svx = (screenW - vw) / 2;
    svy = (screenH - vh) / 2;
    pace = 0;
    (void)tm;
    return 1;
}

LONG FAR PASCAL SaverProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    PAINTSTRUCT ps;
    int dx, dy;
    if (saverInput(w, m, wp, lp)) return 0;
    switch (m) {
    case WM_CREATE: return 0;
    case WM_KILLFOCUS:
        if (srunning || draining) { returnFocus = 0; stop(w, "focus-lost"); }
        return 0;
    case WM_ACTIVATE:
        if (wp == WA_INACTIVE && (srunning || draining)) {
            returnFocus = 0; stop(w, "deactivated");
        } else if (wp != WA_INACTIVE) activated = 1;
        return 0;
    case WM_ACTIVATEAPP:
        if (!wp && (srunning || draining)) {
            returnFocus = 0;
            stop(w, "task-switch");
        }
        return 0;
    case WM_CANCELMODE:
        if (srunning || draining) { returnFocus = 0; stop(w, "cancel-mode"); }
        return 0;
    case WM_ERASEBKGND: return 1;
    case WM_SETCURSOR: SetCursor(NULL); return 1;
    case WM_PAINT:
        BeginPaint(w, &ps);
        EndPaint(w, &ps);
        if (srunning) saverframe(1);
        return 0;
    case WM_TIMER:
        if (wp != 1) return 0;
        if (draining) { drainTick(w); return 0; }
        if (!srunning) return 0;
        if (!ownsScreen()) { stop(w, "ownership-lost"); return 0; }
        if (!firstTick) {
            firstTick = GetTickCount();
            freeWarm = GetFreeSpace(0);
        }
        ++sticks;
        /* a step at most every four ticks, so fast machines stay calm */
        if (++pace >= 4) { pace = 0; saverframe(0); }
        if (qaMode && recovering) {
            recovering = 0;
            stop(w, "repaint-disruption");
            return 0;
        }
        if (qaMode && ++testFrames == 4) {
            PostMessage(qa, WM_USER + 2, 0, 0);
            return 0;
        }
        if (testing && !qaMode && sframes >= 40) {
            stop(w, "benchmark");
            return 0;
        }
        return 0;
    case WM_KEYDOWN: case WM_SYSKEYDOWN: case WM_CHAR:
        if (srunning) { stop(w, "keyboard"); return 0; }
        break;
    case WM_LBUTTONDOWN: case WM_RBUTTONDOWN: case WM_MBUTTONDOWN:
        if (srunning) { stop(w, "mouse-button"); return 0; }
        break;
    case WM_MOUSEMOVE:
        if (srunning) {
            dx = (int)LOWORD(lp) - origin.x;
            dy = (int)HIWORD(lp) - origin.y;
            if (dx > 2 || dx < -2 || dy > 2 || dy < -2) stop(w, "mouse-move");
        }
        return 0;
    case WM_QUERYENDSESSION: returnFocus = 0; stop(w, "shutdown"); return 1;
    case WM_ENDSESSION:
        if (wp || saverMode) {
            returnFocus = 0;
            stop(w, wp ? "shutdown" : "shutdown-cancelled");
        }
        return 0;
    case WM_CLOSE: returnFocus = 0; stop(w, "close"); return 0;
    case WM_DESTROY:
        srunning = draining = 0;
        KillTimer(w, 1);
        if (saverMode && GetCapture() == w) ReleaseCapture();
        if (hidden) { SetCursor(previousCursor); ShowCursor(TRUE); hidden = 0; }
        viewfree();
        if (screenDC) ReleaseDC(w, screenDC);
        screenDC = NULL; saver = NULL;
        if (qaMode) PostMessage(qa, WM_USER + 3, 0, 0);
        else PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(w, m, wp, lp);
}

static int startSaver(void)
{
    char b[220];
    int n;
    if (saverMode && (GetCapture() || GetSysModalWindow())) return 0;
    previousActive = GetActiveWindow();
    previousFocus = GetFocus();
    draining = returnFocus = mouseHeld = mouseGesture = 0;
    if (saverMode) {
        GetKeyboardState(initialKeys);
        for (n = 0; n < 256; n++) {
            initialKeys[n] &= 0x80;
            downKeys[n] = (BYTE)(initialKeys[n] ? 1 : 0);
        }
        if (initialKeys[VK_LBUTTON]) mouseHeld |= MK_LBUTTON;
        if (initialKeys[VK_RBUTTON]) mouseHeld |= MK_RBUTTON;
        if (initialKeys[VK_MBUTTON]) mouseHeld |= MK_MBUTTON;
        GetCursorPos(&origin);
        armStarted = GetTickCount();
    }
    previousCursor = SetCursor(NULL);
    SetCursor(previousCursor);
    srunning = hidden = closing = 0;
    activated = 0;
    firstTick = drawMs = maxDraw = restoreMs = 0;
    sticks = sframes = 0;
    testFrames = 0;
    started = GetTickCount();
    newgame(GetTickCount() ^ 0x2B3DUL);
    gev = 0;
    saver = CreateWindow("TandyMazeSaver", "Maze", WS_POPUP, 0, 0,
                         screenW, screenH, NULL, NULL, instance, NULL);
    if (!saver) return 0;
    if (saverMode && (GetCapture() || GetSysModalWindow() ||
                      GetActiveWindow() != previousActive)) {
        stop(saver, "startup-owner-changed");
        return 0;
    }
    ShowWindow(saver, SW_SHOW);
    SetActiveWindow(saver);
    if (saverMode) {
        if (GetCapture() || GetSysModalWindow() || GetActiveWindow() != saver) {
            stop(saver, "startup-owner-changed");
            return 0;
        }
        SetFocus(saver);
        SetCapture(saver);
        if (GetCapture() != saver || GetActiveWindow() != saver) {
            stop(saver, "activation-failed");
            return 0;
        }
    }
    UpdateWindow(saver);
    if (!saverMode) GetCursorPos(&origin);
    ScreenToClient(saver, &origin);
    if (closing || !IsWindow(saver)) return 0;
    if (!ownsScreen()) {
        returnFocus = 0;
        stop(saver, "startup-ownership-lost");
        return 0;
    }
    if (!initDraw(saver)) { stop(saver, "allocation-failed"); return 0; }
    ShowCursor(FALSE);
    hidden = 1;
    SetCursor(NULL);
    if (!draining) { srunning = 1; saverframe(1); }
    startup = GetTickCount() - started;
    /* The first full-screen paint can take seconds on an 8088: start the
       250 ms grace for keys held at launch when input is read again. */
    armStarted = GetTickCount();
    if (!SetTimer(saver, 1, 55, NULL)) {
        stop(saver, "timer-failed");
        return 0;
    }
    if (testing) {
        wsprintf(b, "START driver=%s fast=0 gdi=%d width=%d colors=%d\r\n",
                 (LPSTR)driver, gdipath, screenW, colors);
        logtext(b);
    }
    return 1;
}

/* QA: sample the screen through GDI every 8 pixels. */
static unsigned compareScreen(int save)
{
    int y, x, n = 0;
    HDC dc;
    COLORREF color;
    DWORD FAR *samples;
    unsigned bad = 0;
    if (!snap) return 65535U;
    samples = (DWORD FAR *)snap;
    dc = GetDC(qa);
    if (!dc) return 65535U;
    for (y = 0; y < 200; y += 8)
        for (x = 0; x < screenW; x += 8) {
            color = GetPixel(dc, x, y);
            if (save) samples[n] = color;
            else if (samples[n] != color) bad++;
            n++;
        }
    ReleaseDC(qa, dc);
    return bad;
}

LONG FAR PASCAL QaProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    HDC dc;
    PAINTSTRUCT ps;
    RECT r;
    char b[160];
    unsigned bad;
    switch (m) {
    case WM_ERASEBKGND: return 1;
    case WM_SETCURSOR: SetCursor(NULL); return 1;
    case WM_PAINT:
        dc = BeginPaint(w, &ps);
        GetClientRect(w, &r);
        FillRect(dc, &r, GetStockObject(WHITE_BRUSH));
        SetBkMode(dc, TRANSPARENT);
        TextOut(dc, 4, 4, "DESKTOP RESTORED", 16);
        MoveTo(dc, 0, 80);
        LineTo(dc, screenW, 80);
        EndPaint(w, &ps);
        return 0;
    case WM_USER + 1:
        UpdateWindow(w);
        compareScreen(1);
        if (!startSaver()) { logtext("QA start failed\r\n"); DestroyWindow(w); }
        return 0;
    case WM_USER + 2:
        if (qaMode == 2) return 0;
        if (testStep == 0) {
            SendMessage(saver, WM_KEYDOWN, VK_ESCAPE, 0L);
            if (saverMode) {
                SendMessage(saver, WM_CHAR, 27, 0L);
                SendMessage(saver, WM_KEYUP, VK_ESCAPE, 0L);
            }
        } else if (testStep == 1) {
            SendMessage(saver, WM_LBUTTONDOWN, MK_LBUTTON, 0L);
            if (saverMode) SendMessage(saver, WM_LBUTTONUP, 0, 0L);
        } else if (testStep == 2)
            SendMessage(saver, WM_MOUSEMOVE, 0,
                        MAKELONG((origin.x + (saverMode ? 1 : 20)) % screenW,
                                 (origin.y + (saverMode ? 0 : 20)) % 200));
        else if (testStep == 3) SetActiveWindow(w);
        else if (testStep == 4) SendMessage(saver, WM_CLOSE, 0, 0L);
        else if (testStep == 5) {
            SendMessage(saver, WM_SYSKEYDOWN, VK_MENU, 0L);
            if (saverMode) {
                SendMessage(saver, WM_SYSCHAR, 'x', 0L);
                SendMessage(saver, WM_SYSKEYUP, VK_MENU, 0L);
            }
        } else if (testStep == 6) SendMessage(saver, WM_CANCELMODE, 0, 0L);
        else if (testStep == 7) SendMessage(saver, WM_QUERYENDSESSION, 0, 0L);
        else if (testStep == 8) SendMessage(saver, WM_ACTIVATEAPP, 0, 0L);
        else if (testStep == 9) {
            recovering = 1;
            dc = GetDC(NULL);
            BitBlt(dc, 0, 0, 1, 1, dc, 0, 0, SRCCOPY);
            ReleaseDC(NULL, dc);
        } else if (testStep == 10) {
            overlay = CreateWindow("STATIC", "", WS_POPUP | SS_BLACKRECT,
                                   8, 8, 8, 8, NULL, NULL, instance, NULL);
            ShowWindow(overlay, SW_SHOWNOACTIVATE);
        } else if (testStep == 11) {
            SendMessage(saver, WM_KEYDOWN, VK_RETURN, 0L);
            SendMessage(saver, WM_ENDSESSION, FALSE, 0L);
        } else if (testStep == 12) {
            qaDrainStage = 0;
            SendMessage(saver, WM_LBUTTONDOWN, MK_LBUTTON, 0L);
            SetTimer(w, 3, 440, NULL);
        } else if (testStep == 13) {
            SendMessage(saver, WM_MOUSEMOVE, 0, MAKELONG(origin.x, origin.y));
            logtext(draining ? "SYNTHETIC FAIL\r\n" : "SYNTHETIC PASS\r\n");
            SendMessage(saver, WM_KEYUP, VK_F1, 0L);
        } else if (testStep == 14) SetCapture(w);
        else if (testStep == 15) SetFocus(w);
        return 0;
    case WM_TIMER:
        if (wp == 5) {
            KillTimer(w, 5);
            logtext("INPUT OBSERVATION DONE\r\n");
            DestroyWindow(w);
            return 0;
        }
        if (wp == 3) {
            KillTimer(w, 3);
            logtext(IsWindow(saver) && draining && GetCapture() == saver ?
                    "HELD MOUSE PASS\r\n" : "HELD MOUSE FAIL\r\n");
            if (!qaDrainStage++) {
                SendMessage(saver, WM_LBUTTONUP, 0, 0L);
                SendMessage(saver, WM_LBUTTONDOWN, MK_LBUTTON, 0L);
                SetTimer(w, 3, 440, NULL);
            } else SendMessage(saver, WM_LBUTTONUP, 0, 0L);
        }
        return 0;
    case WM_USER + 3:
        if (saverMode && testStep == 14) {
            logtext(GetCapture() == w ? "CAPTURE THEFT PASS\r\n" :
                                        "CAPTURE THEFT FAIL\r\n");
            if (GetCapture() == w) ReleaseCapture();
        }
        if (overlay) { DestroyWindow(overlay); overlay = NULL; }
        UpdateWindow(w);
        bad = compareScreen(0);
        wsprintf(b, "QA step=%d changed_units=%u active_ok=%d raw=0 "
                 "capture_released=%d\r\n", testStep, bad,
                 GetActiveWindow() == w, GetCapture() == NULL);
        logtext(b);
        if (qaMode == 2) { SetTimer(w, 5, 1500, NULL); return 0; }
        if (++testStep < (saverMode ? 16 : 11))
            PostMessage(w, WM_USER + 1, 0, 0L);
        else { logtext("QA DONE\r\n"); DestroyWindow(w); }
        return 0;
    case WM_KEYDOWN: case WM_KEYUP: case WM_SYSKEYDOWN: case WM_SYSKEYUP:
    case WM_CHAR: case WM_LBUTTONDOWN: case WM_LBUTTONUP: case WM_LBUTTONDBLCLK:
        logtext("INPUT LEAK\r\n");
        return 0;
    case WM_DESTROY:
        if (snap) GlobalUnlock(snapshot);
        if (snapshot) GlobalFree(snapshot);
        ShowCursor(TRUE);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(w, m, wp, lp);
}

static int SaverMain(HINSTANCE inst, HINSTANCE prev, LPSTR cmd, int show)
{
    WNDCLASS wc;
    MSG msg;
    int i, n;
    HFILE f;
    char c = cmd[1];
    instance = inst;
    saverMode = c == 'S' || c == 's' || c == 'A' || c == 'a' ||
                c == 'B' || c == 'b' || c == 'I' || c == 'i';
    if (!saverMode) return 9;
    if (prev || FindWindow("TandyMaze", NULL) ||
        FindWindow("TandyMazeSaver", NULL))
        return 8;
    testing = c == 'A' || c == 'a' || c == 'B' || c == 'b' ||
              c == 'I' || c == 'i';
    qaMode = (c == 'A' || c == 'a') ? 1 : (c == 'I' || c == 'i') ? 2 : 0;
    GetModuleFileName(inst, logpath, sizeof(logpath));
    n = lstrlen(logpath);
    for (i = n - 1; i >= 0 && logpath[i] != '\\' && logpath[i] != ':'; i--) ;
    logpath[i + 1] = 0;
    lstrcat(logpath, "MAZE.LOG");
    if (testing) { f = _lcreat(logpath, 0); if (f != HFILE_ERROR) _lclose(f); }
    detect();
    if (screenH != 200 ||
        (screenW != 160 && screenW != 320 && screenW != 640)) {
        MessageBox(NULL, "Needs a 160, 320 or 640 by 200 display.",
                   "Maze", MB_OK);
        return 1;
    }
    sound = 0;                          /* the saver is silent           */
    saverhud = 1;
    wc.style = 0;
    wc.lpfnWndProc = SaverProc;
    wc.cbClsExtra = wc.cbWndExtra = 0;
    wc.hInstance = inst;
    wc.hIcon = NULL;
    wc.hCursor = NULL;
    wc.hbrBackground = NULL;
    wc.lpszMenuName = NULL;
    wc.lpszClassName = "TandyMazeSaver";
    if (!RegisterClass(&wc)) return 4;
    wc.lpfnWndProc = QaProc;
    wc.lpszClassName = "MazeQA";
    if (!RegisterClass(&wc)) return 4;
    if (qaMode) {
        snapshot = GlobalAlloc(GMEM_MOVEABLE, 32768UL);
        if (!snapshot) return 5;
        snap = (unsigned char FAR *)GlobalLock(snapshot);
        if (!snap) { GlobalFree(snapshot); return 5; }
        ShowCursor(FALSE);
        qa = CreateWindow("MazeQA", "Maze QA", WS_POPUP, 0, 0, screenW,
                          screenH, NULL, NULL, inst, NULL);
        if (!qa) {
            ShowCursor(TRUE);
            GlobalUnlock(snapshot);
            GlobalFree(snapshot);
            return 6;
        }
        ShowWindow(qa, SW_SHOW);
        UpdateWindow(qa);
        PostMessage(qa, WM_USER + 1, 0, 0L);
    } else if (!startSaver()) return 7;
    while (GetMessage(&msg, NULL, 0, 0)) DispatchMessage(&msg);
    if (testing) logtext("QUIT clean\r\n");
    (void)show;
    return (int)msg.wParam;
}
