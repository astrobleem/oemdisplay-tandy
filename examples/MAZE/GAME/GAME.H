/*
 * GAME.H - Tandy Maze rules: maze generation, grid movement, autopilot.
 *
 * Pure C89 with no Windows calls, shared by MAZE.C and TEST.C. Every value
 * fits a 16-bit int; the random generator uses explicit 32-bit masking so
 * the host test and the 8088 build produce identical mazes.
 *
 * The maze is a block grid: (2n+1) x (2n+1) squares, each wall or open.
 * One keypress moves one square or turns 90 degrees, as in Bard's Tale.
 */

#define MAXN     15                     /* largest maze: 15 x 15 cells   */
#define MAXB     (2 * MAXN + 1)         /* 31 x 31 squares               */

#define B_WALL   0
#define B_OPEN   1
#define B_EXIT   2

/* Directions: 0 north, 1 east, 2 south, 3 west (screen up = north). */
static const int ddx[4] = { 0, 1, 0, -1 };
static const int ddy[4] = { -1, 0, 1, 0 };

static unsigned char grid[MAXB][MAXB];
static unsigned char seen[MAXB][MAXB];  /* 1 visited, 2 seen from afar   */
static int msize;                       /* squares per side, 2n+1        */
static int ncell;                       /* cells per side, n             */
static int px, py, pdir;                /* player square and facing      */
static int ex, ey;                      /* exit square (in outer wall)   */
static int level, moves, par, bumps;
static unsigned long seed;

/* Events for sound and screen updates; cleared by the caller. */
#define EV_STEP   0x01
#define EV_TURN   0x02
#define EV_BUMP   0x04
#define EV_EXIT   0x08
#define EV_LEVEL  0x10
static unsigned gev;

/* Squares newly seen or changed since the caller last emptied the list
   (for drawing the map incrementally). Overflow asks for a full redraw. */
#define NEWMAX 24
static unsigned char newx[NEWMAX], newy[NEWMAX];
static int nnew, newfull;

static void touched(int x, int y)
{
    if (nnew < NEWMAX) {
        newx[nnew] = (unsigned char)x; newy[nnew] = (unsigned char)y; ++nnew;
    } else newfull = 1;
}

static unsigned rnd(void)
{
    seed = (seed * 1103515245UL + 12345UL) & 0xFFFFFFFFUL;
    return (unsigned)((seed >> 16) & 0x7FFF);
}

static int blk(int x, int y)
{
    if (x < 0 || y < 0 || x >= msize || y >= msize) return B_WALL;
    return grid[y][x];
}

/* Breadth-first distances over open squares from (sx,sy). Uses the
   caller's buffer; unreachable squares stay 0xFFFF. Returns the farthest
   cell square found (cells are odd,odd squares) through fx/fy. */
static unsigned dist[MAXB][MAXB];
static unsigned char queue[MAXB * MAXB][2];

static void bfs(int sx, int sy)
{
    int head = 0, tail = 0, x, y, d, nx, ny;
    for (y = 0; y < MAXB; ++y)
        for (x = 0; x < MAXB; ++x) dist[y][x] = 0xFFFFu;
    dist[sy][sx] = 0;
    queue[tail][0] = (unsigned char)sx;
    queue[tail][1] = (unsigned char)sy;
    ++tail;
    while (head < tail) {
        x = queue[head][0]; y = queue[head][1]; ++head;
        for (d = 0; d < 4; ++d) {
            nx = x + ddx[d]; ny = y + ddy[d];
            if (blk(nx, ny) == B_OPEN && dist[ny][nx] == 0xFFFFu) {
                dist[ny][nx] = dist[y][x] + 1;
                queue[tail][0] = (unsigned char)nx;
                queue[tail][1] = (unsigned char)ny;
                ++tail;
            }
        }
    }
}

/* Iterative depth-first carve: a perfect maze (one path between any two
   cells). The stack holds cell indices, at most n*n entries. */
static unsigned char stackc[MAXN * MAXN];

static void carve(void)
{
    int sp = 0, c, cx, cy, d, k, n, nx, ny, opts[4];
    int x, y;

    for (y = 0; y < MAXB; ++y)
        for (x = 0; x < MAXB; ++x) { grid[y][x] = B_WALL; seen[y][x] = 0; }
    grid[1][1] = B_OPEN;
    stackc[sp++] = 0;
    while (sp > 0) {
        c = stackc[sp - 1];
        cx = c % ncell; cy = c / ncell;
        n = 0;
        for (d = 0; d < 4; ++d) {
            nx = cx + ddx[d]; ny = cy + ddy[d];
            if (nx >= 0 && ny >= 0 && nx < ncell && ny < ncell &&
                grid[2 * ny + 1][2 * nx + 1] == B_WALL)
                opts[n++] = d;
        }
        if (!n) { --sp; continue; }
        d = opts[rnd() % n];
        nx = cx + ddx[d]; ny = cy + ddy[d];
        grid[2 * cy + 1 + ddy[d]][2 * cx + 1 + ddx[d]] = B_OPEN;
        grid[2 * ny + 1][2 * nx + 1] = B_OPEN;
        k = ny * ncell + nx;
        stackc[sp++] = (unsigned char)k;
    }
}

