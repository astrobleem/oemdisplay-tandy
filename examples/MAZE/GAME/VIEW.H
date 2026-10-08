/*
 * VIEW.H - Tandy Maze first-person view, drawn into a byte buffer.
 *
 * The buffer uses the layout of a Windows 3.0 compatible bitmap on the
 * Tandy drivers: four 1-bit planes, interleaved per scanline, each plane
 * row rowb bytes (even). MAZE.C hands it to SetBitmapBits and draws it
 * with a single BitBlt, because on these drivers every GDI call costs
 * about 8 ms on an 8088 while plain byte writes are cheap.
 *
 * Geometry: eye at the back of the current square, 90 degree field of
 * view, walls one unit high, so a wall straight ahead is one square
 * away. Faces are drawn far to near. All arithmetic is 16-bit; the
 * slanted edges of side walls step with a remainder.
 */

#ifndef FAR
#define FAR
#endif

#define VDEPTH  5                       /* squares drawn ahead           */

/* Shades. */
#define SH_CEIL   0
#define SH_FLOOR  1
#define SH_EDGE   2
#define SH_MARK   3
#define SH_FRONT  4                     /* 4..8: front faces, depth 1..5 */
#define SH_SIDE   9                     /* 9..14: side faces, depth 0..5 */
#define SH_EXITF  15
#define SH_EXITS  16
#define NSHADE    17

/* Calibrated solid colours: pattern byte per row (0..7) and plane. */
#define C_BLACK  0
#define C_DARK   1
#define C_LIGHT  2
#define C_WHITE  3
#define C_ACC    4
#define C_ACCDK  5
#define NCOL     6
static unsigned char colr[NCOL][8][4];
static unsigned char shade[NSHADE][8][4];

static int vw, vh, rowb, vcx, vcy;      /* view size, plane row bytes    */
static int bh;                          /* buffer rows: view + status    */
static int gscale = 1;                  /* glyph width scale (640: 2)    */
#define HUDH 9                          /* status line under the view    */
static unsigned char FAR *fb;           /* frame buffer                  */
static unsigned long spans;             /* statistics for tests          */

/* 4x4 ordered dither: bit set where level (0..16) says "colour a". */
static const unsigned char bayer[4][4] = {
    { 0, 8, 2, 10 }, { 12, 4, 14, 6 }, { 3, 11, 1, 9 }, { 15, 7, 13, 5 }
};

static unsigned char dmask(int level, int row)
{
    int x;
    unsigned char m = 0;
    for (x = 0; x < 8; ++x)
        if ((int)bayer[row & 3][x & 3] < level)
            m = (unsigned char)(m | (0x80 >> x));
    return m;
}

static void mix(int sh, int a, int b, int level)
{
    int r, p;
    unsigned char m;
    for (r = 0; r < 8; ++r) {
        m = dmask(level, r);
        for (p = 0; p < 4; ++p)
            shade[sh][r][p] = (unsigned char)((colr[a][r][p] & m) |
                                              (colr[b][r][p] & ~m));
    }
}

static int samecol(int a, int b)
{
    int r, p;
    for (r = 0; r < 8; ++r)
        for (p = 0; p < 4; ++p)
            if (colr[a][r][p] != colr[b][r][p]) return 0;
    return 1;
}

/* Choose shades for the colours this mode really has. Returns 1 for the
   16-colour palette, 0 for dithered black and white (plus accent). */
