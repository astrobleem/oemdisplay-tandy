/* T80SET.C - reversible TEXT80 setup for Windows 3.0 (DOS program; C89,
 * Microsoft C small model). Run at the DOS prompt, never inside Windows.
 *
 *   T80SET ON  <windows dir> <driver.drv> [<helper.exe>] [/C]
 *   T80SET OFF <windows dir>
 *   T80SET RESTORE <windows dir>
 *   T80SET SHOW <windows dir>
 *
 * ON refuses if <dir>\SYSTEM.T80, WIN.T80 or T80SET.STA exists (already set
 * up). It changes only these lines:
 *   SYSTEM.INI [boot]: display.drv=<driver>, fonts.fon=XTTSYS.FON,
 *     fixedfon.fon=XTCFIX.FON, oemfonts.fon=XTCOEM.FON (the 8x8 fonts);
 *     a line that already has the value is left as it is;
 *   WIN.INI [windows]: load= gains <helper> at its end (existing entries
 *     kept; nothing if already listed or no helper given);
 *   WIN.INI [fonts]: two lines ADDED, none removed:
 *     Helv 8x8 (TEXT80)=T80HELV.FON and Courier 8x8 (TEXT80)=T80COUR.FON;
 *   /C (compact UI profile): WIN.INI [windows] BorderWidth=7 (sizing frames
 *     one text cell thick) and GridGranularity=1 (windows move and size on
 *     the 8-pixel grid), set like the [boot] keys and undone by OFF the same
 *     way.
 * Every change it made is written to T80SET.STA (each changed line with the
 * line it replaced). SYSTEM.T80 and WIN.T80 are byte-for-byte copies of the
 * files before ON, kept as a safety net.
 *
 * OFF undoes exactly those changes in the files as they are now: a line ON
 * set is put back as it was (or removed, if ON added it) only while it still
 * has the value ON gave it; added lines and the helper are removed. Every
 * other setting, including ones changed since ON, stays. Then T80SET.STA and
 * the copies are deleted. If T80SET.STA is missing, incomplete (it ends
 * with an END line giving the number of changes) or damaged, OFF changes
 * nothing and keeps every file. RESTORE, asked for explicitly, copies
 * SYSTEM.T80 and WIN.T80 back whole (the files exactly as before ON,
 * losing changes made since) and deletes them. The helper is matched as a
 * whole load= entry (XTPAN.EXE, not the end of MYXTPAN.EXE).
 *
 * Files are never edited in place. New contents go to SYSTEM.T8N/WIN.T8N;
 * then for each file the live one is renamed .T8O and the new one renamed
 * live; if any step fails, every file renamed so far is renamed back. Only
 * when both are in place are the .T8O files deleted, and the backups are
 * deleted only after that. If a step fails and putting things back fails
 * too, nothing more is deleted and the message names the files to copy
 * back by hand. Exit code 0 on success, 1 on any error.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <io.h>

#ifndef SEP
#define SEP "\\"                /* the host test (T80SETT.PY) builds with "/" */
#endif
#define MAXF 24000
#define MAXE 12
static char inbuf[MAXF + 1];
static char outbuf[MAXF + 600];
static const char *dir;

/* one change ON made: kind 'K' (a key set: key, value ON wrote, the line it
 * replaced or "" if ON inserted it), 'A' (a line added), 'L' (the helper
 * appended to load=; orig "-" if ON created the load= line) */
typedef struct {
    char kind, file;            /* file 'S' SYSTEM.INI, 'W' WIN.INI */
    char sec[24];
    char key[40];
    char val[64];
    char orig[200];
} ENT;
static ENT ent[MAXE];
static int nent;

static int exists(const char *p)
{
    return access(p, 0) == 0;
}

static void join(char *out, const char *d, const char *name)
{
    strcpy(out, d);
    if (out[0] && out[strlen(out) - 1] != SEP[0] && out[strlen(out) - 1] != ':')
        strcat(out, SEP);
    strcat(out, name);
}

static char *in(const char *name)
{
    static char p[4][160];
    static int k;
    k = (k + 1) & 3;
    join(p[k], dir, name);
    return p[k];
}

