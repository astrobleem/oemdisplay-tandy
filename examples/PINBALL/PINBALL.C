/*
 * PINBALL.C - Tandy Pinball for Windows 3.0 real mode on an 8088.
 *
 * A: left flipper   L: right flipper   Space: hold to pull the plunger,
 * release to shoot (also starts a game)   P: pause   S: sound on/off
 *
 * The table scales to any display mode, keeping it the right shape on a
 * 4:3 monitor. The static table lives in a bitmap; the ball, flippers and
 * plunger are drawn with XOR so moving them never redraws the table.
 */
#define WINVER 0x0300
#include <windows.h>
#include <conio.h>
#pragma intrinsic(outp)
#include "PHYSICS.H"

/* ---- layout: table units to pixels ------------------------------------ */
static int ox, oy;                  /* table origin in client pixels     */
static long kx, ky;                 /* pixels per Q6 unit, 16.16         */
static int cw, ch, cx, cy;          /* client size, character cell       */
static int tw, th;                  /* table size in pixels              */
static int side;                    /* 1: info panel on the right        */
static int px0, py0;                /* panel origin                      */
static int ballrx, ballry;          /* ball half-size in pixels          */

static int SX(int q) { return ox + (int)(((long)q * kx) >> 16); }
static int SY(int q) { return oy + (int)(((long)q * ky) >> 16); }
#define UX(u) SX((u) * Q)
#define UY(u) SY((u) * Q)

static void layout(HDC d)
{
    TEXTMETRIC tm;
    int hres = GetDeviceCaps(d, HORZRES), vres = GetDeviceCaps(d, VERTRES);
    long num = 160L * 3 * hres, den = 244L * 4 * vres;

    GetTextMetrics(d, &tm);
    cx = tm.tmAveCharWidth; cy = tm.tmHeight;

    /* A table unit is square on a 4:3 monitor: width follows height. */
    th = ch - 2;
    tw = (int)(th * num / den);
    side = (cw - tw - 4) >= 13 * cx;
    if (side) {
        ox = 1; oy = 1;
        px0 = tw + 4; py0 = 1;
    } else {
        int top = 2 * cy + 2;
        th = ch - top - 1;
        tw = (int)(th * num / den);
        if (tw > cw - 2) {
            tw = cw - 2;
            th = (int)(tw * den / num);
        }
        ox = (cw - tw) / 2; oy = top;
        px0 = 1; py0 = 1;
    }
    kx = ((long)tw << 16) / (TABLE_W * Q);
    ky = ((long)th << 16) / (TABLE_H * Q);
    ballrx = (int)((BALL_R * Q * kx) >> 16);
    ballry = (int)((BALL_R * Q * ky) >> 16);
    if (ballrx < 1) ballrx = 1;
    if (ballry < 1) ballry = 1;
}

/* ---- static table ------------------------------------------------------ */
static void line(HDC d, int x1, int y1, int x2, int y2)
{
    MoveTo(d, x1, y1);
    LineTo(d, x2, y2);
    SetPixel(d, x2, y2, RGB(255, 255, 255));    /* LineTo skips the end */
}

static void lights(HDC d)
{
    int i;
    for (i = 0; i < 3; ++i) {
        int l = UX(lanex[i] - 3), r = UX(lanex[i] + 3) + 1;
        int t = UY(43), b = UY(47) + 1;
        PatBlt(d, l, t, r - l, b - t, BLACKNESS);
        if (lanes & (1 << i)) PatBlt(d, l, t, r - l, b - t, WHITENESS);
        else Rectangle(d, l, t, r, b);
    }
}

static void dropbank(HDC d)
{
    int i, x = UX(134);
    PatBlt(d, x - 1, UY(104), 3, UY(133) - UY(104) + 1, BLACKNESS);
    for (i = 0; i < 3; ++i) {
        if (targets & (1 << i)) continue;
        line(d, x, UY(104 + 10 * i), x, UY(113 + 10 * i));
        line(d, x - 1, UY(104 + 10 * i), x - 1, UY(113 + 10 * i));
    }
    line(d, x, UY(104), UX(144), UY(98));
    line(d, x, UY(133), UX(144), UY(141));
}