static int makeshades(void)
{
    int k, gray = !samecol(C_LIGHT, C_WHITE) && !samecol(C_DARK, C_BLACK);
    int acc = !samecol(C_ACC, C_BLACK) && !samecol(C_ACC, C_WHITE);
    static const int fl[5] = { 16, 12, 9, 6, 4 };
    static const int sl[6] = { 11, 9, 7, 5, 3, 2 };
    int r, p;

    mix(SH_CEIL, C_BLACK, C_BLACK, 0);
    mix(SH_EDGE, C_BLACK, C_BLACK, 0);
    if (gray) {
        mix(SH_FLOOR, C_DARK, C_BLACK, 16);
        mix(SH_MARK, C_LIGHT, C_LIGHT, 16);
        mix(SH_FRONT + 0, C_WHITE, C_WHITE, 16);
        mix(SH_FRONT + 1, C_LIGHT, C_LIGHT, 16);
        mix(SH_FRONT + 2, C_LIGHT, C_DARK, 8);
        mix(SH_FRONT + 3, C_DARK, C_DARK, 16);
        mix(SH_FRONT + 4, C_DARK, C_BLACK, 8);
        mix(SH_SIDE + 0, C_LIGHT, C_LIGHT, 16);
        mix(SH_SIDE + 1, C_LIGHT, C_LIGHT, 16);
        mix(SH_SIDE + 2, C_LIGHT, C_DARK, 8);
        mix(SH_SIDE + 3, C_DARK, C_DARK, 16);
        mix(SH_SIDE + 4, C_DARK, C_BLACK, 8);
        mix(SH_SIDE + 5, C_DARK, C_BLACK, 4);
    } else {
        mix(SH_FLOOR, C_WHITE, C_BLACK, 2);
        mix(SH_MARK, C_WHITE, C_WHITE, 16);
        for (k = 0; k < 5; ++k) mix(SH_FRONT + k, C_WHITE, C_BLACK, fl[k]);
        for (k = 0; k < 6; ++k) mix(SH_SIDE + k, C_WHITE, C_BLACK, sl[k]);
    }
    if (acc) {
        mix(SH_EXITF, C_ACC, C_ACC, 16);
        mix(SH_EXITS, C_ACCDK, C_ACCDK, 16);
        if (samecol(C_ACCDK, C_BLACK) || samecol(C_ACCDK, C_ACC))
            mix(SH_EXITS, C_ACC, C_BLACK, 10);
    } else {
        /* No accent colour: bold vertical stripes mark the exit. */
        for (r = 0; r < 8; ++r)
            for (p = 0; p < 4; ++p) {
                shade[SH_EXITF][r][p] = (unsigned char)
                    ((colr[C_WHITE][r][p] & 0xCC) |
                     (colr[C_BLACK][r][p] & 0x33));
                shade[SH_EXITS][r][p] = (unsigned char)
                    ((colr[C_WHITE][r][p] & 0x88) |
                     (colr[C_BLACK][r][p] & 0x77));
            }
    }
    return gray;
}

/* Row fill, all four planes, parameters in globals (a far call with
   nine arguments costs more than the fill on an 8088): bytes f_p[0..f_n]
   get f_pat (first and last byte masked by f_m0/f_m1), then the edge
   pixels are cleared with keep masks f_k0 (byte 0) and f_k1 (byte f_n);
   0xFF keeps everything. Black is all-zero on every Tandy driver, which
   makeview() checks. The 8088 build uses inline assembly. */
#define SP_L 1                          /* first pixel is an edge        */
#define SP_R 2                          /* last pixel is an edge         */
#define SP_M 4                          /* also the mirrored row         */
static unsigned char FAR *f_p;
static unsigned char *f_pat;
static int f_n;
static unsigned char f_m0, f_m1, f_k0, f_k1, f_ms;
static const unsigned char lmask[8] = {
    0xFF, 0x7F, 0x3F, 0x1F, 0x0F, 0x07, 0x03, 0x01 };
static const unsigned char rmask[8] = {
    0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE, 0xFF };
static const unsigned char kmask[8] = {
    0x7F, 0xBF, 0xDF, 0xEF, 0xF7, 0xFB, 0xFD, 0xFE };
static unsigned rowoff[200 + HUDH];     /* y * 4 * rowb                  */

/* f_rows rows from f_p; the pattern row pointer f_pat advances 4 bytes
   per row and wraps at f_end (8 rows of the shade). */
static unsigned char *f_end;
static int f_rows;
static unsigned char FAR *f_p2;         /* mirrored row, if f_mir        */
static unsigned char *f_pat2;
static int f_mir;

