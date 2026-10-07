/*
 * PHYSICS.H - table geometry, ball physics and rules for Tandy Pinball.
 *
 * Shared unchanged by the Win16 game (PINBALL.C) and the host tests
 * (TEST.C). Integer-only C89 for Microsoft C 6 on an 8088: no floats.
 *
 * Units: the table is 160 x 244 square "table units" with y pointing down.
 *   Positions are Q6 (64 per unit) in int.
 *   Velocities are Q10 (1024 per unit) per substep, in int.
 * Each 55 ms timer tick runs SUBSTEPS physics substeps. A late timer slows
 * the game down instead of letting the ball jump through walls.
 */

#define Q          64      /* position fixed point                 */
#define SUBSTEPS   8
#define BALL_R     3       /* ball radius, table units             */
#define GRAVITY    13      /* Q10 per substep per substep          */
#define VMAX       2816    /* per-axis cap, 2.75 units per substep */

#define TABLE_W    160
#define TABLE_H    244
#define DRAIN_Y    248

/* ---- element kinds ---------------------------------------------------- */
#define K_WALL     0
#define K_SLING    1       /* kicks the ball away on a firm hit    */
#define K_GATE     2       /* one way: blocks only falling balls   */
#define K_TARGET   3       /* drop target; 'arg' is its index      */

typedef struct {
    int ax, ay, bx, by;    /* table units                          */
    int kind, arg;
} TSEG;

/* Top arc: a 12-chord semicircle, centre (80,80), radius 76. */
static const TSEG segs[] = {
    {  4, 80,   7, 60, K_WALL, 0}, {  7, 60,  14, 42, K_WALL, 0},
    { 14, 42,  26, 26, K_WALL, 0}, { 26, 26,  42, 14, K_WALL, 0},
    { 42, 14,  60,  7, K_WALL, 0}, { 60,  7,  80,  4, K_WALL, 0},
    { 80,  4, 100,  7, K_WALL, 0}, {100,  7, 118, 14, K_WALL, 0},
    {118, 14, 134, 26, K_WALL, 0}, {134, 26, 146, 42, K_WALL, 0},
    {146, 42, 153, 60, K_WALL, 0}, {153, 60, 156, 80, K_WALL, 0},
    /* outer walls, plunger lane and its one-way gate */
    {  4, 80,   4,244, K_WALL, 0},
    {156, 80, 156,244, K_WALL, 0},
    {144,100, 144,244, K_WALL, 0},
    {144,100, 156, 88, K_GATE, 0},
    {144,236, 156,236, K_WALL, 0},       /* plunger tip at rest   */
    /* top rollover lane posts */
    { 44, 28,  44, 38, K_WALL, 0}, { 68, 28,  68, 38, K_WALL, 0},
    { 92, 28,  92, 38, K_WALL, 0}, {116, 28, 116, 38, K_WALL, 0},
    /* upper-left deflector: wall-huggers from the arc go back in play */
    {  4, 98,  18,124, K_WALL, 0},
    /* drop target bank on the right, boxed in against the lane wall */
    {134,104, 144, 98, K_WALL, 0},
    {134,133, 144,141, K_WALL, 0},
    {134,104, 134,113, K_TARGET, 0},
    {134,114, 134,123, K_TARGET, 1},
    {134,124, 134,133, K_TARGET, 2},
    /* left slingshot, inlane/outlane post and inlane guide */
    { 22,150,  36,186, K_SLING, 0},
    { 22,150,  22,174, K_WALL, 0}, { 22,174,  36,186, K_WALL, 0},
    { 12,160,  12,184, K_WALL, 0},
    { 12,184,  46,207, K_WALL, 0},
    /* right side, mirrored about x = 74 */
    {126,150, 112,186, K_SLING, 0},
    {126,150, 126,174, K_WALL, 0}, {126,174, 112,186, K_WALL, 0},
    {136,160, 136,184, K_WALL, 0},
    {136,184, 102,207, K_WALL, 0}
};
#define NSEGS ((int)(sizeof(segs) / sizeof(segs[0])))

