#ifndef RAWREAD_H
#define RAWREAD_H

/* Microsoft C 6.0 small model. Zero means success. Not a write API. */
#define RD_OK 0
#define RD_ENV 1
#define RD_DRIVE 2
#define RD_REMOTE 3
#define RD_REMOV 4
#define RD_IOCTL 5
#define RD_GEOM 6
#define RD_MEMORY 7
#define RD_RANGE 8
#define RD_IO 9
#define RD_BUSY 10
#define RD_MAPPED 11

typedef struct RD_VOLUME {
    unsigned drive;
    unsigned attributes;
    unsigned packet;
    unsigned status;
    unsigned dos_error;
    unsigned opened;
    unsigned busy;
    unsigned selector;
    unsigned char far *buffer;
    unsigned long sectors;
    unsigned long reads;
    unsigned char bpb[25];
} RD_VOLUME;

int RdOpen(RD_VOLUME *v, unsigned drive_zero_based);
int RdRead(void *context, unsigned long sector,
           unsigned char far *destination512);
int RdBootMatches(RD_VOLUME *v, const unsigned char far *boot512);
void RdClose(RD_VOLUME *v);
/* 1 only when full uppercase absolute short path maps to itself. */
int RdPathIdentity(const char *path);

/* Only for disposable image fixture diagnostics, never UI callers. */
#ifdef RD_LAB
unsigned RdAbsRead(unsigned drive, unsigned packet, unsigned long sector,
                   unsigned char far *buffer);
#endif
#endif
