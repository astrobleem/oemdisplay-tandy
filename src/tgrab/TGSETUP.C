/* TGSETUP.EXE - install the Tandy grabber and Clipboard helper from DOS (MIT).
 *
 *   A:\TGSETUP [windows-dir]            install or update (default C:\WINDOWS)
 *   A:\TGSETUP /REMOVE [windows-dir]    undo: previous grabber, no TGCLIP
 *   A:\TGSETUP /CHECK [windows-dir]     report only, nothing is changed
 *
 * Run it from the packet (any drive or folder; it finds its files next to
 * itself) at a plain DOS prompt, with Windows not running. It
 *   - checks every packet file against TGSETUP.LST (size and CRC-32),
 *   - keeps the original SYSTEM.INI and WIN.INI in <windows>\TGBAK once,
 *   - copies TANDYGR.GR2 to <windows>\SYSTEM and TGCLIP.EXE to <windows>
 *     (written as .NEW, read back, then renamed),
 *   - sets [boot] 286grabber=TANDYGR.GR2 and adds <windows>\TGCLIP.EXE to
 *     [windows] load= (both INI files rewritten the same way; every other
 *     byte is kept),
 * and then Windows started by the usual launcher has the grabber and the
 * helper. Nothing in the launcher, CONFIG.SYS or AUTOEXEC.BAT changes; the
 * grabber itself needs no memory adjustment at startup (TGSRSCR.ASM).
 * Running it again updates the files and leaves the backup alone.
 * /REMOVE puts the grabber name from before the first install back, takes
 * TGCLIP out of load= and deletes the two copied files.
 *
 * Refuses (and changes nothing) inside Windows, with a Windows display mode
 * switch pending undo (XTMODE.JRN: run MODES, then retry), or when a file
 * check fails. Microsoft C, small model, 8086; C89.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <dos.h>
#include <direct.h>
#include <io.h>

#define PTH 80
#define MAXINI 16000U

static char pkt[PTH], win[PTH], sysdir[PTH], bak[PTH];
static char path[PTH], path2[PTH], path3[PTH];
static unsigned char buf[4096], buf2[4096];
static char ini[MAXINI + 1], out[MAXINI + 600];
static unsigned long crctab[256];

static void die(const char *msg, const char *detail)
{
    printf("TGSETUP: %s\n", msg);
    if (detail && *detail) printf("  %s\n", detail);
    printf("Nothing more was changed. Windows was not started.\n");
    exit(1);
}

static void join(char *o, const char *dir, const char *name)
{
    if (strlen(dir) + strlen(name) + 2 > PTH) die("Path too long.", dir);
    strcpy(o, dir);
    if (o[strlen(o) - 1] != '\\') strcat(o, "\\");
    strcat(o, name);
}

static int exists(const char *p)
{
    unsigned a;
    return _dos_getfileattr(p, &a) == 0;
}

static void not_windows(void)
{
    union REGS r;
    r.x.ax = 0x1600; int86(0x2f, &r, &r);
    if (r.h.al && r.h.al != 0x80) die("Exit Windows completely first.", "");
    r.x.ax = 0x4680; int86(0x2f, &r, &r);
    if (!r.x.ax) die("Exit Windows completely first.", "");
}

static void crcinit(void)
{
    unsigned long c; int n, k;
    for (n = 0; n < 256; n++) {
        c = (unsigned long)n;
        for (k = 0; k < 8; k++) c = (c & 1) ? 0xEDB88320UL ^ (c >> 1) : c >> 1;
        crctab[n] = c;
    }
}

/* size and CRC-32 of a file; -1 size if it cannot be read */
static long filecrc(const char *p, unsigned long *crc)
{
    FILE *f = fopen(p, "rb");
    unsigned long c = 0xFFFFFFFFUL; long size = 0; size_t n, i;
    if (!f) return -1L;
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0) {
        for (i = 0; i < n; i++) c = crctab[(c ^ buf[i]) & 0xFF] ^ (c >> 8);
        size += (long)n;
    }
    if (ferror(f)) { fclose(f); return -1L; }
    fclose(f);
    *crc = c ^ 0xFFFFFFFFUL;
    return size;
}