static void table(HDC d)
{
    int i;
    SelectObject(d, GetStockObject(WHITE_PEN));
    SelectObject(d, GetStockObject(NULL_BRUSH));
    for (i = 0; i < NSEGS; ++i) {
        const TSEG *s = &segs[i];
        if (s->kind == K_TARGET) continue;
        if (s->ay == 236 && s->by == 236) continue;   /* plunger: dynamic */
        line(d, UX(s->ax), UY(s->ay), UX(s->bx), UY(s->by));
    }
    for (i = 0; i < 3; ++i) {
        Ellipse(d, UX(bumpx[i] - BUMP_R), UY(bumpy[i] - BUMP_R),
                UX(bumpx[i] + BUMP_R) + 1, UY(bumpy[i] + BUMP_R) + 1);
        Ellipse(d, UX(bumpx[i] - 4), UY(bumpy[i] - 4),
                UX(bumpx[i] + 4) + 1, UY(bumpy[i] + 4) + 1);
    }
    lights(d);
    dropbank(d);
}

/* Bitmap cache of the static table. If it can't be allocated, the table
   is drawn directly, which is slower but correct. */
static HDC board;
static HBITMAP boardbits, oldbits;

static void freeboard(void)
{
    if (!board) return;
    SelectObject(board, oldbits);
    DeleteDC(board);
    DeleteObject(boardbits);
    board = NULL;
}

static void cache(HDC d)
{
    if (board) return;
    board = CreateCompatibleDC(d);
    if (!board) return;
    boardbits = CreateCompatibleBitmap(d, cw, ch);
    if (!boardbits) { DeleteDC(board); board = NULL; return; }
    oldbits = SelectObject(board, boardbits);
    PatBlt(board, 0, 0, cw, ch, BLACKNESS);
    table(board);
}

/* ---- XOR-drawn moving parts -------------------------------------------- */
typedef struct {
    int on;
    int bx, by;                     /* ball centre, pixels               */
    int lx, ly, rx, ry;             /* flipper tips, pixels              */
    int py;                         /* plunger tip, pixels               */
} DYN;
static DYN shown;                   /* what is on screen now             */

static void current(DYN *p)
{
    int tx, ty;
    p->on = 1;
    p->bx = SX(bx); p->by = SY(by);
    if (state == ST_OVER) p->bx = -1000;    /* no ball between games    */
    fliptip(1, &tx, &ty); p->lx = SX(tx); p->ly = SY(ty);
    fliptip(0, &tx, &ty); p->rx = SX(tx); p->ry = SY(ty);
    p->py = UY(236) + (int)(((long)charge * 6 * Q * ky / CHARGE_MAX) >> 16);
    if (charge < 0) p->py = UY(236);
}

static void xball(HDC d, DYN *p)
{
    if (p->bx < 0) return;
    PatBlt(d, p->bx - ballrx, p->by - ballry,
           2 * ballrx + 1, 2 * ballry + 1, DSTINVERT);
}

static void xflip(HDC d, int x0, int y0, int x1, int y1)
{
    MoveTo(d, x0, y0); LineTo(d, x1, y1);
    MoveTo(d, x0, y0 + 1); LineTo(d, x1, y1 + 1);
}

static void xflippers(HDC d, DYN *p)
{
    xflip(d, UX(LPIV_X), UY(PIV_Y), p->lx, p->ly);
    xflip(d, UX(RPIV_X), UY(PIV_Y), p->rx, p->ry);
}

static void xplunger(HDC d, DYN *p)
{
    MoveTo(d, UX(146), p->py); LineTo(d, UX(155), p->py);
    MoveTo(d, UX(150), p->py + 1); LineTo(d, UX(150), UY(244));
}

