#include "VFAT.H"
#include <string.h>
#include <limits.h>

#if defined(_MSC_VER) && !defined(_WIN32)
#define VF_MEMSET _fmemset
#define VF_MEMCPY _fmemcpy
#define VF_MEMCMP _fmemcmp
#else
#define VF_MEMSET memset
#define VF_MEMCPY memcpy
#define VF_MEMCMP memcmp
#endif

#if CHAR_BIT != 8 || USHRT_MAX != 65535U || ULONG_MAX < 4294967295UL
#error VFAT requires 8-bit bytes, 16-bit short, and at least 32-bit long
#endif

static VF_WORD word_at(const VF_BYTE VF_FAR *p)
{
    return (VF_WORD)((VF_WORD)p[0] | ((VF_WORD)p[1] << 8));
}

static VF_DWORD dword_at(const VF_BYTE VF_FAR *p)
{
    return (VF_DWORD)p[0] | ((VF_DWORD)p[1] << 8) |
           ((VF_DWORD)p[2] << 16) | ((VF_DWORD)p[3] << 24);
}

int VF_Mount(const VF_BYTE VF_FAR *b, VF_DWORD available, VF_VOLUME VF_FAR *v)
{
    VF_DWORD total, root, data, clusters, bytes;
    VF_WORD reserved, roots, fatsz, small;
    VF_BYTE spc, fats;
    if (v == 0) return VF_BAD_ARG;
    VF_MEMSET(v, 0, sizeof(*v));
    if (b == 0 || available == 0UL) return VF_BAD_ARG;
    reserved = word_at(b + 14);
    roots = word_at(b + 17);
    fatsz = word_at(b + 22);
    small = word_at(b + 19);
    spc = b[13];
    fats = b[16];
    total = small ? (VF_DWORD)small : dword_at(b + 32);
    if (b[510] != 0x55 || b[511] != 0xaa ||
        !((b[0] == 0xeb && b[2] == 0x90) || b[0] == 0xe9) ||
        word_at(b + 11) != VF_SECTOR || spc == 0 || spc > 64 ||
        (spc & (spc - 1)) != 0 || reserved == 0 ||
        (fats != 1 && fats != 2) || roots == 0 || (roots & 15) != 0 ||
        fatsz == 0 || total == 0UL || total > available ||
        (small && dword_at(b + 32) != 0UL) ||
        !(b[21] == 0xf0 || b[21] >= 0xf8)) return VF_BAD_BPB;
    root = (VF_DWORD)reserved + (VF_DWORD)fats * fatsz;
    data = root + (VF_DWORD)roots / 16UL;
    if (data >= total) return VF_BAD_BPB;
    clusters = (total - data) / spc;
    if (clusters == 0UL || clusters >= 65525UL) return VF_BAD_BPB;
    bytes = clusters < 4085UL ? ((clusters + 2UL) * 3UL + 1UL) / 2UL
                               : (clusters + 2UL) * 2UL;
    if (bytes > (VF_DWORD)fatsz * VF_SECTOR) return VF_BAD_BPB;
    v->total_sectors = total;
    v->fat_start = reserved;
    v->root_start = root;
    v->data_start = data;
    v->fat_sectors = fatsz;
    v->root_entries = roots;
    v->root_sectors = (VF_WORD)(roots / 16);
    v->clusters = (VF_WORD)clusters;
    v->sectors_per_cluster = spc;
    v->fats = fats;
    v->fat_bits = (VF_BYTE)(clusters < 4085UL ? 12 : 16);
    v->media = b[21];
    return VF_OK;
}

void VF_Begin(VF_WORK VF_FAR *w)
{
    if (w != 0) VF_MEMSET(w, 0, sizeof(*w));
}

static int short_char(VF_BYTE c)
{
    if (c >= 0x80) return 1;
    if (c < 0x21 || c == 0x7f) return 0;
    return strchr("\"*+,./:;<=>?[\\]|", (int)c) == 0;
}