static int copyfile(const char *from, const char *to)
{
    FILE *a, *b;
    int c, ok = 1;
    a = fopen(from, "rb");
    if (!a)
        return 0;
    b = fopen(to, "wb");
    if (!b) {
        fclose(a);
        return 0;
    }
    while ((c = getc(a)) != EOF)
        if (putc(c, b) == EOF) {
            ok = 0;
            break;
        }
    if (ferror(a))
        ok = 0;
    fclose(a);
    if (fclose(b) != 0)
        ok = 0;
    if (!ok)
        remove(to);
    return ok;
}

static int samefile(const char *x, const char *y)
{
    FILE *a = fopen(x, "rb"), *b = fopen(y, "rb");
    int c, d, same = a && b;
    while (same) {
        c = getc(a);
        d = getc(b);
        if (c != d)
            same = 0;
        if (c == EOF || d == EOF)
            break;
    }
    if (a)
        fclose(a);
    if (b)
        fclose(b);
    return same;
}

static int readfile(const char *p)
{
    FILE *f = fopen(p, "rb");
    int n;
    if (!f)
        return -1;
    n = fread(inbuf, 1, MAXF, f);
    if (!feof(f) && getc(f) != EOF) {
        fclose(f);
        return -1;                       /* too large */
    }
    fclose(f);
    inbuf[n] = 0;
    if ((int)strlen(inbuf) != n)
        return -1;                       /* a NUL byte: not an INI file */
    return n;
}

/* write data to p (a new file) and read it back */
static int writenew(const char *p, const char *data)
{
    FILE *f = fopen(p, "wb");
    int n = strlen(data), ok;
    if (!f)
        return 0;
    ok = (int)fwrite(data, 1, n, f) == n;
    if (fclose(f) != 0)
        ok = 0;
    if (ok && (readfile(p) != n || strcmp(inbuf, data) != 0))
        ok = 0;
    if (!ok)
        remove(p);
    return ok;
}

/* ---- the two-file swap ----------------------------------------------------
 * For SYSTEM.INI and WIN.INI with new contents in <name>.T8N: rename the live
 * file to .T8O, the new one to live. Any failure renames back what was
 * renamed. Returns 1 done, 0 failed and everything back as it was, -1 failed
 * and could not put everything back (nothing deleted; message printed). */
static const char *LIVE[2] = {"SYSTEM.INI", "WIN.INI"};
static const char *NEWF[2] = {"SYSTEM.T8N", "WIN.T8N"};
static const char *OLDF[2] = {"SYSTEM.T8O", "WIN.T8O"};

static int swap2(void)
{
    int i, step = 0, ok = 1;
    for (i = 0; i < 2 && ok; i++) {
        if (rename(in(LIVE[i]), in(OLDF[i])) != 0) {
            ok = 0;
            break;
        }
        step++;
        if (rename(in(NEWF[i]), in(LIVE[i])) != 0) {
            ok = 0;
            break;
        }
        step++;
    }
    if (ok) {
        remove(in(OLDF[0]));
        remove(in(OLDF[1]));
        return 1;
    }
    /* undo: step counts renames done, in order live->old, new->live, ... */
    while (step > 0) {
        i = (step - 1) / 2;
        if (step % 2 == 0) {            /* new was renamed live: back to new */
            if (rename(in(LIVE[i]), in(NEWF[i])) != 0)
                break;
        } else {                        /* live was renamed old: back to live */
            if (rename(in(OLDF[i]), in(LIVE[i])) != 0)
                break;
        }
        step--;
    }
    if (step > 0) {
        printf("T80SET: could not put the files back. In %s: if SYSTEM.INI or WIN.INI\n"
               "is missing, rename SYSTEM.T8O or WIN.T8O to it; SYSTEM.T80 and WIN.T80\n"
               "hold the files as they were before T80SET ON.\n", dir);
        return -1;
    }
    remove(in(NEWF[0]));
    remove(in(NEWF[1]));
    return 0;
}

static int stale(void)
{
    int i;
    for (i = 0; i < 2; i++)
        if (exists(in(NEWF[i])) || exists(in(OLDF[i]))) {
            printf("T80SET: %s or %s is left from an interrupted run: check that\n"
                   "SYSTEM.INI and WIN.INI are complete, then delete them.\n", NEWF[i], OLDF[i]);
            return 1;
        }
    return 0;
}

