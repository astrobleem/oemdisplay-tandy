#include "GRPREAD.H"

static unsigned pmword(const unsigned char *p)
{
    return (unsigned)p[0] | ((unsigned)p[1] << 8);
}

static int pmspan(const PmGroup *g, unsigned p, unsigned n)
{
    return p >= g->dataStart && p < g->size &&
           (unsigned long)p + n <= (unsigned long)g->size;
}

/* Validate the complete string even when only a short display is requested. */
static int pmstring(PmReadFn rd, void *ctx, const PmGroup *g, unsigned pos,
                    char *out, unsigned cap, unsigned *length)
{
    unsigned char b[64];
    unsigned n, i, count;
    unsigned long p;
    if (!pmspan(g, pos, 1)) return PM_STRING;
    count = 0;
    p = pos;
    while (p < g->size) {
        n = (unsigned)((unsigned long)g->size - p);
        if (n > sizeof(b)) n = sizeof(b);
        if (!rd(ctx, p, b, n)) return PM_IO;
        for (i = 0; i < n; ++i) {
            if (!b[i]) {
                if (length) *length = count;
                if (out && cap) {
                    if (count < cap) out[count] = 0;
                    else {
                        out[cap - 1] = 0;
                        if (cap >= 4) {
                            out[cap - 4] = '.';
                            out[cap - 3] = '.';
                            out[cap - 2] = '.';
                        }
                    }
                }
                return PM_OK;
            }
            if (out && cap && count < cap - 1) out[count] = (char)b[i];
            ++count;
        }
        p += n;
    }
    if (out && cap) out[0] = 0;
    return PM_STRING;
}

int PmReadGroup(PmReadFn rd, void *ctx, unsigned long length, PmGroup *g)
{
    unsigned char b[256], head[34], record[24], icon[12];
    unsigned i, n, sum, p, status, namelen, cmdlen, w, h, stride;
    unsigned andSize, xorSize, planes, bits;
    unsigned long offset;
    g->count = 0;
    g->title[0] = 0;
    if (length < 34UL || length > 65535UL) return PM_FORMAT;
    if (!rd(ctx, 0UL, head, sizeof(head))) return PM_IO;
    if (head[0] != 'P' || head[1] != 'M' ||
        head[2] != 'C' || head[3] != 'C') return PM_FORMAT;
    if ((unsigned long)pmword(head + 6) != length) return PM_VERSION;
    g->size = (unsigned)length;
    g->slots = pmword(head + 32);
    if (g->slots > PM_MAX_SLOTS) return PM_LIMIT;
    g->dataStart = 34 + 2 * g->slots;
    if (g->dataStart >= g->size) return PM_FORMAT;
    /* Match original Windows 3.0: ignore an unmatched odd trailing byte. */
    sum = 0;
    offset = 0;
    while (offset + 1 < length) {
        n = (unsigned)(length - offset);
        if (n > sizeof(b)) n = sizeof(b);
        n &= ~1U;
        if (!rd(ctx, offset, b, n)) return PM_IO;
        for (i = 0; i < n; i += 2) sum = (sum + pmword(b + i)) & 65535U;
        offset += n;
    }
    if (sum) return PM_CHECKSUM;
    status = pmstring(rd, ctx, g, pmword(head + 22), g->title,
                      sizeof(g->title), &namelen);
    if (status) return status;
    if (!namelen) return PM_STRING;
    for (i = 0; i < g->slots; ++i) {
        if (!rd(ctx, 34UL + 2UL * i, b, 2)) return PM_IO;
        p = pmword(b);
        if (!p) continue;
        if (g->count == PM_MAX_ITEMS) return PM_LIMIT;
        if (!pmspan(g, p, sizeof(record))) return PM_FORMAT;
        if (!rd(ctx, (unsigned long)p, record, sizeof(record))) return PM_IO;
        /* No Windows 3.1 icon header or extension tags are interpreted. */
        if (pmword(record + 6) != 12) return PM_VERSION;
        if (!pmspan(g, pmword(record + 12), 12) ||
            !pmspan(g, pmword(record + 14), pmword(record + 8)) ||
            !pmspan(g, pmword(record + 16), pmword(record + 10)))
            return PM_FORMAT;
        if (!rd(ctx, (unsigned long)pmword(record + 12), icon, 12))
            return PM_IO;
        w = pmword(icon + 4); h = pmword(icon + 6);
        stride = pmword(icon + 8); planes = icon[10]; bits = icon[11];
        andSize = pmword(record + 8); xorSize = pmword(record + 10);
        if (!w || !h || !stride || !planes || !bits ||
            (unsigned long)h * (((unsigned long)w + 15UL) / 16UL * 2UL)
                != (unsigned long)andSize ||
            (unsigned long)h * stride > 65535UL ||
            (unsigned long)h * stride * planes != (unsigned long)xorSize)
            return PM_FORMAT;
        /* Read only 12 bytes of icon metadata, never bitmap payloads. */
        g->item[g->count].name = pmword(record + 18);
        g->item[g->count].command = pmword(record + 20);
        status = pmstring(rd, ctx, g, pmword(record + 18),
                          (char *)0, 0, &namelen);
        if (status) return status;
        if (!namelen) return PM_STRING;
        status = pmstring(rd, ctx, g, pmword(record + 20),
                          (char *)0, 0, &cmdlen);
        if (status) return status;
        if (!cmdlen) return PM_STRING;
        g->item[g->count].commandLength = cmdlen;
        status = pmstring(rd, ctx, g, pmword(record + 22),
                          (char *)0, 0, (unsigned *)0);
        if (status) return status;
        ++g->count;
    }
    return PM_OK;
}

