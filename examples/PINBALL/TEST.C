/*
 * TEST.C - Tandy Pinball physics and rules regression.
 *
 * Builds on a host C compiler with -DHOSTMAIN, and natively with
 * Microsoft C 6 /G0 /Gw as a Windows app that writes C:\PINTEST.LOG.
 * The replay checksum must match between the two: the native build uses
 * 16-bit int, so any overflow the host can't see changes the checksum.
 */
#ifdef HOSTMAIN
#include <stdio.h>
#else
#define WINVER 0x0300
#include <windows.h>
#endif
#include "PHYSICS.H"

#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)

static void run(int n) { while (n-- > 0) tick(); }

static void plunge(int hold)
{
    setplunger(1);
    run(hold);
    setplunger(0);
}

static void place(int x, int y, int ivx, int ivy)
{
    state = ST_PLAY;
    bx = x * Q; by = y * Q; vx = ivx; vy = ivy; fx = fy = 0;
}

/* Fastest upward speed in the next n ticks (larger = harder shot). */
static int bestup(int n)
{
    int i, k, top = 0;
    for (i = 0; i < n; ++i)
        for (k = 0; k < SUBSTEPS; ++k) {
            substep();
            if (-vy > top) top = -vy;
        }
    return top;
}

static long replay(unsigned long n)
{
    unsigned seed = 7;
    long sum = 0;
    unsigned long t;
    reset();
    for (t = 0; t < n; ++t) {
        seed = (unsigned)((seed * 109U + 89U) & 32767U);
        if (state == ST_OVER) { setplunger(1); setplunger(0); }
        if (state == ST_LANE) plunge(10 + (int)(seed % 11));
        setflip(1, (seed >> 3) & 1);
        setflip(0, (seed >> 7) & 1);
        tick();
        sum = sum * 31 + score + bx + by + vx + vy;
        sum &= 0x0FFFFFFFL;
    }
    return sum;
}