int VF_Alias(const char VF_FAR *name, VF_BYTE VF_FAR *alias)
{
    VF_WORD i, n, part, position;
    VF_BYTE c;
    if (name == 0 || alias == 0) return VF_BAD_ARG;
    VF_MEMSET(alias, ' ', 11);
    n = 0;
    while (n < 13 && name[n] != 0) ++n;
    if (n == 0 || n > 12) return VF_BAD_ARG;
    part = position = 0;
    for (i = 0; i < n; ++i) {
        c = (VF_BYTE)name[i];
        if (c == '.') {
            if (part || position == 0 || i + 1 == n) return VF_BAD_ARG;
            part = 1;
            position = 8;
        } else {
            if (!short_char(c) || (!part && position >= 8) ||
                position >= 11) return VF_BAD_ARG;
            if (c >= 'a' && c <= 'z') c = (VF_BYTE)(c - 'a' + 'A');
            alias[position++] = c;
        }
    }
    if (alias[0] == 0xe5) alias[0] = 0x05;
    return VF_OK;
}

VF_BYTE VF_Checksum(const VF_BYTE VF_FAR *alias)
{
    VF_WORD i;
    VF_BYTE sum;
    sum = 0;
    for (i = 0; i < 11; ++i)
        sum = (VF_BYTE)(((sum & 1) ? 128 : 0) + (sum >> 1) + alias[i]);
    return sum;
}

static int valid_cluster(const VF_VOLUME VF_FAR *v, VF_WORD c)
{
    return c >= 2 && (VF_DWORD)c <= (VF_DWORD)v->clusters + 1UL &&
           c < (v->fat_bits == 12 ? 0xff0U : 0xfff0U);
}

static void lfn_reset(VF_WORK VF_FAR *w)
{
    w->active = 0;
    w->expected = 0;
    w->unit_count = 0;
}

static void lfn_entry(VF_WORK VF_FAR *w, const VF_BYTE VF_FAR *entry)
{
    static const VF_BYTE offsets[13] = {
        1, 3, 5, 7, 9, 14, 16, 18, 20, 22, 24, 28, 30
    };
    VF_WORD i, base;
    VF_BYTE ordinal;
    ordinal = (VF_BYTE)(entry[0] & 0x1f);
    if ((entry[0] & 0xa0) || ordinal == 0 || ordinal > 20 ||
        entry[11] != 0x0f || entry[12] != 0 || word_at(entry + 26) != 0) {
        lfn_reset(w);
        return;
    }
    if (entry[0] & 0x40) {
        /* A fresh LAST entry starts a new contiguous sequence. */
        w->active = 1;
        w->expected = ordinal;
        w->checksum = entry[13];
        w->unit_count = (VF_WORD)(ordinal * 13U);
    }
    if (!w->active || w->expected != ordinal || w->checksum != entry[13]) {
        lfn_reset(w);
        return;
    }
    base = (VF_WORD)((ordinal - 1U) * 13U);
    for (i = 0; i < 13; ++i) w->units[base + i] = word_at(entry + offsets[i]);
    --w->expected;
}

static int long_char(VF_WORD c)
{
    if (c < 0x20U || c > 0x7eU) return 0;
    return strchr("\"*/:<>?\\|", (int)c) == 0;
}

static void lfn_name(VF_WORK VF_FAR *w, VF_SLOT VF_FAR *slot)
{
    VF_WORD i, length, c, copied;
    int ended;
    if (!w->active || w->expected != 0 ||
        w->checksum != VF_Checksum(slot->alias)) return;
    ended = 0;
    length = 0;
    for (i = 0; i < w->unit_count; ++i) {
        c = w->units[i];
        if (ended) {
            if (c != 0xffffU) return;
        } else if (c == 0) {
            ended = 1;
        } else {
            if (!long_char(c)) return;
            ++length;
        }
    }
    if (length == 0 || length > 255 ||
        (length + 12U) / 13U != w->unit_count / 13U ||
        w->units[0] == ' ' || w->units[length - 1] == ' ' ||
        w->units[length - 1] == '.' ||
        (length == 1 && w->units[0] == '.') ||
        (length == 2 && w->units[0] == '.' && w->units[1] == '.')) return;
    copied = length > VF_NAME_MAX ? VF_NAME_MAX : length;
    for (i = 0; i < copied; ++i) slot->name[i] = (char)w->units[i];
    slot->name[copied] = 0;
    slot->flags |= VF_LONG;
    if (length > VF_NAME_MAX) slot->flags |= VF_TRUNCATED;
}

