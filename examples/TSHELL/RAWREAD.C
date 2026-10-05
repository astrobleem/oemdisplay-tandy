/* Read-only sector transport. Target: MS-DOS 6.22 + Windows 3.0 REAL mode.
 * See README.TXT for the remaining integration gates. No INT 13/26 or writes.
 */
#ifndef RD_DOS
#include <windows.h>
#endif
#include <dos.h>
#include <string.h>
#include "RAWREAD.H"

static unsigned rdWord(const unsigned char far *p)
{ return (unsigned)p[0] | ((unsigned)p[1] << 8); }
static unsigned long rdLong(const unsigned char far *p)
{ return (unsigned long)rdWord(p) | ((unsigned long)rdWord(p+2) << 16); }

/* INT25 leaves the ORIGINAL FLAGS word on the stack. CF returned live is
 * captured first. BP may be destroyed by DOS, so restore it before touching
 * any compiler local. Preserve all other registers required by Microsoft C.
 */
#ifndef RD_LAB
static
#endif
unsigned RdAbsRead(unsigned drive, unsigned packet, unsigned long sector,
                   unsigned char far *buffer)
{
    struct { unsigned long sector; unsigned count;
             unsigned char far *buffer; } request;
    unsigned failed, error, lowsector;
    lowsector=(unsigned)sector;
    request.sector=sector; request.count=1; request.buffer=buffer;
    _asm {
        push bx
        push cx
        push dx
        push si
        push di
        push ds
        push es
        mov ax,drive
        cmp packet,0
        jne packet_read
        lds bx,buffer
        mov dx,lowsector
        mov cx,1
        jmp do_read
    packet_read:
        lea bx,word ptr request
        push ss
        pop ds
        mov cx,0ffffh
    do_read:
        push bp
        int 25h
        sbb cx,cx
        popf
        pop bp
        pop es
        pop ds
        mov failed,cx
        mov error,ax
        pop di
        pop si
        pop dx
        pop cx
        pop bx
    }
    return failed ? (error ? error : 0xffff) : 0;
}

static unsigned rdIoctl(unsigned drive, unsigned function,
                        unsigned char far *buffer, unsigned *value)
{
    unsigned error, failed, result;
    _asm {
        push bx
        push cx
        push dx
        push ds
        mov bx,drive
        inc bx
        mov ax,function
        mov cx,0860h
        lds dx,buffer
        int 21h
        sbb cx,cx
        mov bx,ax
        cmp function,4409h
        jne ioctl_ax
        mov bx,dx
    ioctl_ax:
        pop ds
        mov result,bx
        mov error,ax
        mov failed,cx
        pop dx
        pop cx
        pop bx
    }
    *value=result;
    return failed ? (error ? error : 0xffff) : 0;
}

static unsigned rdVersion(void)
{
    unsigned version;
    _asm {
        push bx
        push dx
        mov bx,0
        mov ax,3306h
        int 21h
        mov version,bx
        pop dx
        pop bx
    }
    return version;
}

/* Documented DOS5 INT2F/0600: refuse every drive while ASSIGN is resident. */
static unsigned rdAssignLoaded(void)
{
    unsigned result;
    _asm {
        push bx
        push cx
        push dx
        push si
        push di
        push ds
        push es
        push bp
        mov ax,0600h
        int 2fh
        pop bp
        pop es
        pop ds
        xor ah,ah
        mov result,ax
        pop di
        pop si
        pop dx
        pop cx
        pop bx
    }
    return result;
}

/* Conservative global presence rejection. Verified in the original owned
 * DOS6.22 DRVSPACE.BIN; not a guarantee against third-party compression.
 * No volume compression, mounting or configuration is requested.
 */
static unsigned rdDriveSpacePresent(void)
{
    unsigned resultax,resultbx;
    _asm {
        push bx
        push cx
        push dx
        push si
        push di
        push ds
        push es
        push bp
        mov ax,4a11h
        xor bx,bx
        int 2fh
        pop bp
        pop es
        pop ds
        mov resultax,ax
        mov resultbx,bx
        pop di
        pop si
        pop dx
        pop cx
        pop bx
    }
    return resultax==0 && resultbx==0x444d;
}

/* DOS4 Microsoft source names AH60 $NameTrans. This is an undocumented
 * compatibility gate, tested specifically on DOS6.22, not a general API.
 */
static unsigned rdTrueName(const char far *source, char far *target)
{
    unsigned failed;
    _asm {
        push bx
        push cx
        push dx
        push si
        push di
        push ds
        push es
        lds si,source
        les di,target
        mov ax,6000h
        int 21h
        sbb cx,cx
        pop es
        pop ds
        mov failed,cx
        pop di
        pop si
        pop dx
        pop cx
        pop bx
    }
    return failed;
}

int RdPathIdentity(const char *path)
{
    char target[128];
    unsigned i,n,error;
#ifndef RD_DOS
    unsigned oldmode;
    if(GetWinFlags()&WF_PMODE) return 0;
#endif
    if(!path || rdVersion()!=0x1606 || rdAssignLoaded() || rdDriveSpacePresent()) return 0;
    for(n=0;n<80 && path[n];n++)
        if((unsigned char)path[n]<32 || (unsigned char)path[n]>126 ||
           path[n]=='/' || path[n]=='*' || path[n]=='?') return 0;
    if(n<3 || n>=80 || path[0]<'A' || path[0]>'Z' ||
       path[1]!=':' || path[2]!='\\') return 0;
    memset(target,0,sizeof(target));
#ifndef RD_DOS
    oldmode=SetErrorMode(1);
#endif
    error=rdTrueName((const char far *)path,(char far *)target);
#ifndef RD_DOS
    SetErrorMode(oldmode);
#endif
    if(error) return 0;
    for(i=0;i<=n;i++) if(target[i]!=path[i]) return 0;
    return 1;
}

