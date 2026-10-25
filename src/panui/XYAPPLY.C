/* Host regression for the actual XYCTL Apply glue extracted by HOSTUI.PY. */
#include <stdio.h>
#include <string.h>
#include "PANSET.H"
#define FALSE 0
static int live, hardware, statsProc = 1;
static int edge, edgePolled, edgeRepeat, follow, window;
static int available, reported, refuse, modes, resets;

int Query(void)
{
    if (!available)
        return 0;
    hardware = reported;
    return 1;
}

static void Mode(int want)
{
    modes++;
    if (!refuse)
        hardware = want;
}

static void ResetEdge(void) { resets++; }
static void Log(const char *s, int a, int b, int c, int d)
{
    (void)s; (void)a; (void)b; (void)c; (void)d;
}
static void InvalidateRect(int w, int r, int e)
{
    (void)w; (void)r; (void)e;
}
#define lstrcpy strcpy
#include "XYAPPLY.INC"

static int Test(int avail, int actual, int want, int refused,
                int code, int calls, int result)
{
    PANSET w, a;
    char note[80];
    int rc;
    live = 1; hardware = 0; available = avail; reported = actual;
    refuse = refused; modes = resets = edge = 0;
    PanSetDefaults(PS_BACK_XY, &w);
    w.mode = want; w.edgeOn = 1;
    rc = XyApply(0, &w, &a, note, sizeof(note));
    return rc == code && modes == calls &&
           (code == PS_OK ? (a.mode == result && edge == 1) :
                           (resets == 0 && edge == 0));
}

int main(void)
{
    int bad = 0;
    bad += !Test(0, 0, 0, 0, PS_E_LOST, 0, 0);
    bad += !Test(1, 1, 0, 0, PS_OK, 1, 0);
    bad += !Test(1, 0, 1, 1, PS_OK, 1, 0);
    bad += !Test(1, 0, 0, 0, PS_OK, 0, 0);
    printf("XY Apply driver-state cases: %d failures\n", bad);
    return bad;
}