/* ---- lines ---------------------------------------------------------------- */
static void chomp(char *s)
{
    char *e = s + strlen(s);
    while (e > s && (e[-1] == '\n' || e[-1] == '\r'))
        *--e = 0;
}

static int keyis(const char *line, const char *key)
{
    int n = strlen(key);
    while (*line == ' ' || *line == '\t')
        line++;
    if (strnicmp(line, key, n) != 0)
        return 0;
    line += n;
    while (*line == ' ' || *line == '\t')
        line++;
    return *line == '=';
}

/* the value after '=', without spaces around it or the line end */
static void valueof(const char *line, char *out, int size)
{
    const char *p = strchr(line, '=');
    int n;
    out[0] = 0;
    if (!p)
        return;
    p++;
    while (*p == ' ' || *p == '\t')
        p++;
    n = 0;
    while (p[n] && p[n] != '\r' && p[n] != '\n' && n < size - 1) {
        out[n] = p[n];
        n++;
    }
    out[n] = 0;
    while (n > 0 && (out[n - 1] == ' ' || out[n - 1] == '\t'))
        out[--n] = 0;
}

static int sameline(const char *a, const char *b)
{
    static char x[300], y[300];         /* static: a 2 KB DOS stack */
    strncpy(x, a, sizeof(x) - 1);
    x[sizeof(x) - 1] = 0;
    strncpy(y, b, sizeof(y) - 1);
    y[sizeof(y) - 1] = 0;
    chomp(x);
    chomp(y);
    return stricmp(x, y) == 0;
}

static ENT *add(char kind, char file, const char *sec, const char *key, const char *val, const char *orig)
{
    ENT *e;
    if (nent >= MAXE)
        return NULL;
    e = &ent[nent++];
    e->kind = kind;
    e->file = file;
    strncpy(e->sec, sec, sizeof(e->sec) - 1);
    e->sec[sizeof(e->sec) - 1] = 0;
    strncpy(e->key, key, sizeof(e->key) - 1);
    e->key[sizeof(e->key) - 1] = 0;
    strncpy(e->val, val, sizeof(e->val) - 1);
    e->val[sizeof(e->val) - 1] = 0;
    strncpy(e->orig, orig, sizeof(e->orig) - 1);
    e->orig[sizeof(e->orig) - 1] = 0;
    chomp(e->orig);
    return e;
}

/* the load= entry equal to helper (case-insensitive, a whole entry between
 * spaces or tabs, not part of a longer name such as MYXTPAN.EXE): its offset
 * in line, or -1 */
static int entry(const char *line, const char *helper)
{
    const char *p = strchr(line, '='), *s;
    int n = strlen(helper);
    if (!p)
        return -1;
    for (p++;;) {
        while (*p == ' ' || *p == '\t')
            p++;
        if (!*p || *p == '\r' || *p == '\n')
            return -1;
        s = p;
        while (*p && *p != ' ' && *p != '\t' && *p != '\r' && *p != '\n')
            p++;
        if (p - s == n && strnicmp(s, helper, n) == 0)
            return s - line;
    }
}

/* ON: edit one section of inbuf into outbuf (then back into inbuf).
 * set[i] = "key=value" (replaced where the key is, inserted at the section's
 * end if missing; left alone if it already has the value); addl[i] = lines
 * added if not present (case-insensitive); helper appended to load=.
 * Every change is recorded in ent[] for file f. 0: no such section, a line
 * too long, or the file would grow too large. */