static void xall(HDC d, DYN *p)
{
    xball(d, p); xflippers(d, p); xplunger(d, p);
}

static void xbegin(HDC d)
{
    SetROP2(d, R2_NOT);
    SelectObject(d, GetStockObject(WHITE_PEN));
}

/* Move the parts on screen from 'shown' to the current state. */
static void update(HDC d)
{
    DYN n;
    current(&n);
    xbegin(d);
    if (!shown.on) { xall(d, &n); shown = n; return; }
    if (n.bx != shown.bx || n.by != shown.by) {
        xball(d, &shown); xball(d, &n);
    }
    if (n.lx != shown.lx || n.ly != shown.ly ||
        n.rx != shown.rx || n.ry != shown.ry) {
        xflippers(d, &shown); xflippers(d, &n);
    }
    if (n.py != shown.py) { xplunger(d, &shown); xplunger(d, &n); }
    shown = n;
}

/* Redraw changed static parts (lights, targets) under the moving ones. */
static void refresh(HDC d)
{
    xbegin(d);
    if (shown.on) xall(d, &shown);
    SetROP2(d, R2_COPYPEN);
    if (board) {
        lights(board); dropbank(board);
        BitBlt(d, ox, oy, tw + 1, th + 1, board, ox, oy, SRCCOPY);
    } else {
        SelectObject(d, GetStockObject(NULL_BRUSH));
        lights(d); dropbank(d);
    }
    xbegin(d);
    if (shown.on) xall(d, &shown);
    SetROP2(d, R2_COPYPEN);
}

/* ---- info panel -------------------------------------------------------- */
static int paused, msgt, msgver, sound = 1, soundok;
static char msg[24];

static void say(char *s, int t) { lstrcpy(msg, s); msgt = t; ++msgver; }

static void text(HDC d, int row, char *s)
{
    RECT r;
    int x = px0, y = py0 + row * cy;
    if (side) { r.left = x; r.right = cw; }
    else { r.left = 0; r.right = cw; }
    r.top = y; r.bottom = y + cy;
    ExtTextOut(d, x, y, ETO_OPAQUE, &r, s, lstrlen(s), NULL);
}

static void panel(HDC d)
{
    char s[40];
    char *m = msg;

    SetTextColor(d, RGB(255, 255, 255));
    SetBkColor(d, RGB(0, 0, 0));
    if (paused) m = "PAUSED - P";
    else if (!msgt) {
        if (state == ST_OVER) m = "SPACE: NEW GAME";
        else if (state == ST_LANE) m = "HOLD SPACE";
        else m = "";
    }
    if (!side) {
        if (state == ST_OVER && score == 0) wsprintf(s, "HIGH %ld", best);
        else wsprintf(s, "%ld  BALL %d", score, ballnum);
        text(d, 0, s);
        text(d, 1, m);
        return;
    }
    text(d, 0, "TANDY PINBALL");
    text(d, 2, "SCORE");
    wsprintf(s, "%ld", score); text(d, 3, s);
    if (state == ST_OVER) lstrcpy(s, "GAME OVER");
    else wsprintf(s, "BALL %d OF %d", ballnum, BALLS_PER_GAME);
    text(d, 4, s);
    wsprintf(s, "HIGH %ld", best); text(d, 6, s);
    wsprintf(s, "BONUS %d  X%d", bonus, mult); text(d, 7, s);
    text(d, 9, m);
    text(d, 11, "A     LEFT");
    text(d, 12, "L     RIGHT");
    text(d, 13, "SPACE PLUNGER");
    text(d, 14, sound && soundok ? "P PAUSE  S SOUND" : "P PAUSE");
}

/* ---- sound: Tandy PSG, guarded ----------------------------------------- */
/* Direct PSG writes only in real mode, only with the Tandy ROM signature,
   and only while this app holds the Windows sound device, so it never
   talks over another sound user. Every exit path mutes all channels. */