static int samefile(const char *a, const char *b)
{
    FILE *f = fopen(a, "rb"), *g = fopen(b, "rb");
    size_t n, m; int same = f && g;
    while (same) {
        n = fread(buf, 1, sizeof(buf), f);
        m = fread(buf2, 1, sizeof(buf2), g);
        if (n != m || memcmp(buf, buf2, n)) same = 0;
        if (n == 0) break;
    }
    if (f) { if (ferror(f)) same = 0; fclose(f); }
    if (g) { if (ferror(g)) same = 0; fclose(g); }
    return same;
}

static void copyfile(const char *from, const char *to)
{
    FILE *f = fopen(from, "rb"), *g;
    size_t n;
    if (!f) die("Cannot read", from);
    g = fopen(to, "wb");
    if (!g) { fclose(f); die("Cannot create", to); }
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0)
        if (fwrite(buf, 1, n, g) != n) { fclose(f); fclose(g); remove(to); die("Write failed (disk full?)", to); }
    if (ferror(f)) { fclose(f); fclose(g); remove(to); die("Read failed", from); }
    fclose(f);
    if (fclose(g)) { remove(to); die("Write failed (disk full?)", to); }
    if (!samefile(from, to)) { remove(to); die("Copy does not read back equal", to); }
}

/* copy via NAME.NEW, then replace the target */
static void install_file(const char *from, const char *dir, const char *name)
{
    char nw[PTH], dst[PTH], *dot;
    join(dst, dir, name);
    strcpy(nw, dst);
    dot = strrchr(nw, '.');
    if (dot && dot > strrchr(nw, '\\')) strcpy(dot, ".NEW"); else strcat(nw, ".NEW");
    if (exists(nw) && remove(nw)) die("Cannot remove an old", nw);
    copyfile(from, nw);
    if (exists(dst) && remove(dst)) { remove(nw); die("Cannot replace", dst); }
    if (rename(nw, dst)) die("Cannot rename into place", dst);
    if (!samefile(from, dst)) die("Installed file does not read back equal", dst);
    printf("  %s\n", dst);
}

static unsigned readini(const char *p)
{
    FILE *f = fopen(p, "rb");
    size_t n;
    if (!f) die("Cannot read", p);
    n = fread(ini, 1, MAXINI + 1, f);
    if (ferror(f)) { fclose(f); die("Cannot read", p); }
    fclose(f);
    if (n > MAXINI) die("INI file too large", p);
    ini[n] = 0;
    if (strlen(ini) != n) die("INI file contains a zero byte", p);
    return (unsigned)n;
}

/* Find "key=" (case-insensitive, at line start) inside [section].
 * Returns the offset of the value and sets *vend to the end of the value
 * (before CR/LF), or -1. *secend = offset after the section's last line. */
static long findkey(const char *sect, const char *key, unsigned *vend, unsigned *secend)
{
    unsigned i = 0, n = strlen(ini), ls, k, kl = strlen(key), sl = strlen(sect);
    int in = 0; long found = -1;
    *secend = 0;
    while (i < n) {
        ls = i;
        while (i < n && ini[i] != '\n') i++;
        if (i < n) i++;
        k = ls;
        while (k < i && (ini[k] == ' ' || ini[k] == '\t')) k++;
        if (ini[k] == '[') {
            in = (k + sl + 2 <= n && ini[k + sl + 1] == ']' && !strnicmp(ini + k + 1, sect, sl));
            if (in) *secend = i;
            continue;
        }
        if (!in) continue;
        if (ini[k] != ';' && ini[k] != '\r' && ini[k] != '\n') *secend = i;
        if (found < 0 && !strnicmp(ini + k, key, kl)) {
            unsigned j = k + kl;
            while (j < i && (ini[j] == ' ' || ini[j] == '\t')) j++;
            if (j < i && ini[j] == '=') {
                unsigned e;
                j++;
                e = j;
                while (e < n && ini[e] != '\r' && ini[e] != '\n') e++;
                *vend = e;
                found = (long)j;
            }
        }
    }
    return found;
}