/* Pop bumpers: centre and radius in table units. */
static const int bumpx[3] = {56, 104, 80};
static const int bumpy[3] = {62, 62, 90};
#define BUMP_R 8

/* Top rollover lanes: centres between the posts. */
static const int lanex[3] = {56, 80, 104};
#define LANE_Y 34

/* Flippers: pivot, 22-unit blade, 16 angle steps from rest to up. */
#define FLIP_STEPS 16
#define FLIP_R     2       /* blade half-thickness, table units    */
#define LPIV_X 48
#define RPIV_X 100
#define PIV_Y  212
static const int flipdx[FLIP_STEPS] = {
    1219,1264,1303,1336,1363,1384,1398,1406,
    1408,1403,1392,1374,1351,1321,1285,1243};
static const int flipdy[FLIP_STEPS] = {
    704,620,534,444,353,261,167,72,
    -23,-118,-212,-306,-398,-488,-576,-661};

/* Plunger lane rest position and launch strength. */
#define LANE_X     150
#define REST_Y     232
#define CHARGE_MAX 20
#define PLUNGE_MIN 1650
#define PLUNGE_STEP 55

#define BALLS_PER_GAME 3
#define SAVE_TICKS  145    /* ~8 s ball save after each plunge     */
#define TARGET_RESET 30    /* ticks before a completed bank resets */

/* Events reported by tick(), for sound and redraw. */
#define EV_BUMPER  0x0001
#define EV_SLING   0x0002
#define EV_FLIP    0x0004
#define EV_LANE    0x0008      /* lane lights changed               */
#define EV_TARGET  0x0010      /* drop target state changed         */
#define EV_DRAIN   0x0020
#define EV_SAVE    0x0040
#define EV_LAUNCH  0x0080
#define EV_SCORE   0x0100
#define EV_OVER    0x0200
#define EV_MULT    0x0400
#define EV_WALL    0x0800

/* Game states. */
#define ST_OVER    0           /* waiting for Space                  */
#define ST_LANE    1           /* ball resting on the plunger        */
#define ST_PLAY    2

/* ---- state ------------------------------------------------------------- */
static int bx, by, vx, vy, fx, fy;     /* ball: Q6 pos, Q10 vel, carry  */
static int pbx, pby;                   /* position before this substep  */
static int lang, rang, lw, rw;         /* flipper angle step, ang. vel  */
static int leftkey, rightkey, plungekey;
static int charge;
static int state, balls, ballnum, saveticks, saveavail, resettick;
static int lanes, targets, bonus, mult;
static long score, best, lastbonus;
static unsigned events;
static unsigned long ticks;
static unsigned hits;                  /* switch hits, for the tests    */
static int lnx, lny;                   /* last contact normal, Q8       */
static int stillx, stilly, stillt;     /* stuck-ball detector           */
static int drainx;                     /* where the last ball left, units */

/* ---- integer helpers --------------------------------------------------- */
static int clampi(int v, int m)
{
    return v < -m ? -m : (v > m ? m : v);
}

static unsigned isqrt(unsigned long n)
{
    unsigned long r = 0, bit = 1UL << 30;
    while (bit > n) bit >>= 2;
    while (bit) {
        if (n >= r + bit) { n -= r + bit; r = (r >> 1) + bit; }
        else r >>= 1;
        bit >>= 2;
    }
    return (unsigned)r;
}

static void addscore(long n)
{
    score += n;
    if (score > 99999990L) score = 99999990L;
    events |= EV_SCORE;
}

/*
 * Resolve one contact. (cx,cy) is the closest point on the obstacle in Q6,
 * reach is ball radius plus obstacle half-thickness in table units,
 * e16 the restitution in 16ths, (svx,svy) the obstacle surface velocity.
 * Returns the incoming normal speed (positive = into the surface), or -1
 * when there is no contact.
 */