static int tests(void)
{
    int i, top, base, still;
    unsigned ev;

    /* Power-on: attract state, Space starts a game with three balls. */
    reset();
    CHECK(state == ST_OVER);
    setplunger(1); setplunger(0);
    CHECK(state == ST_LANE && balls == 3 && ballnum == 1);

    /* A full plunge leaves the lane and reaches the top arc. */
    run(3);
    plunge(CHARGE_MAX);
    top = by;
    for (i = 0; i < 40; ++i) { tick(); if (by < top) top = by; }
    CHECK(top < 30 * Q);
    CHECK(state == ST_PLAY);

    /* A tap of the plunger falls back to it without losing a ball. */
    newgame(); run(3);
    plunge(2);
    run(60);
    CHECK(state == ST_LANE && balls == 3);

    /* Held flipper cradles a ball near its pivot. */
    newgame(); leftkey = 1; run(2);
    place(30, 188, 200, 0);
    run(120);
    CHECK(state == ST_PLAY);
    CHECK(bx > 38 * Q && bx < 56 * Q && by > 196 * Q && by < 212 * Q);
    CHECK(vx > -80 && vx < 80 && vy > -80 && vy < 80);

    /* Release the cradle, let the ball roll, flip: it goes up-field.
       (Flipping with the ball on the pivot is weak, as on real ones.) */
    leftkey = 0; run(7);                /* let it roll to the sweet spot */
    setflip(1, 1);
    top = by;
    for (i = 0; i < 40; ++i) { tick(); if (by < top) top = by; }
    CHECK(top < 140 * Q);
    setflip(1, 0);

    /* Tip shots are harder than shots near the pivot. */
    newgame(); place(64, 214, 0, 0); lang = 0; leftkey = 1;
    top = bestup(3);
    newgame(); place(52, 206, 0, 0); lang = 0; leftkey = 1;
    base = bestup(3);
    CHECK(top > base + 300);
    leftkey = 0;

    /* A flipper at rest gives no kick; a ball rolls off it. */
    newgame(); place(52, 205, 0, 0); run(60);
    CHECK(by > 216 * Q || state != ST_PLAY || balls < 3);

    /* Pop bumper: scores 100 and throws the ball away hard. */
    newgame(); place(bumpx[0], bumpy[0] - 14, 0, 400);
    ev = tick();
    CHECK(ev & EV_BUMPER);
    CHECK(score >= 100 && bonus >= 1);

    /* Slingshot kicks a firm hit. */
    newgame(); place(40, 165, -1200, 300);
    for (i = 0, ev = 0; i < 6; ++i) ev |= tick();
    CHECK(ev & EV_SLING);

    /* Top lanes: light each, three lit raise the multiplier. */
    newgame();
    for (i = 0; i < 3; ++i) {
        place(lanex[i], LANE_Y - 1, 0, 300);
        tick();
    }
    CHECK(mult == 2 && lanes == 0 && score >= 6500);

    /* Flipper buttons rotate lit lanes. */
    newgame(); state = ST_PLAY; lanes = 1;
    setflip(0, 1); setflip(0, 0);
    CHECK(lanes == 2);
    setflip(1, 1); setflip(1, 0);
    CHECK(lanes == 1);

    /* Drop targets: each drops; the full bank scores and resets. */
    newgame();
    for (i = 0; i < 3; ++i) {
        place(128, 108 + 10 * i, 1200, 0);
        tick();
        state = ST_PLAY;
    }
    CHECK(targets == 7);
    run(TARGET_RESET + 1);
    CHECK(targets == 0);

    /* Ball save once per ball, then drains count. */
    newgame(); run(2); plunge(CHARGE_MAX);
    place(74, 240, 0, 900);
    for (i = 0, ev = 0; i < 4; ++i) ev |= tick();
    CHECK(ev & EV_SAVE);
    CHECK(balls == 3 && state == ST_LANE);
    plunge(CHARGE_MAX);
    place(74, 240, 0, 900);
    for (i = 0, ev = 0; i < 4; ++i) ev |= tick();
    CHECK((ev & EV_DRAIN) && balls == 2 && ballnum == 2);

    /* Three drains end the game and keep the high score. */
    newgame(); score = 1234;
    for (i = 0; i < 3; ++i) {
        place(74, 240, 0, 900);
        run(4);
    }
    CHECK(state == ST_OVER && best >= 1234);

    /* A ball that falls back into the lane can be plunged again. */
    newgame(); place(150, 210, 0, 300); run(30);
    CHECK(state == ST_LANE);

    /* Stress: random play never leaves the table or sticks. */
    reset();
    {
        unsigned seed = 3;
        unsigned long t;
#ifdef HOSTMAIN
        unsigned long n = 2000000UL;
#else
        unsigned long n = 20000UL;
#endif
        int sx = 0, sy = 0;
        still = 0;
        for (t = 0; t < n; ++t) {
            seed = (unsigned)((seed * 109U + 89U) & 32767U);
            if (state == ST_OVER) { setplunger(1); setplunger(0); }
            if (state == ST_LANE) plunge(8 + (int)(seed % 13));
            setflip(1, (seed & 3) == 0);
            setflip(0, (seed & 12) == 0);
            tick();
            if (state == ST_PLAY) {
                CHECK(bx >= 3 * Q && bx <= 157 * Q);
                CHECK(by >= 3 * Q && by <= DRAIN_Y * Q + 2 * Q);
                CHECK(vx >= -VMAX && vx <= VMAX && vy >= -VMAX &&
                      vy <= VMAX);
                if (bx / Q == sx && by / Q == sy && !leftkey && !rightkey) {
                    CHECK(++still < 60);
                } else {
                    still = 0; sx = bx / Q; sy = by / Q;
                }
            }
            CHECK(score >= 0 && score <= 99999990L);
        }
    }

    /* Same input schedule, same result. */
    CHECK(replay(3000) == replay(3000));
    return 0;
}

#ifdef HOSTMAIN
int main(void)
{
    int r = tests();
    printf("%s line=%d replay=%ld\n", r ? "FAIL" : "PASS", r, replay(3000));
    return r ? 1 : 0;
}
#else
LONG FAR PASCAL WndProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    return DefWindowProc(w, m, wp, lp);
}

int PASCAL WinMain(HANDLE h, HANDLE old, LPSTR cmd, int show)
{
    int r = tests();
    HFILE f;
    char s[96];
    wsprintf(s, "%s line=%d replay=%ld\r\nCOMPLETE=1\r\n",
             (LPSTR)(r ? "FAIL" : "PASS"), r, replay(3000));
    f = _lcreat("C:\\PINTEST.LOG", 0);
    if (f != HFILE_ERROR) { _lwrite(f, s, lstrlen(s)); _lclose(f); }
    (void)h; (void)old; (void)cmd; (void)show;
    return r;
}
#endif