static int voicet[4];
#define PSG 0xC0

static void psgmute(void)
{
    int i;
    for (i = 0; i < 4; ++i) outp(PSG, 0x9F | (i << 5));
    voicet[0] = voicet[1] = voicet[2] = voicet[3] = 0;
}

static void tone(int ch, int hz, int ticks)
{
    unsigned div;
    if (!soundok || !sound) return;
    div = (unsigned)(111861L / hz);
    if (div > 1023) div = 1023;
    outp(PSG, 0x80 | (ch << 5) | (div & 15));
    outp(PSG, (div >> 4) & 63);
    outp(PSG, 0x90 | (ch << 5) | 2);
    voicet[ch] = ticks;
}

static void noise(int ticks)
{
    if (!soundok || !sound) return;
    outp(PSG, 0xE5);                    /* white noise, middle rate      */
    outp(PSG, 0xF4);
    voicet[3] = ticks;
}

static int dropt;                       /* falling drain tone            */

static void sounds(unsigned ev)
{
    int i;
    for (i = 0; i < 4; ++i)
        if (voicet[i] && --voicet[i] == 0 && soundok)
            outp(PSG, 0x9F | (i << 5));
    if (dropt) {
        --dropt;
        tone(2, 220 + dropt * 40, 1);
    }
    if (ev & EV_FLIP) noise(1);
    if (ev & EV_LAUNCH) noise(2);
    if (ev & EV_SLING) tone(1, 660, 1);
    if (ev & EV_BUMPER) tone(0, 1175, 1);
    if (ev & EV_TARGET) tone(1, 392, 2);
    if (ev & EV_LANE && lanes) tone(0, 1568, 2);
    if (ev & EV_MULT) tone(0, 2093, 4);
    if (ev & EV_SAVE) tone(0, 880, 3);
    if (ev & EV_DRAIN) dropt = 8;
}

static int tandypsg(void)
{
    unsigned char far *sig = (unsigned char far *)0xF000C000L;
    if (GetWinFlags() & WF_PMODE) return 0;
    return *sig == 0x21;
}

/* ---- window ------------------------------------------------------------ */
static void repaint(HWND w)
{
    HDC d = GetDC(w);
    cache(d);
    if (board) BitBlt(d, 0, 0, cw, ch, board, 0, 0, SRCCOPY);
    else { PatBlt(d, 0, 0, cw, ch, BLACKNESS); table(d); }
    SelectObject(d, GetStockObject(SYSTEM_FIXED_FONT));
    panel(d);
    shown.on = 0;
    update(d);
    ReleaseDC(w, d);
}

static void pause(HWND w, int on)
{
    HDC d;
    paused = on;
    leftkey = rightkey = 0;
    if (plungekey) setplunger(0);
    if (soundok) psgmute();
    d = GetDC(w);
    SelectObject(d, GetStockObject(SYSTEM_FIXED_FONT));
    panel(d);
    ReleaseDC(w, d);
}