static int contact(int cx, int cy, int reach, int e16, int svx, int svy)
{
    int dx = bx - cx, dy = by - cy, nx, ny, d;
    long d2, r2 = (long)reach * Q * reach * Q, vn;

    if (dx < -reach * Q || dx > reach * Q ||
        dy < -reach * Q || dy > reach * Q) return -1;
    d2 = (long)dx * dx + (long)dy * dy;
    if (d2 >= r2) return -1;

    /* If the ball's previous position was on the other side, it moved
       through the surface during this substep: push back to that side. */
    if ((long)(pbx - cx) * dx + (long)(pby - cy) * dy < 0) {
        dx = -dx; dy = -dy;
    }
    d = (int)isqrt(d2);
    if (d == 0) { dx = pbx - cx; dy = pby - cy; d = (int)isqrt(
        (long)dx * dx + (long)dy * dy); }
    if (d == 0) { dx = 0; dy = -1; d = 1; }
    nx = (int)((long)dx * 256 / d);
    ny = (int)((long)dy * 256 / d);
    lnx = nx; lny = ny;

    bx = cx + (int)((long)nx * reach * Q / 256);
    by = cy + (int)((long)ny * reach * Q / 256);

    vn = ((long)(vx - svx) * nx + (long)(vy - svy) * ny) / 256;
    if (vn < 0) {
        long j = vn + vn * e16 / 16;
        if (vn > -160) j = vn;          /* settle slow contacts       */
        vx -= (int)(j * nx / 256);
        vy -= (int)(j * ny / 256);
        vx = clampi(vx, VMAX);
        vy = clampi(vy, VMAX);
    }
    return vn < 0 ? (int)-vn : 0;
}

/* Closest point on segment A-B (Q6) to the ball; 0 if out of reach. */
static int closest(int ax, int ay, int ex, int ey, int reach,
                   int *cxp, int *cyp)
{
    int dx = ex - ax, dy = ey - ay, lo, hi;
    long t, len2;

    lo = (ax < ex ? ax : ex) - reach * Q;
    hi = (ax > ex ? ax : ex) + reach * Q;
    if (bx < lo || bx > hi) return 0;
    lo = (ay < ey ? ay : ey) - reach * Q;
    hi = (ay > ey ? ay : ey) + reach * Q;
    if (by < lo || by > hi) return 0;

    len2 = (long)dx * dx + (long)dy * dy;
    t = (long)(bx - ax) * dx + (long)(by - ay) * dy;
    if (t <= 0) { *cxp = ax; *cyp = ay; }
    else if (t >= len2) { *cxp = ex; *cyp = ey; }
    else {
        /* t/len2 is 0..1; use 1/1024 steps to stay inside a long. */
        long f = t / (len2 / 1024 + 1);
        *cxp = ax + (int)((long)dx * f / 1024);
        *cyp = ay + (int)((long)dy * f / 1024);
    }
    return 1;
}

static int segcontact(int ax, int ay, int ex, int ey, int reach, int e16)
{
    int cx, cy;
    if (!closest(ax, ay, ex, ey, reach, &cx, &cy)) return -1;
    return contact(cx, cy, reach, e16, 0, 0);
}

/* ---- flippers ---------------------------------------------------------- */
static void fliptip(int left, int *tx, int *ty)
{
    int a = left ? lang : rang;
    *tx = (left ? LPIV_X * Q + flipdx[a] : RPIV_X * Q - flipdx[a]);
    *ty = PIV_Y * Q + flipdy[a];
}

static int flipper(int left)
{
    int px = (left ? LPIV_X : RPIV_X) * Q, py = PIV_Y * Q;
    int tx, ty, cx, cy, w = left ? lw : rw, svx = 0, svy = 0;
    long rx, ry;

    fliptip(left, &tx, &ty);
    if (!closest(px, py, tx, ty, BALL_R + FLIP_R, &cx, &cy)) return -1;
    if (w) {
        /* Surface velocity of the rotating blade at the contact point:
           farther from the pivot is faster, so tip shots are stronger. */
        rx = cx - px; ry = cy - py;
        if (left) { svx = (int)(ry * w / 16); svy = (int)(-rx * w / 16); }
        else      { svx = (int)(-ry * w / 16); svy = (int)(rx * w / 16); }
    }
    return contact(cx, cy, BALL_R + FLIP_R, 4, svx, svy);
}