static int valid_alias(const VF_BYTE VF_FAR *alias)
{
    VF_WORD i;
    int padding;
    if (alias[0] == ' ' || alias[0] == 0 || alias[0] == 0xe5) return 0;
    padding = 0;
    for (i = 0; i < 11; ++i) {
        if (i == 8) padding = 0;
        if (alias[i] == ' ') padding = 1;
        else if (padding ||
                 (!(i == 0 && alias[i] == 0x05) && !short_char(alias[i]))) return 0;
    }
    return 1;
}

static int valid_short(const VF_VOLUME VF_FAR *v, const VF_BYTE VF_FAR *entry)
{
    VF_WORD cluster;
    VF_DWORD size;
    if (!valid_alias(entry) || (entry[11] & 0xc8) || word_at(entry + 20) != 0)
        return 0;
    cluster = word_at(entry + 26);
    size = dword_at(entry + 28);
    if (entry[11] & 0x10) return size == 0UL && valid_cluster(v, cluster);
    return cluster == 0 ? size == 0UL : valid_cluster(v, cluster);
}

static void clear_outputs(VF_SLOT VF_FAR *slots, VF_WORD count)
{
    VF_WORD i;
    for (i = 0; i < count; ++i) {
        slots[i].name[0] = 0;
        slots[i].cluster = 0;
        slots[i].attr = 0;
        slots[i].flags = 0;
    }
}

static int dir_sector(const VF_VOLUME VF_FAR *v, VF_WORK VF_FAR *w,
                      VF_SLOT VF_FAR *slots, VF_WORD count, VF_WORD entries)
{
    const VF_BYTE VF_FAR *entry;
    VF_WORD i, j;
    for (i = 0; i < entries; ++i) {
        if (w->entries >= VF_ENTRY_MAX) return VF_LIMIT;
        ++w->entries;
        entry = w->sector + i * 32U;
        if (entry[0] == 0) {
            lfn_reset(w);
            return -1;
        }
        if (entry[0] == 0xe5) {
            lfn_reset(w);
        } else if (entry[11] == 0x0f) {
            lfn_entry(w, entry);
        } else {
            for (j = 0; j < count; ++j) {
                if (VF_MEMCMP(slots[j].alias, entry, 11) == 0) {
                    if (slots[j].flags & (VF_MATCH | VF_DUPLICATE)) {
                        slots[j].name[0] = 0;
                        slots[j].cluster = 0;
                        slots[j].attr = 0;
                        slots[j].flags = VF_MATCH | VF_DUPLICATE;
                    } else {
                        slots[j].flags |= VF_MATCH;
                        if (!valid_short(v, entry)) slots[j].flags |= VF_INVALID;
                        else if (!(slots[j].flags & VF_INVALID)) {
                            slots[j].cluster = word_at(entry + 26);
                            slots[j].attr = entry[11];
                            lfn_name(w, slots + j);
                        }
                    }
                }
            }
            lfn_reset(w);
        }
    }
    return VF_OK;
}

#define PH_HEADER0 1
#define PH_HEADER1 2
#define PH_DIRECTORY 3
#define PH_VALIDATE 4
#define PH_FINISHED 5

static int finish(VF_WORK VF_FAR *w, int status)
{
    if (status != VF_OK && w->target_slots != 0)
        clear_outputs(w->target_slots, w->target_count);
    w->status = status;
    w->phase = PH_FINISHED;
    lfn_reset(w);
    w->cache_valid = 0;
    return status;
}

static int read_one(VF_WORK VF_FAR *w, VF_DWORD sector,
                    VF_BYTE VF_FAR *buffer)
{
    if (sector >= w->volume.total_sectors) return VF_BAD_FAT;
    if (w->reads >= VF_READ_MAX) return VF_LIMIT;
    ++w->reads;
    if (w->reader(w->context, sector, buffer) != 0) return VF_IO;
    return VF_OK;
}

