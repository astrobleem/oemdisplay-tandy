#ifndef GRPREAD_H
#define GRPREAD_H

/* Portable C89, bounded read-only Windows 3.0 PMCC reader. */
#define PM_MAX_ITEMS 50
#define PM_MAX_SLOTS 64
#define PM_CMD_MAX 126
#define PM_NAME_MAX 63
#define PM_OK 0
#define PM_IO 1
#define PM_FORMAT 2
#define PM_CHECKSUM 3
#define PM_VERSION 4
#define PM_LIMIT 5
#define PM_STRING 6
#define PM_LONG 7

typedef int (*PmReadFn)(void *, unsigned long, unsigned char *, unsigned);
typedef struct {
    unsigned name, command, commandLength;
} PmItem;
typedef struct {
    unsigned size, dataStart, count, slots;
    char title[PM_NAME_MAX + 1];
    PmItem item[PM_MAX_ITEMS];
} PmGroup;

/* ReadFn must return nonzero only after reading exactly n requested bytes. */
int PmReadGroup(PmReadFn readfn, void *context, unsigned long length,
                PmGroup *group);
/* Display names may be ellipsized; commands are NEVER silently truncated. */
int PmReadName(PmReadFn readfn, void *context, const PmGroup *group,
               unsigned index, char *name, unsigned capacity);
int PmReadCommand(PmReadFn readfn, void *context, const PmGroup *group,
                  unsigned index, char *command, unsigned capacity);
/* Extract only the executable token; command itself is not modified. */
int PmCommandToken(const char *command, char *token, unsigned capacity);
/* 1 = bare filename, 2 = absolute drive path, 0 = unsupported/ambiguous. */
int PmTokenKind(const char *token);

#endif