static int edit(char f, const char *section, const char **set, int nset, const char **addl, int nadd,
                const char *helper)
{
    char *p = inbuf, *o = outbuf, *eol;
    static char line[300], v[64], k[40];
    int insec = 0, found = 0, i, seen[8], have[8], loaddone = 0;
    for (i = 0; i < 8; i++)
        seen[i] = have[i] = 0;
    for (;;) {
        int len, last = 0;
        if (*p) {
            eol = strchr(p, '\n');
            len = eol ? (int)(eol - p + 1) : (int)strlen(p);
            if (len >= (int)sizeof(line) - 2)
                return 0;
            memcpy(line, p, len);
            line[len] = 0;
            p += len;
        } else
            last = 1;
        if (last || line[0] == '[') {
            if (insec) {                 /* leaving the section: insert what is missing */
                if (o > outbuf && o[-1] != '\n')
                    o += sprintf(o, "\r\n");   /* last line without an end (stays after OFF) */
                for (i = 0; i < nset; i++)
                    if (!seen[i]) {
                        o += sprintf(o, "%s\r\n", set[i]);
                        strcpy(k, set[i]);
                        *strchr(k, '=') = 0;
                        add('K', f, section, k, strchr(set[i], '=') + 1, "");
                    }
                for (i = 0; i < nadd; i++)
                    if (!have[i]) {
                        o += sprintf(o, "%s\r\n", addl[i]);
                        add('A', f, section, "", "", addl[i]);
                    }
                if (helper && !loaddone) {
                    o += sprintf(o, "load=%s\r\n", helper);
                    add('L', f, section, "load", helper, "-");
                }
                insec = 0;
            }
            if (last)
                break;
            if (strnicmp(line, section, strlen(section)) == 0) {
                insec = found = 1;
                strcpy(o, line);
                o += len;
                if (o[-1] != '\n')
                    return 0;
                continue;
            }
        } else if (insec) {
            for (i = 0; i < nset; i++) {
                strncpy(k, set[i], sizeof(k) - 1);
                k[sizeof(k) - 1] = 0;
                *strchr(k, '=') = 0;
                if (!seen[i] && keyis(line, k)) {
                    seen[i] = 1;
                    valueof(line, v, sizeof(v));
                    if (stricmp(v, strchr(set[i], '=') + 1) == 0)
                        goto keep;
                    o += sprintf(o, "%s\r\n", set[i]);
                    add('K', f, section, k, strchr(set[i], '=') + 1, line);
                    goto next;
                }
            }
            for (i = 0; i < nadd; i++)
                if (sameline(line, addl[i]))
                    have[i] = 1;
            if (helper && !loaddone && keyis(line, "load")) {
                static char upper[300];
                char *e;
                loaddone = 1;
                if (entry(line, helper) >= 0)
                    goto keep;
                strcpy(upper, line);
                chomp(upper);
                e = line + strlen(upper);         /* keep the line's own ending */
                o += sprintf(o, "%s%s%s%s", upper, upper[strlen(upper) - 1] == '=' ? "" : " ", helper,
                             *e ? e : "\r\n");
                add('L', f, section, "load", helper, upper);
                goto next;
            }
        }
    keep:
        strcpy(o, line);
        o += len;
    next:
        if (o - outbuf > MAXF - 300)
            return 0;
    }
    *o = 0;
    if (!found)
        return 0;
    strcpy(inbuf, outbuf);
    return 1;
}

/* OFF: undo the ent[] changes for file f in inbuf (the file as it is now).
 * Returns the number of changes left in place because the line has been
 * changed since ON (those are reported). */