static void fat_start(VF_WORK VF_FAR *w, VF_WORD cluster)
{
    w->fat_cluster = cluster;
    w->fat_offset = w->volume.fat_bits == 12 ?
        (VF_DWORD)cluster + cluster / 2U : (VF_DWORD)cluster * 2UL;
    w->fat_copy = w->fat_part = 0;
    w->fat_first = 0;
}

/* Save byte/copy progress before requesting a second sector in a later Step. */
static int fat_poll(VF_WORK VF_FAR *w, VF_WORD *value, int *did_read)
{
    VF_DWORD offset, sector;
    VF_WORD current;
    VF_BYTE byte;
    int status;
    while (w->fat_copy < w->volume.fats) {
        offset = w->fat_offset + w->fat_part;
        if (offset >= (VF_DWORD)w->volume.fat_sectors * VF_SECTOR)
            return VF_BAD_FAT;
        sector = w->volume.fat_start +
            (VF_DWORD)w->fat_copy * w->volume.fat_sectors + offset / VF_SECTOR;
        if (!w->cache_valid || w->cached_sector != sector) {
            if (*did_read) return VF_PENDING;
            w->cache_valid = 0;
            status = read_one(w, sector, w->fat);
            *did_read = 1;
            if (status != VF_OK) return status;
            w->cached_sector = sector;
            w->cache_valid = 1;
        }
        byte = w->fat[(VF_WORD)(offset % VF_SECTOR)];
        if (w->fat_part == 0) {
            w->fat_low = byte;
            w->fat_part = 1;
        } else {
            current = (VF_WORD)((VF_WORD)w->fat_low | ((VF_WORD)byte << 8));
            if (w->volume.fat_bits == 12)
                current = (VF_WORD)((w->fat_cluster & 1) ?
                    current >> 4 : current & 0xfffU);
            if (w->fat_copy == 0) w->fat_first = current;
            else if (current != w->fat_first) return VF_BAD_FAT;
            ++w->fat_copy;
            w->fat_part = 0;
        }
    }
    *value = w->fat_first;
    return VF_OK;
}

static int enter_cluster(VF_WORK VF_FAR *w, VF_WORD cluster)
{
    VF_WORD i;
    if (!valid_cluster(&w->volume, cluster)) return VF_BAD_FAT;
    for (i = 0; i < w->seen_count; ++i)
        if (w->seen[i] == cluster) return VF_CYCLE;
    if (w->seen_count >= VF_CHAIN_MAX || w->clusters >= VF_CHAIN_MAX)
        return VF_LIMIT;
    w->seen[w->seen_count++] = cluster;
    ++w->clusters;
    w->cluster = cluster;
    w->first_sector = w->volume.data_start +
        (VF_DWORD)(cluster - 2U) * w->volume.sectors_per_cluster;
    w->sector_index = 0;
    w->sector_count = w->volume.sectors_per_cluster;
    return VF_OK;
}

static int begin_scan(VF_WORK VF_FAR *w, VF_WORD directory,
                      VF_SLOT VF_FAR *slots, VF_WORD count)
{
    VF_WORD i, j;
    if (directory != 0 && !valid_cluster(&w->volume, directory)) return VF_BAD_ARG;
    w->directory = directory;
    w->scan_slots = slots;
    w->scan_count = count;
    w->seen_count = 0;
    w->cache_valid = 0;
    lfn_reset(w);
    clear_outputs(slots, count);
    for (i = 0; i < count; ++i) {
        if (!valid_alias(slots[i].alias)) slots[i].flags = VF_INVALID;
        for (j = 0; j < i; ++j)
            if (VF_MEMCMP(slots[i].alias, slots[j].alias, 11) == 0) {
                slots[i].flags |= VF_DUPLICATE;
                slots[j].flags |= VF_DUPLICATE;
            }
    }
    w->phase = PH_HEADER0;
    fat_start(w, 0);
    return VF_PENDING;
}