static void moveflipper(int key, int *ang, int *w)
{
    int old = *ang;
    if (key) { *ang += 2; if (*ang > FLIP_STEPS - 1) *ang = FLIP_STEPS - 1; }
    else if (*ang > 0) --*ang;
    /* Angular velocity in 1/256 rad per substep; up is positive. */
    *w = (*ang - old) * 17;
}

/* ---- rules ------------------------------------------------------------- */
static void ready(void)
{
    bx = LANE_X * Q; by = REST_Y * Q;
    vx = vy = fx = fy = 0;
    charge = 0;
    bonus = 0; mult = 1;
    saveavail = 1;                      /* one ball save per ball       */
    state = ST_LANE;
}

static void newgame(void)
{
    score = 0; lastbonus = 0;
    balls = BALLS_PER_GAME; ballnum = 1;
    lanes = 0; targets = 0; resettick = 0;
    lang = rang = lw = rw = 0;
    hits = 0;
    ready();
    events |= EV_SCORE | EV_LANE | EV_TARGET;
}

static void reset(void)                 /* power-on: attract state     */
{
    ticks = 0; events = 0;
    leftkey = rightkey = plungekey = 0;
    saveticks = 0; stillx = stilly = stillt = 0;
    newgame();
    state = ST_OVER;
    balls = 0;
    best = 0;
}

static void lanehit(int i)
{
    int bit = 1 << i;
    ++hits; ++bonus;
    addscore(lanes & bit ? 100 : 500);
    lanes |= bit;
    if (lanes == 7) {
        lanes = 0;
        if (mult < 5) ++mult;
        addscore(5000);
        events |= EV_MULT;
    }
    events |= EV_LANE;
}

static void drain(void)
{
    drainx = bx / Q;
    if (saveticks > 0) {                /* ball save                    */
        saveticks = 0;
        bx = LANE_X * Q; by = REST_Y * Q;
        vx = vy = fx = fy = 0; charge = 0;
        state = ST_LANE;
        events |= EV_SAVE;
        return;
    }
    lastbonus = (long)bonus * 1000L * mult;
    addscore(lastbonus);
    events |= EV_DRAIN;
    if (--balls <= 0) {
        state = ST_OVER;
        if (score > best) best = score;
        events |= EV_OVER;
        return;
    }
    ++ballnum;
    ready();
}

/* ---- one physics substep ----------------------------------------------- */
static void substep(void)
{
    int i, n, oldy;

    moveflipper(leftkey, &lang, &lw);
    moveflipper(rightkey, &rang, &rw);
    if (state == ST_OVER) return;

    pbx = bx; pby = by; oldy = by;
    vy = clampi(vy + GRAVITY, VMAX);
    fx += vx; bx += fx >> 4; fx &= 15;
    fy += vy; by += fy >> 4; fy &= 15;

    for (i = 0; i < NSEGS; ++i) {
        const TSEG *s = &segs[i];
        if (s->kind == K_GATE) {
            /* One way: only a ball coming up out of the lane passes. */
            long side = (long)(s->bx - s->ax) * (pby - s->ay * Q) -
                        (long)(s->by - s->ay) * (pbx - s->ax * Q);
            if (side > 0) continue;
        }
        if (s->kind == K_TARGET && (targets & (1 << s->arg))) continue;
        n = segcontact(s->ax * Q, s->ay * Q, s->bx * Q, s->by * Q,
                       BALL_R, 8);
        if (n < 0) continue;
        if (s->kind == K_SLING && n > 200) {
            /* Kick along the contact normal, away from the rubber. */
            vx = clampi(vx + (int)((long)lnx * 1200 / 256), VMAX);
            vy = clampi(vy + (int)((long)lny * 1200 / 256), VMAX);
            ++hits; addscore(10);
            events |= EV_SLING;
        } else if (s->kind == K_TARGET && n > 120) {
            targets |= 1 << s->arg;
            ++hits; ++bonus; addscore(500);
            if (targets == 7) {
                addscore(5000); bonus += 3;
                resettick = TARGET_RESET;
            }
            events |= EV_TARGET;
        } else if (n > 600) {
            events |= EV_WALL;
        }
    }

    for (i = 0; i < 3; ++i) {
        n = contact(bumpx[i] * Q, bumpy[i] * Q, BALL_R + BUMP_R, 6, 0, 0);
        if (n >= 0) {
            vx = clampi(vx + (int)((long)lnx * 1434 / 256), VMAX);
            vy = clampi(vy + (int)((long)lny * 1434 / 256), VMAX);
            ++hits; ++bonus; addscore(100);
            events |= EV_BUMPER;
        }
    }

    if (flipper(1) > 900) events |= EV_WALL;
    if (flipper(0) > 900) events |= EV_WALL;

    /* Top rollover lanes: score when the ball crosses LANE_Y going down. */
    if (oldy < LANE_Y * Q && by >= LANE_Y * Q) {
        for (i = 0; i < 3; ++i)
            if (bx > (lanex[i] - 11) * Q && bx < (lanex[i] + 11) * Q)
                lanehit(i);
    }

    /* Drain first. Anything off the table also counts, as a safety net
       for 16-bit positions; it never happens in the tested geometry. */
    if (state != ST_OVER &&
        (by > DRAIN_Y * Q || bx < 0 || bx > TABLE_W * Q || by < 0)) {
        if (state == ST_LANE) state = ST_PLAY;
        drain();
    } else if (state == ST_LANE && bx < 144 * Q) {
        state = ST_PLAY;                /* ball left the plunger lane   */
    } else if (state == ST_PLAY && bx > 145 * Q && by > 200 * Q &&
               by < 240 * Q) {
        state = ST_LANE;                /* fell back: plunge it again   */
        charge = 0;
    }
}