static void fillrow(void)
{
#ifdef MAZE_HOST
    int pl, i, n = f_n, r;
#ifdef PROF
    ++pcalls;
    prow += (unsigned long)f_rows;
    pbytes += (unsigned long)f_rows * (unsigned long)(n + 1);
#endif
    unsigned char FAR *q, FAR *row = f_p, *pat = f_pat;
    for (r = 0; r < f_rows; ++r) {
        for (pl = 0; pl < 4; ++pl) {
            q = row + pl * rowb;
            if (n == 0) {
                unsigned char m = (unsigned char)(f_m0 & f_m1);
                q[0] = (unsigned char)((q[0] & ~m) | (pat[pl] & m));
            } else {
                q[0] = (unsigned char)((q[0] & ~f_m0) | (pat[pl] & f_m0));
                for (i = 1; i < n; ++i) q[i] = pat[pl];
                q[n] = (unsigned char)((q[n] & ~f_m1) | (pat[pl] & f_m1));
            }
            q[0] &= f_k0;
            q[n] &= f_k1;
        }
        row += 4 * rowb;
        pat += 4;
        if (pat == f_end) pat -= 32;
        if (r == f_rows - 1 && f_mir) {
            f_mir = 0; f_rows = 1; r = -1;
            row = f_p2; pat = f_pat2;
        }
    }
#else
    int rb = rowb;
    _asm {
        push si
        push di
        les di, f_p
        mov si, f_pat
        mov dx, rb
        mov bl, f_m0
        mov bh, f_m1
    row:
        mov cx, 4
    plane:
        push cx
        push di
        lodsb
        mov cx, f_n
        jcxz single
        mov ah, es:[di]
        xor ah, al
        and ah, bl
        xor es:[di], ah
        inc di
        dec cx
        mov ah, al
        shr cx, 1
        rep stosw
        adc cx, cx
        rep stosb
        mov ah, es:[di]
        xor ah, al
        and ah, bh
        xor es:[di], ah
        mov al, f_k1
        and es:[di], al
        pop di
        mov al, f_k0
        and es:[di], al
        jmp next
    single:
        mov ah, es:[di]
        xor ah, al
        and ah, f_ms
        xor es:[di], ah
        mov al, f_k0
        and al, f_k1
        and es:[di], al
        pop di
    next:
        add di, dx
        pop cx
        loop plane
        cmp si, f_end
        jne samepat
        sub si, 32
    samepat:
        dec f_rows
        jnz row
        cmp f_mir, 0
        je done
        mov f_mir, 0
        mov f_rows, 1
        les di, f_p2
        mov si, f_pat2
        jmp row
    done:
        pop di
        pop si
    }
#endif
}

/* Rows y..y+n-1, pixels [x0,x1). Flags: SP_L/SP_R edge pixels; SP_M
   also fills the mirror of row y in the bottom half (n must be 1). */
static void hrect(int y, int n, int x0, int x1, int sh, int fl)
{
    int b0, y2;
    if (x0 < 0) { x0 = 0; fl &= ~SP_L; }
    if (x1 > vw) { x1 = vw; fl &= ~SP_R; }
    if (x0 >= x1 || n < 1) return;
    ++spans;
#ifdef GDIHOOK
    if (gdc) {
        gdirect(y, n, x0, x1, sh, fl);
        if (fl & SP_M) gdirect(vh - 1 - y, 1, x0, x1, sh, fl);
        return;
    }
#endif
    b0 = x0 >> 3;
    f_n = ((x1 - 1) >> 3) - b0;
    f_m0 = lmask[x0 & 7];
    f_m1 = rmask[(x1 - 1) & 7];
    f_ms = (unsigned char)(f_m0 & f_m1);
    f_k0 = (unsigned char)((fl & SP_L) ? kmask[x0 & 7] : 0xFF);
    f_k1 = (unsigned char)((fl & SP_R) ? kmask[(x1 - 1) & 7] : 0xFF);
    f_p = fb + rowoff[y] + b0;
    f_pat = shade[sh][y & 7];
    f_end = shade[sh][0] + 32;
    f_rows = n;
    f_mir = 0;
    if (fl & SP_M) {
        y2 = vh - 1 - y;
        f_p2 = fb + rowoff[y2] + b0;
        f_pat2 = shade[sh][y2 & 7];
        f_mir = 1;
    }
    fillrow();
}