/* write out[] (len bytes) to p via NAME.TGN, read back, then replace */
static void writeini(const char *p, unsigned len)
{
    char nw[PTH], old[PTH];
    FILE *f;
    strcpy(nw, p); strcpy(strrchr(nw, '.'), ".TGN");
    strcpy(old, p); strcpy(strrchr(old, '.'), ".TGO");
    if (exists(nw)) remove(nw);
    if (exists(old)) die("A previous INI update was interrupted; restore it from", old);
    f = fopen(nw, "wb");
    if (!f) die("Cannot create", nw);
    if (fwrite(out, 1, len, f) != len || fclose(f)) { remove(nw); die("Write failed (disk full?)", nw); }
    f = fopen(nw, "rb");
    if (!f) die("Cannot reread", nw);
    {
        unsigned done = 0; size_t n;
        while ((n = fread(buf, 1, sizeof(buf), f)) > 0) {
            if (done + n > len || memcmp(buf, out + done, n)) { fclose(f); remove(nw); die("INI does not read back equal", nw); }
            done += (unsigned)n;
        }
        fclose(f);
        if (done != len) { remove(nw); die("INI does not read back equal", nw); }
    }
    if (rename(p, old)) { remove(nw); die("Cannot rename", p); }
    if (rename(nw, p)) { rename(old, p); die("Cannot rename", nw); }
    if (remove(old)) die("Cannot remove", old);
}

/* replace [sect] key's value with val (adds "key=val" at the end of the
 * section, or a new section, if missing) */
static unsigned setvalue(const char *sect, const char *key, const char *val)
{
    unsigned vend, secend, n = strlen(ini), len;
    long at = findkey(sect, key, &vend, &secend);
    if (at >= 0) {
        len = (unsigned)at;
        memcpy(out, ini, len);
        strcpy(out + len, val);
        len += strlen(val);
        memcpy(out + len, ini + vend, n - vend);
        return len + (n - vend);
    }
    if (secend) {
        memcpy(out, ini, secend);
        len = secend;
        if (len && out[len - 1] != '\n') { out[len++] = '\r'; out[len++] = '\n'; }
        sprintf(out + len, "%s=%s\r\n", key, val);
        len += strlen(out + len);
        memcpy(out + len, ini + secend, n - secend);
        return len + (n - secend);
    }
    memcpy(out, ini, n);
    len = n;
    if (len && out[len - 1] != '\n') { out[len++] = '\r'; out[len++] = '\n'; }
    sprintf(out + len, "[%s]\r\n%s=%s\r\n", sect, key, val);
    return len + strlen(out + len);
}

static void getvalue(const char *sect, const char *key, char *val, unsigned cb)
{
    unsigned vend, secend, k;
    long at = findkey(sect, key, &vend, &secend);
    val[0] = 0;
    if (at < 0) return;
    k = vend - (unsigned)at;
    if (k >= cb) k = cb - 1;
    memcpy(val, ini + (unsigned)at, k);
    val[k] = 0;
    while (k && (val[k - 1] == ' ' || val[k - 1] == '\t')) val[--k] = 0;
}

/* does a load= list contain TGCLIP (any path, any case)? */
static char *hasclip(char *list)
{
    char *p;
    for (p = list; *p; p++)
        if (!strnicmp(p, "TGCLIP", 6) && (p == list || p[-1] == ' ' || p[-1] == '\\' || p[-1] == ',' || p[-1] == ':'))
            return p;
    return NULL;
}