static int undo(char f)
{
    char *p = inbuf, *o = outbuf, *eol;
    static char line[300], v[64], sec[24];
    int i, len, kept = 0, done[MAXE];
    sec[0] = 0;
    for (i = 0; i < nent; i++)
        done[i] = ent[i].file != f;
    while (*p) {
        eol = strchr(p, '\n');
        len = eol ? (int)(eol - p + 1) : (int)strlen(p);
        if (len >= (int)sizeof(line) - 2) {
            memcpy(o, p, len);              /* too long to be ours: keep */
            o += len;
            p += len;
            continue;
        }
        memcpy(line, p, len);
        line[len] = 0;
        p += len;
        if (line[0] == '[') {
            strncpy(sec, line, sizeof(sec) - 1);
            sec[sizeof(sec) - 1] = 0;
        } else
            for (i = 0; i < nent; i++) {
                ENT *e = &ent[i];
                if (done[i] || strnicmp(sec, e->sec, strlen(e->sec)) != 0)
                    continue;
                if (e->kind == 'K' && keyis(line, e->key)) {
                    done[i] = 1;
                    valueof(line, v, sizeof(v));
                    if (stricmp(v, e->val) != 0) {
                        printf("T80SET: %s %s %s was changed since ON: left as it is\n",
                               f == 'S' ? "SYSTEM.INI" : "WIN.INI", e->sec, e->key);
                        kept++;
                        break;
                    }
                    if (e->orig[0])
                        o += sprintf(o, "%s\r\n", e->orig);
                    goto dropped;
                }
                if (e->kind == 'A' && sameline(line, e->orig)) {
                    done[i] = 1;
                    goto dropped;
                }
                if (e->kind == 'L' && keyis(line, "load")) {
                    static char cur[300];
                    int hl = strlen(e->val), at;
                    done[i] = 1;
                    strcpy(cur, line);
                    chomp(cur);
                    at = entry(cur, e->val);
                    if (at < 0)
                        break;                      /* already gone */
                    if (strcmp(e->orig, "-") == 0 && stricmp(strchr(cur, '=') + 1, e->val) == 0)
                        goto dropped;               /* ON made this line: remove it */
                    {
                        int from = at, to = at + hl;
                        char *end = line;
                        if (from > 0 && cur[from - 1] == ' ')
                            from--;                 /* the space ON put before it */
                        else if (cur[to] == ' ')
                            to++;
                        memmove(cur + from, cur + to, strlen(cur + to) + 1);
                        while (*end && *end != '\r' && *end != '\n')
                            end++;
                        o += sprintf(o, "%s%s", cur, end);    /* the line's own ending */
                    }
                    goto dropped;
                }
            }
        strcpy(o, line);
        o += len;
    dropped:
        if (o - outbuf > MAXF + 300)
            return -1;
    }
    *o = 0;
    for (i = 0; i < nent; i++)
        if (!done[i] && ent[i].kind == 'K')
            printf("T80SET: %s %s %s is no longer there: nothing to undo\n",
                   f == 'S' ? "SYSTEM.INI" : "WIN.INI", ent[i].sec, ent[i].key);
    strcpy(inbuf, outbuf);
    return kept;
}

/* ---- the record of changes (T80SET.STA): one change per line,
 * kind TAB file TAB section TAB key TAB value TAB original line ---------- */
static int savestate(const char *p)
{
    int i;
    char *o = outbuf;
    o += sprintf(o, "T80SET 2\r\n");
    for (i = 0; i < nent; i++)
        o += sprintf(o, "%c\t%c\t%s\t%s\t%s\t%s\r\n", ent[i].kind, ent[i].file, ent[i].sec, ent[i].key,
                     ent[i].val, ent[i].orig);
    o += sprintf(o, "END %d\r\n", nent);       /* a complete record ends so */
    return writenew(p, outbuf);
}

/* 1 only for a complete record: the header, whole change lines, and the
 * END line with their number (a truncated file is refused, so OFF never
 * deletes the copies on the strength of it) */
static int loadstate(const char *p)
{
    char *s, *f[6], *eol;
    int i, ended = 0;
    nent = 0;
    if (readfile(p) < 0 || strncmp(inbuf, "T80SET 2", 8) != 0)
        return 0;
    s = strchr(inbuf, '\n');
    while (s && *++s) {
        eol = strchr(s, '\n');
        if (eol)
            *eol = 0;
        chomp(s);
        if (ended && *s)
            return 0;                       /* anything after END */
        if (strncmp(s, "END ", 4) == 0) {
            if (atoi(s + 4) != nent || !eol)
                return 0;
            ended = 1;
        } else if (*s) {
            f[0] = s;
            for (i = 1; i < 6; i++) {
                f[i] = strchr(f[i - 1], '\t');
                if (!f[i])
                    return 0;
                *f[i]++ = 0;
            }
            if (!strchr("KAL", f[0][0]) || f[0][1] || !strchr("SW", f[1][0]) || f[1][1] ||
                !add(f[0][0], f[1][0], f[2], f[3], f[4], f[5]))
                return 0;
        }
        if (!eol)
            break;
        s = eol;
    }
    return ended;
}

static int fail(const char *what)
{
    printf("T80SET: %s\n", what);
    return 1;
}