static int next_job(VF_WORK VF_FAR *w)
{
    char component[13];
    VF_WORD n;
    int status;
    if (w->path[w->path_position] == 0) {
        w->resolving = 0;
        if (w->resolve_only) return finish(w, VF_OK);
        return begin_scan(w, w->resolved, w->target_slots, w->target_count);
    }
    if (w->depth >= VF_DEPTH_MAX) return VF_LIMIT;
    ++w->depth;
    n = 0;
    while (w->path[w->path_position] != 0 && w->path[w->path_position] != '\\') {
        if (n >= 12) return VF_BAD_ARG;
        component[n++] = w->path[w->path_position++];
    }
    if (n == 0) return VF_BAD_ARG;
    component[n] = 0;
    if (w->path[w->path_position] == '\\') ++w->path_position;
    status = VF_Alias(component, w->dir_slot.alias);
    if (status != VF_OK) return status;
    w->resolving = 1;
    return begin_scan(w, w->resolved, &w->dir_slot, 1);
}

static int scan_finished(VF_WORK VF_FAR *w)
{
    if (!w->resolving) return finish(w, VF_OK);
    if (w->dir_slot.flags & VF_DUPLICATE) return VF_AMBIGUOUS;
    if (!(w->dir_slot.flags & VF_MATCH)) return VF_NOT_FOUND;
    if ((w->dir_slot.flags & VF_INVALID) || !(w->dir_slot.attr & 0x10) ||
        !valid_cluster(&w->volume, w->dir_slot.cluster)) return VF_BAD_FAT;
    w->resolved = w->dir_slot.cluster;
    return next_job(w);
}

static int setup(const VF_VOLUME VF_FAR *v, VF_READ reader, void *ctx,
                 VF_WORK VF_FAR *w, VF_SLOT VF_FAR *slots, VF_WORD count)
{
    if (slots != 0 && count <= VF_SLOTS_MAX) clear_outputs(slots, count);
    if (v == 0 || reader == 0 || w == 0 || count > VF_SLOTS_MAX ||
        (count != 0 && slots == 0) || (v->fat_bits != 12 && v->fat_bits != 16))
        return VF_BAD_ARG;
    VF_MEMCPY(&w->volume, v, sizeof(*v));
    w->reader = reader;
    w->context = ctx;
    w->target_slots = slots;
    w->target_count = count;
    w->scan_slots = 0;
    w->scan_count = 0;
    w->resolved = 0;
    w->depth = w->resolving = w->resolve_only = 0;
    w->phase = PH_FINISHED;
    w->status = VF_PENDING;
    return VF_OK;
}

static int start_path(VF_WORK VF_FAR *w, const char VF_FAR *path)
{
    VF_WORD length, position;
    if (path == 0) return VF_BAD_ARG;
    length = 0;
    while (length < VF_PATH_MAX && path[length] != 0) ++length;
    if (length == 0 || length >= VF_PATH_MAX) return VF_BAD_ARG;
    position = 0;
    if (length >= 3 && path[1] == ':') {
        if (!((path[0] >= 'A' && path[0] <= 'Z') ||
              (path[0] >= 'a' && path[0] <= 'z'))) return VF_BAD_ARG;
        position = 2;
    }
    if (path[position] != '\\') return VF_BAD_ARG;
    VF_MEMCPY(w->path, path, length + 1U);
    w->path_position = (VF_WORD)(position + 1U);
    return next_job(w);
}

int VF_Start(const VF_VOLUME VF_FAR *v, VF_READ reader, void *ctx,
              VF_WORK VF_FAR *w, const char VF_FAR *path,
              VF_SLOT VF_FAR *slots, VF_WORD count)
{
    int status;
    if (count == 0) return VF_BAD_ARG;
    status = setup(v, reader, ctx, w, slots, count);
    if (status != VF_OK) return status;
    status = start_path(w, path);
    return status > VF_OK ? finish(w, status) : status;
}