static void checkpacket(void)
{
    FILE *f;
    char line[120], name[20];
    long size, got;
    unsigned long crc, have;
    int n = 0;
    join(path, pkt, "TGSETUP.LST");
    f = fopen(path, "r");
    if (!f) die("Packet list missing; run TGSETUP from the complete packet.", path);
    while (fgets(line, sizeof(line), f)) {
        if (line[0] == ';' || line[0] == '\n') continue;
        if (sscanf(line, "%12s %ld %lx", name, &size, &crc) != 3) { fclose(f); die("Bad packet list line", line); }
        join(path, pkt, name);
        got = filecrc(path, &have);
        if (got != size || have != crc) { fclose(f); die("Packet file missing or damaged; copy the packet again.", path); }
        n++;
    }
    fclose(f);
    if (n < 2) die("Packet list incomplete.", "");
    printf("Packet: %d files checked.\n", n);
}

static void paths(int argc, char **argv, int first)
{
    char *s;
    strcpy(pkt, argv[0]);
    s = strrchr(pkt, '\\');
    if (!s) die("Cannot find the packet folder.", argv[0]);
    s[1] = 0;
    if (strlen(pkt) > 3) s[0] = 0;          /* keep "A:\" */
    strcpy(win, argc > first ? argv[first] : "C:\\WINDOWS");
    strupr(win);
    if (strlen(win) > 3 && win[strlen(win) - 1] == '\\') win[strlen(win) - 1] = 0;
    join(sysdir, win, "SYSTEM");
    join(bak, win, "TGBAK");
    join(path, win, "WIN.COM");
    join(path2, win, "SYSTEM.INI");
    join(path3, win, "WIN.INI");
    if (!exists(path) || !exists(path2) || !exists(path3) || !exists(sysdir))
        die("Windows 3.0 not found in this folder (WIN.COM, SYSTEM.INI, WIN.INI, SYSTEM).", win);
}

static void report(void)
{
    char g[40], l[256];
    join(path, win, "SYSTEM.INI"); readini(path); getvalue("boot", "286grabber", g, sizeof(g));
    join(path, win, "WIN.INI"); readini(path); getvalue("windows", "load", l, sizeof(l));
    printf("286grabber=%s\nload=%s\n", g, l);
    join(path, bak, "DONE.TAG");
    printf("Backup %s: %s\n", bak, exists(path) ? "present" : "none");
}

static void install(void)
{
    char g[40], l[256], val[PTH + 260], clip[PTH];
    unsigned len;
    FILE *f;
    join(path, win, "XTMODE.JRN");
    if (exists(path))
        die("A display mode change can still be undone (XTMODE.JRN). Run C:\\WINXT\\MODES,\n"
            "  keep or undo that change, then run TGSETUP again.", path);
    checkpacket();
    join(path, bak, "DONE.TAG");
    if (!exists(path)) {
        if (!exists(bak) && mkdir(bak)) die("Cannot create the backup folder", bak);
        join(path, win, "SYSTEM.INI"); join(path2, bak, "SYSTEM.INI"); copyfile(path, path2);
        join(path, win, "WIN.INI"); join(path2, bak, "WIN.INI"); copyfile(path, path2);
        join(path, win, "SYSTEM.INI"); readini(path); getvalue("boot", "286grabber", g, sizeof(g));
        join(path, bak, "OLDGRAB.TXT");
        f = fopen(path, "w");
        if (!f || fprintf(f, "%s\n", g) < 0 || fclose(f)) die("Cannot write", path);
        join(path2, pkt, "TGSETUP.EXE"); join(path3, bak, "TGSETUP.EXE"); copyfile(path2, path3);
        join(path, bak, "DONE.TAG");
        f = fopen(path, "w");
        if (!f || fprintf(f, "Original SYSTEM.INI and WIN.INI kept before the first TGSETUP.\n") < 0 || fclose(f))
            die("Cannot write", path);
        printf("Backup: %s (undo: %s\\TGSETUP /REMOVE %s)\n", bak, bak, win);
    } else
        printf("Backup from the first install kept: %s\n", bak);
    printf("Installing:\n");
    join(path, pkt, "TANDYGR.GR2"); install_file(path, sysdir, "TANDYGR.GR2");
    join(path, pkt, "TGCLIP.EXE"); install_file(path, win, "TGCLIP.EXE");
    join(path, win, "SYSTEM.INI"); readini(path); getvalue("boot", "286grabber", g, sizeof(g));
    if (stricmp(g, "TANDYGR.GR2")) {
        len = setvalue("boot", "286grabber", "TANDYGR.GR2");
        writeini(path, len);
        printf("  SYSTEM.INI: 286grabber=TANDYGR.GR2 (was %s)\n", g[0] ? g : "not set");
    } else
        printf("  SYSTEM.INI: 286grabber=TANDYGR.GR2 already\n");
    join(path, win, "WIN.INI"); readini(path); getvalue("windows", "load", l, sizeof(l));
    join(clip, win, "TGCLIP.EXE");
    if (!hasclip(l)) {
        if (strlen(l) + strlen(clip) + 2 > 250) die("WIN.INI load= is too long to add TGCLIP.", l);
        strcpy(val, l);
        if (val[0]) strcat(val, " ");
        strcat(val, clip);
        len = setvalue("windows", "load", val);
        writeini(path, len);
        printf("  WIN.INI: load=%s\n", val);
    } else
        printf("  WIN.INI: TGCLIP is already in load=\n");
    printf("Done. Start Windows as usual (for Windows XT: C:\\WINXT\\WINXT).\n"
           "Print Screen (Shift+PRINT) in a DOS program copies its screen to the Clipboard.\n");
}