static int restore_whole(void)
{
    int r;
    if (!exists(in("SYSTEM.T80")) || !exists(in("WIN.T80")))
        return fail("no saved SYSTEM.T80/WIN.T80: nothing to restore");
    if (stale())
        return 1;
    if (!copyfile(in("SYSTEM.T80"), in(NEWF[0])) || !samefile(in("SYSTEM.T80"), in(NEWF[0])) ||
        !copyfile(in("WIN.T80"), in(NEWF[1])) || !samefile(in("WIN.T80"), in(NEWF[1]))) {
        remove(in(NEWF[0]));
        remove(in(NEWF[1]));
        return fail("cannot copy SYSTEM.T80/WIN.T80; nothing was changed");
    }
    r = swap2();
    if (r != 1)
        return fail(r == 0 ? "cannot replace SYSTEM.INI/WIN.INI; nothing was changed"
                           : "restore failed part way (see above)");
    remove(in("SYSTEM.T80"));
    remove(in("WIN.T80"));
    remove(in("T80SET.STA"));
    printf("T80SET: SYSTEM.INI and WIN.INI restored whole from SYSTEM.T80 and WIN.T80\n");
    return 0;
}

int main(int argc, char **argv)
{
    static char drv[40], sysset[4][60], helper[40];
    const char *sset[4], *fadd[2], *wset[2];
    int r, kept, compact = 0, nargs = argc;
    if (argc >= 5 && stricmp(argv[argc - 1], "/C") == 0) {
        compact = 1;
        nargs = argc - 1;
    }
    wset[0] = "BorderWidth=7";
    wset[1] = "GridGranularity=1";
    if (argc >= 3)
        dir = argv[2];
    if (argc >= 3 && stricmp(argv[1], "RESTORE") == 0)
        return restore_whole();
    if (argc >= 3 && stricmp(argv[1], "OFF") == 0) {
        if (!exists(in("T80SET.STA"))) {
            if (exists(in("SYSTEM.T80")) || exists(in("WIN.T80")))
                return fail("no T80SET.STA, so no record of what ON changed: nothing was changed.\n"
                            "         T80SET RESTORE puts back SYSTEM.T80 and WIN.T80 whole\n"
                            "         (losing every change made since they were saved)");
            return fail("not set up (no T80SET.STA): nothing to undo");
        }
        if (stale())
            return 1;
        if (!loadstate(in("T80SET.STA")))
            return fail("T80SET.STA is incomplete or damaged: nothing was changed, the copies are kept\n"
                        "         (T80SET RESTORE puts back SYSTEM.T80 and WIN.T80 whole)");
        if (readfile(in("SYSTEM.INI")) < 0)
            return fail("cannot read SYSTEM.INI (or larger than 24000 bytes)");
        kept = undo('S');
        if (kept < 0 || !writenew(in(NEWF[0]), outbuf))
            return fail("cannot write SYSTEM.T8N; nothing was changed");
        if (readfile(in("WIN.INI")) < 0) {
            remove(in(NEWF[0]));
            return fail("cannot read WIN.INI; nothing was changed");
        }
        r = undo('W');
        if (r < 0 || !writenew(in(NEWF[1]), outbuf)) {
            remove(in(NEWF[0]));
            return fail("cannot write WIN.T8N; nothing was changed");
        }
        kept += r;
        r = swap2();
        if (r != 1)
            return fail(r == 0 ? "cannot replace SYSTEM.INI/WIN.INI; nothing was changed"
                               : "undo failed part way (see above)");
        remove(in("T80SET.STA"));
        remove(in("SYSTEM.T80"));
        remove(in("WIN.T80"));
        printf("T80SET: TEXT80's changes to SYSTEM.INI and WIN.INI undone%s\n",
               kept ? " (lines changed since ON left as they are)" : "");
        return 0;
    }
    if (argc >= 4 && stricmp(argv[1], "ON") == 0) {
        strncpy(drv, argv[3], sizeof(drv) - 1);
        drv[sizeof(drv) - 1] = 0;
        strupr(drv);
        helper[0] = 0;
        if (nargs >= 5) {
            strncpy(helper, argv[4], sizeof(helper) - 1);
            helper[sizeof(helper) - 1] = 0;
            strupr(helper);
        }
        if (exists(in("SYSTEM.T80")) || exists(in("WIN.T80")) || exists(in("T80SET.STA")))
            return fail("already set up (SYSTEM.T80/WIN.T80/T80SET.STA exist); run T80SET OFF first");
        if (stale())
            return 1;
        nent = 0;
        if (readfile(in("SYSTEM.INI")) < 0)
            return fail("cannot read SYSTEM.INI (or larger than 24000 bytes)");
        sprintf(sysset[0], "display.drv=%s", drv);
        strcpy(sysset[1], "fonts.fon=XTTSYS.FON");
        strcpy(sysset[2], "fixedfon.fon=XTCFIX.FON");
        strcpy(sysset[3], "oemfonts.fon=XTCOEM.FON");
        sset[0] = sysset[0];
        sset[1] = sysset[1];
        sset[2] = sysset[2];
        sset[3] = sysset[3];
        if (!edit('S', "[boot]", sset, 4, NULL, 0, NULL))
            return fail("SYSTEM.INI has no [boot] section or a line too long; nothing was changed");
        if (!writenew(in(NEWF[0]), outbuf))
            return fail("cannot write SYSTEM.T8N; nothing was changed");
        if (readfile(in("WIN.INI")) < 0) {
            remove(in(NEWF[0]));
            return fail("cannot read WIN.INI; nothing was changed");
        }
        fadd[0] = "Helv 8x8 (TEXT80)=T80HELV.FON";
        fadd[1] = "Courier 8x8 (TEXT80)=T80COUR.FON";
        if (!edit('W', "[windows]", compact ? wset : NULL, compact ? 2 : 0, NULL, 0, helper[0] ? helper : NULL) ||
            !edit('W', "[fonts]", NULL, 0, fadd, 2, NULL) || !writenew(in(NEWF[1]), outbuf)) {
            remove(in(NEWF[0]));
            remove(in(NEWF[1]));
            return fail("WIN.INI has no [windows] or [fonts] section, a line too long, or cannot "
                        "be written; nothing was changed");
        }
        if (!copyfile(in("SYSTEM.INI"), in("SYSTEM.T80")) || !samefile(in("SYSTEM.INI"), in("SYSTEM.T80")) ||
            !copyfile(in("WIN.INI"), in("WIN.T80")) || !samefile(in("WIN.INI"), in("WIN.T80")) ||
            !savestate(in("T80SET.STA"))) {
            remove(in("SYSTEM.T80"));
            remove(in("WIN.T80"));
            remove(in("T80SET.STA"));
            remove(in(NEWF[0]));
            remove(in(NEWF[1]));
            return fail("cannot save SYSTEM.T80/WIN.T80/T80SET.STA; nothing was changed");
        }
        r = swap2();
        if (r == 0) {
            remove(in("SYSTEM.T80"));
            remove(in("WIN.T80"));
            remove(in("T80SET.STA"));
            return fail("cannot replace SYSTEM.INI/WIN.INI; nothing was changed");
        }
        if (r < 0)
            return fail("set-up failed part way (see above)");
        printf("T80SET: display.drv=%s, 8x8 system/fixed/OEM fonts, %s%s; [fonts] +2 lines%s\n", drv,
               helper[0] ? "load= +" : "load= unchanged", helper,
               compact ? "; BorderWidth=7, GridGranularity=1" : "");
        printf("T80SET: undo with T80SET OFF %s\n", dir);
        return 0;
    }
    if (argc >= 3 && stricmp(argv[1], "SHOW") == 0) {
        printf("%s: %s\n", in("SYSTEM.INI"), exists(in("SYSTEM.INI")) ? "present" : "missing");
        if (!exists(in("T80SET.STA")) || !loadstate(in("T80SET.STA"))) {
            printf("T80SET.STA: %s\n", exists(in("T80SET.STA")) ? "damaged" : "none (not set up)");
            return 0;
        }
        for (r = 0; r < nent; r++)
            printf("%s %s: %s %s%s%s\n", ent[r].file == 'S' ? "SYSTEM.INI" : "WIN.INI", ent[r].sec,
                   ent[r].kind == 'K' ? "set" : ent[r].kind == 'A' ? "added" : "load= +",
                   ent[r].kind == 'A' ? ent[r].orig : ent[r].key, ent[r].kind == 'K' ? "=" : "",
                   ent[r].kind == 'K' ? ent[r].val : ent[r].kind == 'L' ? ent[r].val : "");
        return 0;
    }
    printf("usage: T80SET ON <windows dir> <driver.drv> [<helper.exe>] [/C]\n"
           "       T80SET OFF <windows dir>       (undo ON's changes, keep the rest)\n"
           "       T80SET RESTORE <windows dir>   (the saved files back whole)\n"
           "       T80SET SHOW <windows dir>\n");
    return 1;
}
