#ifndef VFAT_H
#define VFAT_H

/* Pure C89, 8088/small-model friendly. See README.TXT for the contract. */
#define VF_SECTOR       512
#define VF_NAME_MAX      63
#define VF_SLOTS_MAX    128
#define VF_CHAIN_MAX    128
#define VF_READ_MAX    1024
#define VF_ENTRY_MAX   4096
#define VF_PATH_MAX      80
#define VF_DEPTH_MAX      8

#define VF_PENDING       -1
#define VF_OK             0
#define VF_BAD_BPB        1
#define VF_BAD_ARG        2
#define VF_IO            3
#define VF_LIMIT          4
#define VF_BAD_FAT        5
#define VF_CYCLE          6
#define VF_NOT_FOUND      7
#define VF_AMBIGUOUS      8

#define VF_MATCH          1
#define VF_LONG           2
#define VF_DUPLICATE      4
#define VF_INVALID        8
#define VF_TRUNCATED     16

#if defined(_MSC_VER) && !defined(_WIN32)
#define VF_FAR _far
#else
#define VF_FAR
#endif

typedef unsigned char VF_BYTE;
typedef unsigned short VF_WORD;
typedef unsigned long VF_DWORD;

typedef struct VF_VOLUME {
    VF_DWORD total_sectors;
    VF_DWORD fat_start;
    VF_DWORD root_start;
    VF_DWORD data_start;
    VF_WORD fat_sectors;
    VF_WORD root_entries;
    VF_WORD root_sectors;
    VF_WORD clusters;
    VF_BYTE sectors_per_cluster;
    VF_BYTE fats;
    VF_BYTE fat_bits;
    VF_BYTE media;
} VF_VOLUME;

typedef struct VF_SLOT {
    VF_BYTE alias[11];             /* INPUT: exact padded on-disk alias */
    char name[VF_NAME_MAX + 1];    /* OUTPUT: display only, never a path */
    VF_WORD cluster;
    VF_BYTE attr;
    VF_BYTE flags;
} VF_SLOT;

/* Zero means success; nonzero means failure or cancellation. */
typedef int (*VF_READ)(void *context, VF_DWORD sector,
                       VF_BYTE VF_FAR *buffer);

typedef struct VF_WORK {
    VF_BYTE sector[VF_SECTOR];
    VF_BYTE fat[VF_SECTOR];
    VF_WORD units[260];
    VF_WORD seen[VF_CHAIN_MAX];
    VF_DWORD cached_sector;
    VF_WORD reads;
    VF_WORD entries;
    VF_WORD clusters;
    VF_WORD seen_count;
    VF_WORD unit_count;
    VF_BYTE expected;
    VF_BYTE checksum;
    VF_BYTE active;
    VF_BYTE cache_valid;
    VF_VOLUME volume;
    VF_SLOT dir_slot;
    VF_SLOT VF_FAR *target_slots;
    VF_SLOT VF_FAR *scan_slots;
    VF_READ reader;
    void *context;
    char path[VF_PATH_MAX];
    VF_DWORD first_sector;
    VF_DWORD fat_offset;
    VF_WORD target_count;
    VF_WORD scan_count;
    VF_WORD directory;
    VF_WORD cluster;
    VF_WORD next_cluster;
    VF_WORD sector_index;
    VF_WORD sector_count;
    VF_WORD path_position;
    VF_WORD fat_cluster;
    VF_WORD fat_first;
    VF_WORD resolved;
    int status;
    VF_BYTE phase;
    VF_BYTE fat_copy;
    VF_BYTE fat_part;
    VF_BYTE fat_low;
    VF_BYTE resolving;
    VF_BYTE resolve_only;
    VF_BYTE depth;
} VF_WORK;

/* Callback is read-only, volume-relative and synchronous. It may check
 * cancellation before a read. No yielding or reentry into the core.
 * VF_Begin resets cumulative budgets. Do not call it between resolver and
 * index operations that belong to one refresh. VF_Start does not reset them.
 * Keep volume, callback context, work, and slots valid through completion.
 * VF_Step makes at most ONE callback and returns VF_PENDING until complete.
 * Publish output names only after VF_OK. Any error/cancel clears all outputs.
 */
int VF_Mount(const VF_BYTE VF_FAR *boot, VF_DWORD available,
             VF_VOLUME VF_FAR *volume);
void VF_Begin(VF_WORK VF_FAR *work);
int VF_Alias(const char VF_FAR *dos_name, VF_BYTE VF_FAR *alias);
VF_BYTE VF_Checksum(const VF_BYTE VF_FAR *alias);
int VF_Start(const VF_VOLUME VF_FAR *volume, VF_READ read_sector,
              void *context, VF_WORK VF_FAR *work,
              const char VF_FAR *absolute_path,
              VF_SLOT VF_FAR *slots, VF_WORD count);
int VF_Step(VF_WORK VF_FAR *work);
void VF_Cancel(VF_WORK VF_FAR *work);
/* Synchronous conveniences: same engine, same shared cumulative budgets. */
int VF_IndexDir(const VF_VOLUME VF_FAR *volume, VF_READ read_sector,
                void *context, VF_WORK VF_FAR *work, VF_WORD directory,
                VF_SLOT VF_FAR *slots, VF_WORD count);
int VF_Resolve(const VF_VOLUME VF_FAR *volume, VF_READ read_sector,
               void *context, VF_WORK VF_FAR *work,
               const char VF_FAR *absolute_path, VF_WORD *directory);

#endif