void RdClose(RD_VOLUME *v)
{
    if(v->selector) {
#ifdef RD_DOS
        _dos_freemem(v->selector);
#else
        GlobalDosFree(v->selector);
#endif
    }
    v->selector=0; v->buffer=0; v->opened=0; v->busy=0;
}

static int rdProbe(RD_VOLUME *v)
{
    unsigned n,i,align,spc,fats,reserved,roots,spf,clusters;
    unsigned long allocation,metadata,data;
    unsigned char far *b;
    if(rdVersion()!=0x1606) return RD_ENV;
    if(rdAssignLoaded() || rdDriveSpacePresent()) return RD_MAPPED;
    if(v->drive>25) return RD_DRIVE;
    v->dos_error=rdIoctl(v->drive,0x4409,0,&n);
    if(v->dos_error) return RD_IOCTL;
    v->attributes=n;
    if(n & 0x9200) return RD_REMOTE; /* network, SUBST or shared */
    if((n & 0x0840)!=0x0840) return RD_IOCTL;
    v->dos_error=rdIoctl(v->drive,0x4408,0,&n);
    if(v->dos_error) return RD_IOCTL;
    if(n!=1) return RD_REMOV;
#ifdef RD_DOS
    if(_dos_allocmem(64,&v->selector)) return RD_MEMORY;
    allocation=(unsigned long)v->selector<<16;
#else
    allocation=GlobalDosAlloc(1024L);
    if(!allocation) return RD_MEMORY;
    v->selector=LOWORD(allocation);
#endif
    /* A physical 512-byte alignment also prevents 64KiB DMA crossings. */
    n=(unsigned)(allocation>>16);
    align=(unsigned)(0-(n<<4)) & 511;
    v->buffer=(unsigned char far *)(((unsigned long)n<<16)|align);
    b=v->buffer;
    for(i=0;i<512;i++) b[i]=0;
    b[0]=1; /* current medium, never Set Device Parameters */
    v->dos_error=rdIoctl(v->drive,0x440d,b,&n);
    if(v->dos_error) return RD_IOCTL;
    if(b[1]!=5 || !(rdWord(b+2)&1)) return RD_REMOV;
    for(i=0;i<25;i++) v->bpb[i]=b[i+7];
    b+=7;
    if(rdWord(b)!=512) return RD_GEOM;
    spc=b[2]; reserved=rdWord(b+3); fats=b[5]; roots=rdWord(b+6);
    spf=rdWord(b+11);
    v->sectors=rdWord(b+8);
    if(!v->sectors) v->sectors=rdLong(b+21);
    if(!spc || spc>64 || (spc&(spc-1)) || !reserved ||
       (fats!=1 && fats!=2) || !roots || !spf || !v->sectors)
        return RD_GEOM;
    metadata=(unsigned long)reserved+(unsigned long)fats*spf+
             (((unsigned long)roots*32+511)/512);
    if(metadata>=v->sectors) return RD_GEOM;
    data=(v->sectors-metadata)/spc;
    if(!data || data>=65525L) return RD_GEOM;
    clusters=(unsigned)data;
    if(clusters<4085) {
        if(((data+2)*3+1)/2 > (unsigned long)spf*512) return RD_GEOM;
    } else if((data+2)*2 > (unsigned long)spf*512) return RD_GEOM;
    v->packet=(v->attributes&2)!=0 || v->sectors>65535L;
    v->opened=1;
    return RD_OK;
}

int RdOpen(RD_VOLUME *v, unsigned drive)
{
    int result;
#ifndef RD_DOS
    unsigned oldmode;
#endif
    memset(v,0,sizeof(*v)); v->drive=drive;
#ifndef RD_DOS
    if(GetWinFlags()&WF_PMODE) return v->status=RD_ENV;
    oldmode=SetErrorMode(1);
#endif
    result=rdProbe(v);
#ifndef RD_DOS
    SetErrorMode(oldmode);
#endif
    if(result) RdClose(v);
    v->status=result;
    return result;
}

int RdRead(void *context, unsigned long sector,
           unsigned char far *destination)
{
    RD_VOLUME *v=(RD_VOLUME *)context;
    unsigned i;
    if(!v->opened || !destination || sector>=v->sectors)
        return v->status=RD_RANGE;
    if(v->busy) return v->status=RD_BUSY;
    v->busy=1;
    v->dos_error=RdAbsRead(v->drive,v->packet,sector,v->buffer);
    ++v->reads;
    if(!v->dos_error) for(i=0;i<512;i++) destination[i]=v->buffer[i];
    v->busy=0;
    return v->status=v->dos_error ? RD_IO : RD_OK;
}

int RdBootMatches(RD_VOLUME *v, const unsigned char far *boot)
{
    unsigned i;
    if(!v->opened || boot[510]!=0x55 || boot[511]!=0xaa) return 0;
    for(i=0;i<25;i++) if(v->bpb[i]!=boot[i+11]) return 0;
    return 1;
}