/* One row and, with SP_M, its mirror in the bottom half. */
static void hspan(int y, int x0, int x1, int sh, int fl)
{
    hrect(y, 1, x0, x1, sh, fl);
}

static void span(int y, int x0, int x1, int sh)
{
    hspan(y, x0, x1, sh, 0);
}

/* Set the view size and its row table. rowb is the bitmap's own row
   width in bytes per plane (even). */
static void viewsize(int w, int h, int rb, unsigned char FAR *buf)
{
    int y;
    vw = w; vh = h; vcx = w / 2; vcy = h / 2; rowb = rb; fb = buf;
    bh = h + HUDH;
    for (y = 0; y < bh && y < 200 + HUDH; ++y)
        rowoff[y] = (unsigned)(y * 4) * (unsigned)rb;
}

/* floor(n / d) for d > 0. */
static int fdiv(int n, int d)
{
    return n >= 0 ? n / d : -((-n + d - 1) / d);
}

/* Screen x of lateral position (2*X units of half squares) at depth
   z2 = 2*z (odd). */
static int sx(int twox, int z2)
{
    return vcx + fdiv(twox * (vw / 2), z2);
}

/* Rows y0..y1-1 in one shade; rows and planes are contiguous. */
static void bgrows(int y0, int y1, int sh)
{
#ifdef MAZE_HOST
    int y, p, i;
    unsigned char FAR *q;
    for (y = y0; y < y1; ++y)
        for (p = 0; p < 4; ++p) {
            q = fb + (unsigned)(y * 4 + p) * (unsigned)rowb;
            for (i = 0; i < rowb; ++i) q[i] = shade[sh][y & 7][p];
        }
#else
    unsigned char FAR *q = fb + rowoff[y0];
    unsigned char *pat;
    int y, words = rowb / 2;
#ifdef GDIHOOK
    if (gdc) { gdirect(y0, y1 - y0, 0, vw, sh, 0); return; }
#endif
    for (y = y0; y < y1; ++y) {
        pat = shade[sh][y & 7];
        _asm {
            push si
            push di
            les di, q
            mov si, pat
            mov dx, words
            mov bx, 4
        bgp:
            lodsb
            mov ah, al
            mov cx, dx
            rep stosw
            dec bx
            jnz bgp
            mov word ptr q, di
            pop di
            pop si
        }
    }
#endif
}

static void background(void)
{
    bgrows(0, vcy, SH_CEIL);
    bgrows(vcy, vh, SH_FLOOR);
}

/* Front face of the square at depth k, lateral l (negative = left). */
static void front(int k, int l, int sh)
{
    int z2 = 2 * k, xl = sx(2 * l - 1, z2), xr = sx(2 * l + 1, z2);
    int h = vcy / z2;
    if (xr <= 0 || xl >= vw || h < 1) return;
    hspan(vcy - h, xl, xr, SH_EDGE, SP_M);
    hrect(vcy - h + 1, h - 1, xl, xr, sh, SP_L | SP_R);
    hrect(vcy, h - 1, xl, xr, sh, SP_L | SP_R);
}

/* Side face of the square at depth k, lateral l != 0: the wall plane
   facing the centre column, from depth k to k+1 (clipped at 1/2). */