/* Rotate lit lanes, as real machines do with the flipper buttons. */
static void lanechange(int left)
{
    if (state != ST_PLAY || lanes == 0 || lanes == 7) return;
    if (left) lanes = ((lanes >> 1) | (lanes << 2)) & 7;
    else      lanes = ((lanes << 1) | (lanes >> 2)) & 7;
    events |= EV_LANE;
}

/* Set flipper keys, remembering presses for lane change and sound. */
static void setflip(int left, int down)
{
    int *k = left ? &leftkey : &rightkey;
    if (down && !*k) {
        lanechange(left);
        events |= EV_FLIP;
    }
    *k = down;
}

/* Plunger: hold to pull back, release to fire. Space also starts a game. */
static void setplunger(int down)
{
    if (down && !plungekey && state == ST_OVER) {
        newgame();
        plungekey = 1;                  /* this press only starts       */
        charge = -1;
        return;
    }
    if (!down && plungekey) {
        if (state == ST_LANE && charge > 0 && bx > 144 * Q &&
            by >= (REST_Y - 2) * Q) {
            vy = -(PLUNGE_MIN + charge * PLUNGE_STEP);
            if (saveavail) { saveticks = SAVE_TICKS; saveavail = 0; }
            events |= EV_LAUNCH;
        }
        charge = 0;
    }
    plungekey = down;
}

/* Drop a held plunger without firing (pause, focus loss). */
static void cancelplunger(void)
{
    plungekey = 0;
    charge = 0;
}

/* One 55 ms timer tick. Returns and clears the event mask. */
static unsigned tick(void)
{
    int i;
    unsigned ev;

    ++ticks;
    if (plungekey && state == ST_LANE && charge >= 0 &&
        charge < CHARGE_MAX) ++charge;
    if (saveticks > 0 && state == ST_PLAY) --saveticks;
    if (resettick > 0 && --resettick == 0) {
        targets = 0;
        events |= EV_TARGET;
    }
    for (i = 0; i < SUBSTEPS; ++i) substep();

    /* Integer physics can balance a ball on a post tip forever. If a live
       ball has not moved for ~2 s and is not cradled on a held flipper,
       nudge it sideways. */
    if (state == ST_PLAY && (by < 195 * Q || (!leftkey && !rightkey)) &&
        bx - stillx > -Q && bx - stillx < Q &&
        by - stilly > -Q && by - stilly < Q) {
        if (++stillt > 36) {
            vx = (ticks & 1) ? 500 : -500;
            vy = -300;
            stillt = 0;
        }
    } else {
        stillx = bx; stilly = by; stillt = 0;
    }
    ev = events;
    events = 0;
    return ev;
}
