/* T80SET.C - reversible TEXT80 setup for Windows 3.0 (DOS program; C89,
 * Microsoft C small model). Run at the DOS prompt, never inside Windows.
 *
 *   T80SET ON  <windows dir> <driver.drv> [<helper.exe>]
 *   T80SET OFF <windows dir>
 *   T80SET SHOW <windows dir>
 *
 * ON refuses if <dir>\SYSTEM.T80 or WIN.T80 exists (already set up). It
 * copies SYSTEM.INI to SYSTEM.T80 and WIN.INI to WIN.T80 byte for byte, then
 * edits the live files (each written to a .$$$ file first, then renamed):
 *   SYSTEM.INI [boot]: display.drv=<driver>, fonts.fon=XTTSYS.FON,
 *     fixedfon.fon=XTCFIX.FON, oemfonts.fon=XTCOEM.FON (the 8x8 fonts);
 *   WIN.INI [windows]: load= gains <helper> at its end (existing entries
 *     kept; nothing if already listed or no helper given);
 *   WIN.INI [fonts]: two lines ADDED, none removed:
 *     Helv 8x8 (TEXT80)=T80HELV.FON and Courier 8x8 (TEXT80)=T80COUR.FON.
 * OFF copies SYSTEM.T80 and WIN.T80 back over the live files and deletes
 * them: Windows starts exactly as before ON. SHOW prints the lines ON sets.
 * Exit code 0 on success, 1 on any error (files then left unchanged).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <io.h>

#ifndef SEP
#define SEP "\\"                /* the host test (T80SETT.PY) builds with "/" */
#endif
#define MAXF 32000
static char inbuf[MAXF + 1];
static char outbuf[MAXF + 600];
static char path[160], path2[160], tmp[160];

static int copyfile(const char *from, const char *to)
{
    FILE *a, *b;
    int c;
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
            fclose(a);
            fclose(b);
            return 0;
        }
    fclose(a);
    return fclose(b) == 0;
}

static int exists(const char *p)
{
    return access(p, 0) == 0;
}

static void join(char *out, const char *dir, const char *name)
{
    strcpy(out, dir);
    if (out[0] && out[strlen(out) - 1] != SEP[0] && out[strlen(out) - 1] != ':')
        strcat(out, SEP);
    strcat(out, name);
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
    return n;
}