static void side(int k, int l, int sh)
{
    int a = l > 0 ? 2 * l - 1 : -(2 * l + 1);  /* |2X| of the plane      */
    int zn = k ? 2 * k : 1;                     /* near plane, half units */
    int xn = sx(a, zn) - vcx;                   /* near edge, from centre */
    int xf = sx(a, 2 * k + 2) - vcx;            /* far edge               */
    int num = a * vw, den = vh;                 /* edge slope dx/dy       */
    int q = num / den, r = num % den;
    int y, t, acc, cur, nxt, x0, top;

    if (xn <= xf || xf >= vw - vcx) return;
    top = vcy - vcy / zn;
    /* c(d) = ceil(d * num / den) is where row vcy-d starts to be covered;
       t/acc carry d*num/den as quotient and remainder (16-bit only). */
    t = q; acc = r;
    cur = t + (acc ? 1 : 0);                    /* c(1)                  */
    /* Rows covered across the whole face are one block per half, with a
       one-pixel edge at the far side; only the slanted rows go one by
       one (on an 8088 each fill call costs about 0.5 ms). */
    y = vcy - 1;
    while (y >= top && y >= 0 && cur <= xf) {
        t += q; acc += r;
        if (acc >= den) { ++t; acc -= den; }
        cur = t + (acc ? 1 : 0);
        --y;
    }
    if (y < vcy - 1) {
        int n = vcy - 1 - y;
        if (l > 0) {
            hrect(y + 1, n, vcx + xf, vcx + xn, sh, SP_L);
            hrect(vcy, n, vcx + xf, vcx + xn, sh, SP_L);
        } else {
            hrect(y + 1, n, vcx - xn, vcx - xf, sh, SP_R);
            hrect(vcy, n, vcx - xn, vcx - xf, sh, SP_R);
        }
    }
    for (; y >= top && y >= 0; --y) {
        t += q; acc += r;
        if (acc >= den) { ++t; acc -= den; }
        nxt = t + (acc ? 1 : 0);                /* c(d+1), row above     */
        x0 = cur > xf ? cur : xf;
        if (x0 >= xn) break;
        /* One edge pixel per row: on shallow slopes the outline is a
           dotted line, but the shading already shows the edge and this
           halves the fills (each costs about 0.5 ms on an 8088). */
        if (l > 0) hspan(y, vcx + x0, vcx + xn, sh, SP_L | SP_M);
        else hspan(y, vcx - xn, vcx - x0, sh, SP_R | SP_M);
        cur = nxt;
    }
}

/* Chalk mark on the floor of a visited square at depth k (k may be 0). */
static void mark(int k, int l)
{
    int z2 = 2 * k + 1, y, h, w, xc;
    xc = vcx + fdiv(2 * l * (vw / 2), z2);
    w = (vw / 2) / (z2 * 4);
    h = vcy / z2;
    if (w < 1 || h < 2) return;
    y = vcy + h - h / 4;
    span(y, xc - w, xc + w, SH_MARK);
    if (w > 2) span(y + 1, xc - w + 1, xc + w - 1, SH_MARK);
}

/* The squares in view, read once per frame by stepping pointers (no
   multiplies): cell[k][l + VDEPTH + 2] for depth 0..VDEPTH+1, lateral
   -(VDEPTH+2)..VDEPTH+2. Squares off the map read as wall. */
#define VW2 (2 * VDEPTH + 5)
static unsigned char cell[VDEPTH + 2][VW2], mk[VDEPTH + 2][VW2];

static void readview(void)
{
    int k, i, x0 = px, y0 = py, x, y;
    int fx = ddx[pdir], fy = ddy[pdir];
    int rx = ddx[(pdir + 1) & 3], ry = ddy[(pdir + 1) & 3];
    for (k = 0; k < VDEPTH + 2; ++k) {
        x = x0 - (VDEPTH + 2) * rx;
        y = y0 - (VDEPTH + 2) * ry;
        for (i = 0; i < VW2; ++i) {
            if (x < 0 || y < 0 || x >= msize || y >= msize) {
                cell[k][i] = B_WALL; mk[k][i] = 0;
            } else {
                cell[k][i] = grid[y][x];
                mk[k][i] = (unsigned char)
                    (seen[y][x] == 1 && grid[y][x] == B_OPEN);
            }
            x += rx; y += ry;
        }
        x0 += fx; y0 += fy;
    }
}

#define at(k, l) (cell[k][(l) + VDEPTH + 2])
#define markat(k, l) (mk[k][(l) + VDEPTH + 2])

/* Is (k,l) possibly visible: some open path of squares toward the eye.
   Cheap test that skips work hidden behind near walls. */
static unsigned char vis[VDEPTH + 2][2 * VDEPTH + 3];