int VF_Step(VF_WORK VF_FAR *w)
{
    VF_WORD value, i;
    int status, did_read;
    if (w == 0 || w->reader == 0) return VF_BAD_ARG;
    if (w->phase == PH_FINISHED) return w->status;
    did_read = 0;
    for (;;) {
        if (w->phase == PH_HEADER0 || w->phase == PH_HEADER1 || w->phase == PH_VALIDATE) {
            status = fat_poll(w, &value, &did_read);
            if (status == VF_PENDING) return status;
            if (status != VF_OK) return finish(w, status);
            if (w->phase == PH_HEADER0) {
                if (value != (VF_WORD)((w->volume.fat_bits == 12 ? 0xf00U : 0xff00U)
                                      | w->volume.media)) return finish(w, VF_BAD_FAT);
                w->phase = PH_HEADER1;
                fat_start(w, 1);
            } else if (w->phase == PH_HEADER1) {
                if ((w->volume.fat_bits == 12 && value != 0xfffU) ||
                    (w->volume.fat_bits == 16 && (value & 0x3fffU) != 0x3fffU))
                    return finish(w, VF_BAD_FAT);
                if (w->directory == 0) {
                    w->first_sector = w->volume.root_start;
                    w->sector_count = w->volume.root_sectors;
                    w->sector_index = 0;
                    w->phase = PH_DIRECTORY;
                } else {
                    status = enter_cluster(w, w->directory);
                    if (status != VF_OK) return finish(w, status);
                    fat_start(w, w->cluster);
                    w->phase = PH_VALIDATE;
                }
            } else {
                if (value < (w->volume.fat_bits == 12 ? 0xff8U : 0xfff8U)) {
                    if (!valid_cluster(&w->volume, value)) return finish(w, VF_BAD_FAT);
                    for (i = 0; i < w->seen_count; ++i)
                        if (w->seen[i] == value) return finish(w, VF_CYCLE);
                }
                w->next_cluster = value;
                w->phase = PH_DIRECTORY;
            }
        } else if (w->phase == PH_DIRECTORY) {
            if (did_read) return VF_PENDING;
            status = read_one(w, w->first_sector + w->sector_index, w->sector);
            did_read = 1;
            if (status != VF_OK) return finish(w, status);
            status = dir_sector(&w->volume, w, w->scan_slots, w->scan_count, 16);
            if (status == -1) {
                status = scan_finished(w);
                if (status != VF_PENDING) return finish(w, status);
            } else {
                if (status != VF_OK) return finish(w, status);
                ++w->sector_index;
                if (w->sector_index >= w->sector_count) {
                    if (w->directory == 0) {
                        status = scan_finished(w);
                        if (status != VF_PENDING) return finish(w, status);
                    } else {
                        if (w->next_cluster >=
                            (w->volume.fat_bits == 12 ? 0xff8U : 0xfff8U)) {
                            status = scan_finished(w);
                            if (status != VF_PENDING) return finish(w, status);
                        } else {
                            status = enter_cluster(w, w->next_cluster);
                            if (status != VF_OK) return finish(w, status);
                            fat_start(w, w->cluster);
                            w->phase = PH_VALIDATE;
                        }
                    }
                }
            }
            /* Bound both I/O and CPU work per timer call to one sector. */
            return VF_PENDING;
        } else return finish(w, VF_BAD_ARG);
    }
}

void VF_Cancel(VF_WORK VF_FAR *w)
{
    if (w != 0) finish(w, VF_IO);
}

int VF_IndexDir(const VF_VOLUME VF_FAR *v, VF_READ reader, void *ctx,
                VF_WORK VF_FAR *w, VF_WORD directory,
                VF_SLOT VF_FAR *slots, VF_WORD count)
{
    int status;
    if (count == 0) return VF_BAD_ARG;
    status = setup(v, reader, ctx, w, slots, count);
    if (status != VF_OK) return status;
    status = begin_scan(w, directory, slots, count);
    while (status == VF_PENDING) status = VF_Step(w);
    return status > VF_OK ? finish(w, status) : status;
}

int VF_Resolve(const VF_VOLUME VF_FAR *v, VF_READ reader, void *ctx,
               VF_WORK VF_FAR *w, const char VF_FAR *path, VF_WORD *directory)
{
    int status;
    if (directory == 0) return VF_BAD_ARG;
    *directory = 0;
    status = setup(v, reader, ctx, w, 0, 0);
    if (status != VF_OK) return status;
    w->resolve_only = 1;
    status = start_path(w, path);
    while (status == VF_PENDING) status = VF_Step(w);
    if (status != VF_OK) return finish(w, status);
    *directory = w->resolved;
    return VF_OK;
}