static int writefile(const char *p, const char *data)
{
    FILE *f;
    char t[160];
    strcpy(t, p);
    strcpy(strrchr(t, '.'), ".$$$");
    f = fopen(t, "wb");
    if (!f)
        return 0;
    if (fwrite(data, 1, strlen(data), f) != strlen(data)) {
        fclose(f);
        remove(t);
        return 0;
    }
    if (fclose(f) != 0) {
        remove(t);
        return 0;
    }
    if (remove(p) != 0 || rename(t, p) != 0)
        return 0;
    return 1;
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

/* Edit one section: set[i] = "key=value" lines to set (replace or insert at
 * the section's top); add[i] = lines to add if not present (exact,
 * case-insensitive); loadhelper: append to load=. */
static int edit(const char *section, const char **set, int nset, const char **add, int nadd,
                const char *helper)
{
    char *p = inbuf, *o = outbuf, *eol;
    char line[300], upper[300];
    int insec = 0, found = 0, i, seen[8], have[8], loaddone = 0;
    for (i = 0; i < 8; i++)
        seen[i] = have[i] = 0;
    for (;;) {
        int len;
        if (!*p)
            break;
        eol = strchr(p, '\n');
        len = eol ? (int)(eol - p + 1) : (int)strlen(p);
        if (len >= (int)sizeof(line) - 2)
            return 0;
        memcpy(line, p, len);
        line[len] = 0;
        p += len;
        if (line[0] == '[') {
            if (insec) {                 /* leaving the section: insert what is missing */
                for (i = 0; i < nset; i++)
                    if (!seen[i])
                        o += sprintf(o, "%s\r\n", set[i]);
                for (i = 0; i < nadd; i++)
                    if (!have[i])
                        o += sprintf(o, "%s\r\n", add[i]);
                if (helper && !loaddone)
                    o += sprintf(o, "load=%s\r\n", helper);
                insec = 0;
            }
            if (strnicmp(line, section, strlen(section)) == 0) {
                insec = found = 1;
                strcpy(o, line);
                o += len;
                if (o[-1] != '\n')
                    o += sprintf(o, "\r\n");
                continue;
            }
        } else if (insec) {
            for (i = 0; i < nset; i++) {
                char key[40];
                strncpy(key, set[i], sizeof(key) - 1);
                key[sizeof(key) - 1] = 0;
                *strchr(key, '=') = 0;
                if (keyis(line, key)) {
                    o += sprintf(o, "%s\r\n", set[i]);
                    seen[i] = 1;
                    goto next;
                }
            }
            for (i = 0; i < nadd; i++)
                if (strnicmp(line, add[i], strlen(add[i])) == 0)
                    have[i] = 1;
            if (helper && keyis(line, "load")) {
                char *e = line + strlen(line);
                while (e > line && (e[-1] == '\n' || e[-1] == '\r'))
                    *--e = 0;
                if (!strstr(strupr(strcpy(upper, line)), helper))
                    o += sprintf(o, "%s%s%s\r\n", line,
                                 line[strlen(line) - 1] == '=' ? "" : " ", helper);
                else
                    o += sprintf(o, "%s\r\n", line);
                loaddone = 1;
                goto next;
            }
        }
        strcpy(o, line);
        o += len;
    next:
        if (o - outbuf > MAXF + 300)
            return 0;
    }
    if (insec) {
        if (o > outbuf && o[-1] != '\n')
            o += sprintf(o, "\r\n");
        for (i = 0; i < nset; i++)
            if (!seen[i])
                o += sprintf(o, "%s\r\n", set[i]);
        for (i = 0; i < nadd; i++)
            if (!have[i])
                o += sprintf(o, "%s\r\n", add[i]);
        if (helper && !loaddone)
            o += sprintf(o, "load=%s\r\n", helper);
    }
    *o = 0;
    if (!found)
        return 0;
    strcpy(inbuf, outbuf);
    return 1;
}

static int fail(const char *what)
{
    printf("T80SET: %s\n", what);
    return 1;
}

int main(int argc, char **argv)
{
    char drv[40], sysset[4][60], helper[40];
    const char *sset[4], *fadd[2];
    if (argc >= 3 && stricmp(argv[1], "OFF") == 0) {
        join(path, argv[2], "SYSTEM.T80");
        join(path2, argv[2], "WIN.T80");
        if (!exists(path) || !exists(path2))
            return fail("no saved SYSTEM.T80/WIN.T80: nothing to undo");
        join(tmp, argv[2], "SYSTEM.INI");
        if (!copyfile(path, tmp))
            return fail("cannot restore SYSTEM.INI");
        join(tmp, argv[2], "WIN.INI");
        if (!copyfile(path2, tmp))
            return fail("cannot restore WIN.INI (SYSTEM.INI already restored)");
        remove(path);
        remove(path2);
        printf("T80SET: SYSTEM.INI and WIN.INI restored from SYSTEM.T80 and WIN.T80\n");
        return 0;
    }
    if (argc >= 4 && stricmp(argv[1], "ON") == 0) {
        strncpy(drv, argv[3], sizeof(drv) - 1);
        drv[sizeof(drv) - 1] = 0;
        strupr(drv);
        helper[0] = 0;
        if (argc >= 5) {
            strncpy(helper, argv[4], sizeof(helper) - 1);
            helper[sizeof(helper) - 1] = 0;
            strupr(helper);
        }
        join(path, argv[2], "SYSTEM.T80");
        join(path2, argv[2], "WIN.T80");
        if (exists(path) || exists(path2))
            return fail("already set up (SYSTEM.T80/WIN.T80 exist); run T80SET OFF first");
        join(tmp, argv[2], "SYSTEM.INI");
        if (readfile(tmp) < 0)
            return fail("cannot read SYSTEM.INI (or larger than 32000 bytes)");
        sprintf(sysset[0], "display.drv=%s", drv);
        strcpy(sysset[1], "fonts.fon=XTTSYS.FON");
        strcpy(sysset[2], "fixedfon.fon=XTCFIX.FON");
        strcpy(sysset[3], "oemfonts.fon=XTCOEM.FON");
        sset[0] = sysset[0];
        sset[1] = sysset[1];
        sset[2] = sysset[2];
        sset[3] = sysset[3];
        if (!edit("[boot]", sset, 4, NULL, 0, NULL))
            return fail("SYSTEM.INI has no [boot] section or a line too long");
        if (!copyfile(tmp, path))
            return fail("cannot save SYSTEM.T80");
        if (!writefile(tmp, inbuf)) {
            remove(path);
            return fail("cannot write SYSTEM.INI");
        }
        join(tmp, argv[2], "WIN.INI");
        if (readfile(tmp) < 0) {
            join(tmp, argv[2], "SYSTEM.INI");
            copyfile(path, tmp);
            remove(path);
            return fail("cannot read WIN.INI; SYSTEM.INI restored");
        }
        fadd[0] = "Helv 8x8 (TEXT80)=T80HELV.FON";
        fadd[1] = "Courier 8x8 (TEXT80)=T80COUR.FON";
        if (!edit("[windows]", NULL, 0, NULL, 0, helper[0] ? helper : NULL) ||
            !edit("[fonts]", NULL, 0, fadd, 2, NULL) || !copyfile(tmp, path2) ||
            !writefile(tmp, inbuf)) {
            join(tmp, argv[2], "SYSTEM.INI");
            copyfile(path, tmp);
            remove(path);
            remove(path2);
            return fail("cannot update WIN.INI; SYSTEM.INI restored");
        }
        printf("T80SET: display.drv=%s, 8x8 system/fixed/OEM fonts, %s%s; [fonts] +2 lines\n", drv,
               helper[0] ? "load= +" : "load= unchanged", helper);
        printf("T80SET: undo with T80SET OFF %s (restores SYSTEM.T80, WIN.T80)\n", argv[2]);
        return 0;
    }
    if (argc >= 3 && stricmp(argv[1], "SHOW") == 0) {
        join(tmp, argv[2], "SYSTEM.INI");
        printf("%s: %s\n", tmp, exists(tmp) ? "present" : "missing");
        join(path, argv[2], "SYSTEM.T80");
        printf("saved originals: %s\n", exists(path) ? "yes (T80SET ON is active)" : "no");
        return 0;
    }
    printf("usage: T80SET ON <windows dir> <driver.drv> [<helper.exe>]\n"
           "       T80SET OFF <windows dir>\n       T80SET SHOW <windows dir>\n");
    return 1;
}