/* Put the exit in the outer wall beside the boundary cell farthest from
   the start, so every level asks for a real walk. */
static void placeexit(void)
{
    int x, y, bx = 1, by = 1, best = -1, d;
    bfs(1, 1);
    for (y = 1; y < msize; y += 2)
        for (x = 1; x < msize; x += 2)
            if ((x == 1 || y == 1 || x == msize - 2 || y == msize - 2) &&
                (int)dist[y][x] > best && !(x == 1 && y == 1)) {
                best = (int)dist[y][x]; bx = x; by = y;
            }
    /* Prefer the side facing away from the start corner. */
    if (bx == msize - 2) { ex = msize - 1; ey = by; }
    else if (by == msize - 2) { ex = bx; ey = msize - 1; }
    else if (by == 1) { ex = bx; ey = 0; }
    else { ex = 0; ey = by; }
    grid[ey][ex] = B_EXIT;
    par = best + 1;                     /* last step goes into the exit */
    (void)d;
}

static void face_open(void)
{
    int d;
    for (d = 0; d < 4; ++d)
        if (blk(px + ddx[d], py + ddy[d]) != B_WALL) { pdir = d; return; }
}

static int apend;                       /* autopilot: step after a turn  */

static void look(void);

static void newlevel(int lv)
{
    level = lv;
    ncell = 3 + lv;
    if (ncell > MAXN) ncell = MAXN;
    msize = 2 * ncell + 1;
    carve();
    placeexit();
    px = py = 1;
    face_open();
    moves = bumps = 0;
    apend = 0;
    look();
    nnew = 0; newfull = 1;
    gev |= EV_LEVEL;
}

static void newgame(unsigned long s)
{
    seed = s & 0xFFFFFFFFUL;
    newlevel(1);
}

/* Mark squares the player has looked at, for the map. */
static void look(void)
{
    int k, x = px, y = py, l, sx, sy;
    if (seen[py][px] != 1) { seen[py][px] = 1; touched(px, py); }
    for (k = 1; k < 6; ++k) {
        x += ddx[pdir]; y += ddy[pdir];
        for (l = -1; l <= 1; ++l) {
            sx = x + l * ddx[(pdir + 1) & 3];
            sy = y + l * ddy[(pdir + 1) & 3];
            if (sx >= 0 && sy >= 0 && sx < msize && sy < msize &&
                !seen[sy][sx]) { seen[sy][sx] = 2; touched(sx, sy); }
        }
        if (blk(x, y) != B_OPEN) break;
    }
}

/* Actions. Each returns nonzero if the view changed. */
#define A_FWD   0
#define A_BACK  1
#define A_LEFT  2
#define A_RIGHT 3
#define A_ABOUT 4

static int act(int a)
{
    int d = pdir, nx, ny, b;
    touched(px, py);                    /* player marker moves or turns */
    if (a == A_LEFT || a == A_RIGHT || a == A_ABOUT) {
        pdir = (pdir + (a == A_LEFT ? 3 : a == A_RIGHT ? 1 : 2)) & 3;
        gev |= EV_TURN;
        look();
        return 1;
    }
    if (a == A_BACK) d = (pdir + 2) & 3;
    nx = px + ddx[d]; ny = py + ddy[d];
    b = blk(nx, ny);
    if (b == B_WALL) { ++bumps; gev |= EV_BUMP; return 0; }
    ++moves;
    if (b == B_EXIT) { px = nx; py = ny; gev |= EV_EXIT; return 1; }
    px = nx; py = ny;
    touched(px, py);
    gev |= EV_STEP;
    look();
    return 1;
}

/* Screensaver walker: keep the right hand on the wall. In a perfect maze
   with the exit in the outer wall this visits the exit. */
static int autopilot(void)
{
    int r = (pdir + 1) & 3, l = (pdir + 3) & 3;
    if (apend) { apend = 0; return act(A_FWD); }
    if (blk(px + ddx[r], py + ddy[r]) != B_WALL) {
        apend = 1;
        return act(A_RIGHT);
    }
    if (blk(px + ddx[pdir], py + ddy[pdir]) != B_WALL) return act(A_FWD);
    if (blk(px + ddx[l], py + ddy[l]) != B_WALL) {
        apend = 1;
        return act(A_LEFT);
    }
    return act(A_ABOUT);
}