static void visibility(void)
{
    int k, l, i, j, o;
    for (k = 0; k <= VDEPTH + 1; ++k)
        for (i = 0; i < 2 * VDEPTH + 3; ++i) vis[k][i] = 0;
    for (k = 0; k <= VDEPTH; ++k)
        for (j = 0; j <= 2 * (k + 1); ++j) {
            /* l = 0, -1, 1, -2, 2 ...: inner neighbours come first */
            l = (j + 1) / 2;
            if (j & 1) l = -l;
            i = l + VDEPTH + 1;
            o = l > 0 ? -1 : 1;                 /* toward the centre     */
            if (k == 0 && l == 0) { vis[k][i] = 1; continue; }
            if ((k > 0 && vis[k - 1][i] && at(k - 1, l) == B_OPEN) ||
                (l != 0 && vis[k][i + o] && at(k, l + o) == B_OPEN) ||
                (k > 0 && l != 0 && vis[k - 1][i + o] &&
                 at(k - 1, l + o) == B_OPEN))
                vis[k][i] = 1;
        }
}

static void render(void)
{
    int k, l, i, b, e;
    spans = 0;
    readview();
    background();
    visibility();
    for (k = VDEPTH; k >= 0; --k) {
        /* marks on open floor at this depth */
        for (l = -k; l <= k; ++l)
            if (vis[k][l + VDEPTH + 1] && markat(k, l)) mark(k, l);
        /* outermost first; nothing at one depth overlaps */
        for (i = k + 1; i >= 0; --i)
            for (e = -1; e <= 1; e += 2) {
                l = i * e;
                if (i == 0 && e > 0) continue;
                if (!vis[k][l + VDEPTH + 1]) continue;
                b = at(k, l);
                if (b == B_OPEN) continue;
                if (l != 0 && at(k, l > 0 ? l - 1 : l + 1) == B_OPEN)
                    side(k, l, b == B_EXIT ? SH_EXITS : SH_SIDE + k);
                if (k > 0 && at(k - 1, l) == B_OPEN)
                    front(k, l, b == B_EXIT ? SH_EXITF : SH_FRONT + k - 1);
            }
    }
}

/* ---- status text: a 5x7 font written straight into the buffer (GDI
   TextOut costs about 20 ms a character on an 8088 with these drivers) */
#include "FONT.H"

static int glyphat(char c)
{
    int i;
    for (i = 0; fontch[i]; ++i)
        if (fontch[i] == c) return i;
    return 0;
}

/* 5 font bits doubled to 10, left-aligned in 16 (for 640-wide modes). */
static unsigned wide2[32];

static void glyph(int x, int y, char c, int sh)
{
    int r, p, k = glyphat(c), b0 = x >> 3, s = x & 7, two;
    unsigned m;
    unsigned char hi, lo, pat, FAR *row;
    if (x < 0 || y < 0 || y + 7 > bh || b0 >= rowb) return;
    two = b0 + 1 < rowb;
    for (r = 0; r < 7; ++r) {
        if (gscale == 2) m = wide2[fontbits[k][r] >> 3] >> s;  /* s is 0 or 4 */
        else m = ((unsigned)fontbits[k][r] << 8) >> s;
        if (!m) continue;
        hi = (unsigned char)(m >> 8);
        lo = (unsigned char)m;
        row = fb + rowoff[y + r] + b0;
        for (p = 0; p < 4; ++p, row += rowb) {
            pat = shade[sh][(y + r) & 7][p];
            row[0] = (unsigned char)((row[0] & ~hi) | (pat & hi));
            if (lo && two)
                row[1] = (unsigned char)((row[1] & ~lo) | (pat & lo));
        }
    }
}

static int textw(const char *s)
{
    int n = 0;
    while (s[n]) ++n;
    return n ? n * 6 * gscale - gscale : 0;
}

static void textat(int x, int y, const char *s, int sh)
{
    int i, j;
    if (gscale == 2) {                          /* keep x on 4-pixel steps */
        x &= ~3;
        if (!wide2[1])
            for (i = 0; i < 32; ++i)
                for (j = 0; j < 5; ++j)
                    if (i & (16 >> j)) wide2[i] |= 0xC000u >> (2 * j);
    }
    for (; *s; ++s, x += 6 * gscale) glyph(x, y, *s, sh);
}

/* Black status line under the view. */
static void hudclear(void)
{
    bgrows(vh, bh, SH_CEIL);
}