static void uninstall(void)
{
    char g[40], l[256], *p, *e;
    unsigned len;
    FILE *f;
    join(path, bak, "DONE.TAG");
    if (!exists(path)) die("No TGSETUP backup in this Windows folder.", bak);
    join(path, bak, "OLDGRAB.TXT");
    f = fopen(path, "r");
    if (!f || !fgets(g, sizeof(g), f)) die("Cannot read", path);
    fclose(f);
    if ((p = strchr(g, '\n')) != NULL) *p = 0;
    join(path, win, "SYSTEM.INI"); readini(path);
    len = setvalue("boot", "286grabber", g);
    writeini(path, len);
    printf("SYSTEM.INI: 286grabber=%s\n", g);
    join(path, win, "WIN.INI"); readini(path); getvalue("windows", "load", l, sizeof(l));
    while ((p = hasclip(l)) != NULL) {
        char *s = p;
        while (s > l && s[-1] != ' ' && s[-1] != ',') s--;
        e = p;
        while (*e && *e != ' ' && *e != ',') e++;
        while (*e == ' ' || *e == ',') e++;
        memmove(s, e, strlen(e) + 1);
    }
    len = strlen(l);
    while (len && l[len - 1] == ' ') l[--len] = 0;
    len = setvalue("windows", "load", l);
    writeini(path, len);
    printf("WIN.INI: load=%s\n", l);
    join(path, sysdir, "TANDYGR.GR2"); if (exists(path) && remove(path)) die("Cannot delete", path);
    join(path, win, "TGCLIP.EXE"); if (exists(path) && remove(path)) die("Cannot delete", path);
    join(path, bak, "DONE.TAG"); join(path2, bak, "REMOVED.TAG");
    if (exists(path2)) remove(path2);
    if (rename(path, path2)) die("Cannot mark the backup removed", path);
    printf("Removed. The original INI files stay in %s.\n", bak);
}

int main(int argc, char **argv)
{
    int first = 1, mode = 0;
    crcinit();
    if (argc > 1 && argv[1][0] == '/') {
        if (!stricmp(argv[1], "/REMOVE")) mode = 1;
        else if (!stricmp(argv[1], "/CHECK")) mode = 2;
        else { puts("TGSETUP [windows-dir] | /REMOVE [windows-dir] | /CHECK [windows-dir]"); return 2; }
        first = 2;
    }
    if (argc > first + 1) { puts("TGSETUP [windows-dir] | /REMOVE [windows-dir] | /CHECK [windows-dir]"); return 2; }
    puts("Tandy grabber and Clipboard helper setup (Windows 3.0 real mode)");
    not_windows();
    paths(argc, argv, first);
    if (mode == 2) report();
    else if (mode == 1) uninstall();
    else install();
    return 0;
}