LONG FAR PASCAL WndProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    PAINTSTRUCT ps;
    HDC d;
    unsigned ev;
    static long pscore = -1;
    static int pball, pstate, pbonus, pmult, pmsg, pver;

    switch (m) {
    case WM_CREATE:
        reset();
        soundok = tandypsg() && OpenSound() > 0;
        if (soundok) psgmute();
        if (!SetTimer(w, 1, 55, NULL)) return -1L;
        return 0;

    case WM_SIZE:
        cw = LOWORD(lp); ch = HIWORD(lp);
        freeboard();
        d = GetDC(w);
        SelectObject(d, GetStockObject(SYSTEM_FIXED_FONT));
        layout(d);
        ReleaseDC(w, d);
        InvalidateRect(w, NULL, FALSE);
        return 0;

    case WM_ERASEBKGND:
        return 1L;

    case WM_PAINT:
        /* Always repaint everything so the XOR parts stay consistent. */
        BeginPaint(w, &ps);
        EndPaint(w, &ps);
        repaint(w);
        return 0;

    case WM_KEYDOWN:
        if (paused && wp != 'P') return 0;
        if (wp == 'A') setflip(1, 1);
        else if (wp == 'L') setflip(0, 1);
        else if (wp == VK_SPACE) setplunger(1);
        else if (wp == 'P' && !(lp & 0x40000000L)) pause(w, !paused);
        else if (wp == 'S' && !(lp & 0x40000000L) && soundok) {
            sound = !sound;
            psgmute();
            pscore = -1;                /* redraw the panel             */
        }
        return 0;

    case WM_KEYUP:
        if (wp == 'A') setflip(1, 0);
        else if (wp == 'L') setflip(0, 0);
        else if (wp == VK_SPACE) setplunger(0);
        return 0;

    case WM_KILLFOCUS:
        if (!paused) pause(w, 1);
        return 0;

    case WM_SETCURSOR:
        if (LOWORD(lp) == HTCLIENT) { SetCursor(NULL); return 1L; }
        break;

    case WM_TIMER:
        if (paused || IsIconic(w) || !cw) return 0;
        ev = tick();
        if (ev & EV_SAVE) say("BALL SAVED", 36);
        if (ev & EV_MULT) {
            static char mm[] = "MULTIPLIER X0";
            mm[12] = (char)('0' + mult);
            say(mm, 36);
        }
        if ((ev & EV_DRAIN) && lastbonus > 0) {
            static char bm[24];
            wsprintf(bm, "BONUS %ld", lastbonus);
            say(bm, 45);
        }
        if (msgt) --msgt;
        sounds(ev);
        d = GetDC(w);
        if (ev & (EV_LANE | EV_TARGET)) refresh(d);
        update(d);
        if (score != pscore || ballnum != pball || state != pstate ||
            bonus != pbonus || mult != pmult || (msgt != 0) != pmsg ||
            msgver != pver) {
            SelectObject(d, GetStockObject(SYSTEM_FIXED_FONT));
            SetROP2(d, R2_COPYPEN);
            panel(d);
            pscore = score; pball = ballnum; pstate = state;
            pbonus = bonus; pmult = mult; pmsg = msgt != 0; pver = msgver;
        }
        ReleaseDC(w, d);
        return 0;

    case WM_DESTROY:
        KillTimer(w, 1);
        if (soundok) { psgmute(); CloseSound(); }
        freeboard();
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(w, m, wp, lp);
}

int PASCAL WinMain(HANDLE inst, HANDLE prev, LPSTR cmd, int show)
{
    WNDCLASS wc;
    HWND w;
    MSG msgq;

    if (!prev) {
        wc.style = 0;
        wc.lpfnWndProc = WndProc;
        wc.cbClsExtra = wc.cbWndExtra = 0;
        wc.hInstance = inst;
        wc.hIcon = NULL;
        wc.hCursor = NULL;              /* no pointer over the table     */
        wc.hbrBackground = GetStockObject(BLACK_BRUSH);
        wc.lpszMenuName = NULL;
        wc.lpszClassName = "TandyPinball";
        if (!RegisterClass(&wc)) return 1;
    }
    w = CreateWindow("TandyPinball", "Pinball",
                     WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
                     0, 0, GetSystemMetrics(SM_CXSCREEN),
                     GetSystemMetrics(SM_CYSCREEN), NULL, NULL, inst, NULL);
    if (!w) return 2;
    ShowWindow(w, show);
    UpdateWindow(w);
    while (GetMessage(&msgq, NULL, 0, 0)) {
        TranslateMessage(&msgq);
        DispatchMessage(&msgq);
    }
    (void)cmd;
    return (int)msgq.wParam;
}