int PmReadName(PmReadFn rd, void *ctx, const PmGroup *g,
               unsigned index, char *name, unsigned capacity)
{
    if (index >= g->count || !capacity) return PM_FORMAT;
    return pmstring(rd, ctx, g, g->item[index].name, name, capacity,
                    (unsigned *)0);
}

int PmReadCommand(PmReadFn rd, void *ctx, const PmGroup *g,
                  unsigned index, char *command, unsigned capacity)
{
    unsigned status, length;
    if (capacity) command[0] = 0;
    if (index >= g->count || !capacity) return PM_FORMAT;
    if (g->item[index].commandLength > PM_CMD_MAX ||
        g->item[index].commandLength >= capacity) return PM_LONG;
    status = pmstring(rd, ctx, g, g->item[index].command,
                      command, capacity, &length);
    if (status || length != g->item[index].commandLength ||
        length > PM_CMD_MAX || length >= capacity) {
        command[0] = 0;
        return status ? status : PM_LONG;
    }
    return PM_OK;
}

int PmCommandToken(const char *command, char *token, unsigned capacity)
{
    unsigned i, n;
    int quoted;
    i = 0; n = 0; quoted = 0;
    if (!capacity) return 0;
    token[0] = 0;
    while (command[i] == ' ' || command[i] == '\t') ++i;
    if (command[i] == '"') { quoted = 1; ++i; }
    while (command[i] && (quoted ? command[i] != '"' :
           (command[i] != ' ' && command[i] != '\t'))) {
        if (n + 1 >= capacity || (unsigned char)command[i] < 32 ||
            command[i] == '"') return 0;
        token[n++] = command[i++];
    }
    if (quoted && command[i] != '"') return 0;
    if (quoted && command[i + 1] && command[i + 1] != ' ' &&
        command[i + 1] != '\t') return 0;
    token[n] = 0;
    return n != 0;
}

int PmTokenKind(const char *token)
{
    unsigned i;
    int kind;
    if (!token[0]) return 0;
    kind = 1;
    if (((token[0] >= 'A' && token[0] <= 'Z') ||
         (token[0] >= 'a' && token[0] <= 'z')) &&
        token[1] == ':' && token[2] == '\\') kind = 2;
    for (i = 0; token[i]; ++i) {
        if (token[i] == '/' || token[i] == '*' || token[i] == '?' ||
            token[i] == '"' || token[i] == ' ' || token[i] == '\t') return 0;
        if ((token[i] == ':' && !(kind == 2 && i == 1)) ||
            (token[i] == '\\' && kind != 2)) return 0;
    }
    return kind;
}
