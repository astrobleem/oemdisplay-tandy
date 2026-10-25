/* Native CGA packet entry, DOS 3.3+, C89 /G0 /AS. Real files in ./CGA.
 * Reuses the staged TEXT80 INI transaction, never the published SETUP binary.
 * Payload copies are new-name or byte-identical only. A small owned-copy
 * journal makes failure/UNDO cleanup bounded to this packet's created files.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <io.h>
#ifndef HOST_TEST
#include <dos.h>
#endif

typedef unsigned long U32;
typedef char cga_u32_check[sizeof(U32)==4?1:-1];
#include "CRCFAST.H"
typedef struct {const char *name,*target;U32 size,crc;} CGAFILE;
#include "CGAPINS.H"
static int cga_small;
static int cga_discard(void);
#ifdef HOST_TEST
#include "HOSTTEST.H"
#endif
#include "INICGA.C"

static unsigned char copybuf[1024],owned[CGA_COUNT];
static char payload[160],systemdir[160],srcpath[160],dstpath[160],tmppath[160];

static int plain_dos(void)
{
#ifndef HOST_TEST
    union REGS r;
    memset(&r,0,sizeof(r));r.x.ax=0x1600;int86(0x2f,&r,&r);
    if(r.h.al && r.h.al!=0x80)return 0;
    memset(&r,0,sizeof(r));r.x.ax=0x4680;int86(0x2f,&r,&r);
    if(!r.x.ax)return 0;
#else
    if(getenv("CGA_WINDOWS"))return 0;
#endif
    return 1;
}

static int matches(const char *path,const CGAFILE *pin)
{
    FILE *f;unsigned n;U32 size=0,c=0xffffffffUL;int ok;
    f=fopen(path,"rb");if(!f)return 0;
    while((n=(unsigned)fread(copybuf,1,sizeof(copybuf),f))!=0){
        size+=n;c=fast_crc(c,copybuf,n);
        if(size>pin->size)break;
    }
    ok=!ferror(f) && size==pin->size && (c^0xffffffffUL)==pin->crc;
    if(fclose(f))ok=0;
    return ok;
}

static void paths(unsigned i)
{
    char *dot;
    join(srcpath,payload,cga_files[i].name);
    join(dstpath,systemdir,cga_files[i].target);
    strcpy(tmppath,dstpath);dot=strrchr(tmppath,'.');
    if(!dot)dot=tmppath+strlen(tmppath);
    strcpy(dot,".CGT");
}

static int save_plan(void)
{
    unsigned i;char *o=outbuf;U32 crc;
    o+=sprintf(o,"CGA COPY 1 %s\r\n",CGA_PACKET_ID);
    for(i=0;i<CGA_COUNT;i++)o+=sprintf(o,"%s %u\r\n",cga_files[i].name,(unsigned)owned[i]);
    crc=fast_crc(0xffffffffUL,(unsigned char *)outbuf,(unsigned)(o-outbuf))^0xffffffffUL;
    sprintf(o,"CRC %08lx\r\n",crc);
    if(!writenew(in("CGACOPY.NEW"),outbuf))return 0;
    if(rename(in("CGACOPY.NEW"),in("CGACOPY.STA"))){remove(in("CGACOPY.NEW"));return 0;}
    return 1;
}

static int load_plan_file(const char *file)
{
    unsigned i,flag;char *line,*end,extra;static char name[16],header[100];U32 crc,want;
    if(readfile(in(file))<0)return 0;
    sprintf(header,"CGA COPY 1 %s\r\n",CGA_PACKET_ID);
    if(strncmp(inbuf,header,strlen(header)))return 0;
    end=strstr(inbuf,"CRC ");if(!end)return 0;
    if(sscanf(end,"CRC %lx%c",&want,&extra)!=2 || extra!='\r')return 0;
    if(strlen(end)!=14 || strcmp(end+12,"\r\n"))return 0;
    crc=fast_crc(0xffffffffUL,(unsigned char *)inbuf,(unsigned)(end-inbuf))^0xffffffffUL;
    if(crc!=want)return 0;
    *end=0;line=strtok(inbuf,"\r\n");
    for(i=0;i<CGA_COUNT;i++){
        line=strtok(NULL,"\r\n");
        if(!line || sscanf(line,"%15s %u %c",name,&flag,&extra)!=2)return 0;
        if(strcmp(name,cga_files[i].name) || flag>2 ||
           (cga_files[i].target[0] ? flag==2 : flag!=2))return 0;
        owned[i]=(unsigned char)flag;
    }
    return strtok(NULL,"\r\n")==NULL;
}

static int load_plan(void){return load_plan_file("CGACOPY.STA");}

static int referenced(const char *name)
{
    unsigned j,k,n=(unsigned)strlen(name);int f;
    for(f=0;f<2;f++){
        if(readfile(in(f ? "WIN.INI" : "SYSTEM.INI"))<0)return 1;
        for(j=0;inbuf[j];j++){
            for(k=0;k<n && inbuf[j+k] && toupper((unsigned char)inbuf[j+k])==name[k];k++);
            if(k==n)return 1;
        }
    }
    return 0;
}

static int cleanup(void)
{
    unsigned i;int ok=1;
    for(i=0;i<CGA_COUNT;i++)if(owned[i]==0){
        paths(i);
        /* This temporary was absent before our sealed copy plan was saved. */
        if(exists(tmppath) && remove(tmppath))ok=0;
        if(exists(dstpath)){
            if(!matches(dstpath,&cga_files[i])){
                printf("SETUP: keeping changed file %s\n",dstpath);continue;
            }
            if(referenced(cga_files[i].target)){
                printf("SETUP: keeping referenced file %s\n",dstpath);continue;
            }
            if(remove(dstpath))ok=0;
        }
    }
    if(ok && exists(in("CGADONE.STA")) && remove(in("CGADONE.STA")))ok=0;
    if(ok && remove(in("CGACOPY.STA")))ok=0;
    return ok;
}

static int cga_discard(void)
{
    sprintf(outbuf,"CGA DONE 1 %s\r\n",CGA_PACKET_ID);
    return writenew(in("CGADONE.STA"),outbuf);
}

static int done_valid(void)
{
    static char expected[100];
    if(readfile(in("CGADONE.STA"))<0)return 0;
    sprintf(expected,"CGA DONE 1 %s\r\n",CGA_PACKET_ID);
    return strcmp(inbuf,expected)==0;
}

static int discard_ini_leftovers(void)
{
    static const char *names[]={"CGASET.STA","SYSTEM.CG0","WIN.CG0","SYSTEM.CGN","WIN.CGN","SYSTEM.CGO","WIN.CGO"};
    unsigned i;int ok=1;
    for(i=0;i<sizeof(names)/sizeof(names[0]);i++)if(exists(in(names[i])) && remove(in(names[i])))ok=0;
    return ok;
}

static int ini_state(void)
{
    return exists(in("CGASET.STA")) || exists(in("SYSTEM.CG0")) || exists(in("WIN.CG0")) ||
           exists(in("SYSTEM.CGN")) || exists(in("WIN.CGN")) ||
           exists(in("SYSTEM.CGO")) || exists(in("WIN.CGO"));
}

static int undo_ini(int whole)
{
    char *args[4];
    args[0]="CGASET";args[1]=whole ? "RESTORE" : "OFF";args[2]=(char *)dir;args[3]=NULL;
    return cga_ini_main(3,args);
}

/* Explicit whole-INI recovery only, after a valid packet copy record.
 * These private CGN/CGO names were absent at first preflight. Restore missing
 * live files from the two retained safety copies, then let the existing
 * transaction perform its normal checked two-file replacement. Never touch
 * another installer's leftovers or guess at legacy backup formats.
 */
static int prepare_restore(void)
{
    int i,found;char *p;const char *section;static char saved[160],live[160];
    for(i=0;i<2;i++){
        if(readfile(in(i ? "WIN.CG0" : "SYSTEM.CG0"))<=0)return 0;
        section=i ? "[windows]" : "[boot]";found=0;
        for(p=inbuf;*p;p++)if(!strnicmp(p,section,strlen(section))){found=1;break;}
        if(!found)return 0;
    }
    for(i=0;i<2;i++){
        strcpy(saved,in(i ? "WIN.CG0" : "SYSTEM.CG0"));strcpy(live,in(LIVE[i]));
        if(!exists(live) && (!copyfile(saved,live) || !samefile(saved,live)))return 0;
    }
    for(i=0;i<2;i++){
        if(exists(in(NEWF[i])) && remove(in(NEWF[i])))return 0;
        if(exists(in(OLDF[i])) && remove(in(OLDF[i])))return 0;
    }
    return 1;
}

static int preflight(void)
{
    unsigned i;
    for(i=0;i<CGA_COUNT;i++){
        paths(i);
        printf("SETUP: checking %s\n",cga_files[i].name);fflush(stdout);
        if(!matches(srcpath,&cga_files[i])){printf("SETUP: missing/damaged packet file %s\n",srcpath);return 0;}
        if(!cga_files[i].target[0]){owned[i]=2;continue;}
        if(exists(tmppath)){printf("SETUP: temporary already exists: %s\n",tmppath);return 0;}
        owned[i]=(unsigned char)(exists(dstpath)!=0);
        if(owned[i] && !matches(dstpath,&cga_files[i])){
            printf("SETUP: different installed file %s; nothing replaced\n",dstpath);return 0;
        }
    }
    return 1;
}

static int copy_payload(void)
{
    unsigned i,done=0;
    for(i=0;i<CGA_COUNT;i++)if(owned[i]==0){
        paths(i);
        printf("SETUP: installing %s\n",cga_files[i].name);fflush(stdout);
        if(exists(dstpath) || !copyfile(srcpath,tmppath) || !matches(tmppath,&cga_files[i]) || rename(tmppath,dstpath))
            return 0;
        done++;
#ifdef HOST_TEST
        if(getenv("CGA_STOP_AFTER_COPY") && done==(unsigned)atoi(getenv("CGA_STOP_AFTER_COPY")))return -1;
#endif
    }
    return 1;
}

static int payload_location(const char *exe)
{
    char *last,*slash;
    if(strlen(exe)>110)return 0;
    strcpy(payload,exe);last=strrchr(payload,'\\');slash=strrchr(payload,'/');
    if(slash && (!last || slash>last))last=slash;
    if(last)last[1]=0;else payload[0]=0;
    strcat(payload,"CGA");return 1;
}

int main(int argc,char **argv)
{
    unsigned i;int rc,whole=0;const char *mode;char *args[6];
    if(argc!=3){
        puts("IBM CGA / Windows 3.0 real-mode display setup (existing Windows required).");
        puts("SETUP C:\\WINDOWS 100|320|640   (select mode; start WIN /R afterward)");
        puts("SETUP UNDO C:\\WINDOWS         (undo this packet's changes)");
        puts("SETUP RESTORE C:\\WINDOWS      (saved INIs whole; loses later INI edits)");
        return 1;
    }
    if(!plain_dos())return fail("Exit Windows completely before running SETUP.");
    if(!stricmp(argv[1],"UNDO") || !stricmp(argv[1],"RESTORE")){
        whole=!stricmp(argv[1],"RESTORE");dir=argv[2];mode=NULL;
    }else{dir=argv[1];mode=argv[2];}
    if(!dir[0] || strlen(dir)>110)return fail("Windows path is empty or too long.");
    join(systemdir,dir,"SYSTEM");
    if(!exists(in("WIN.COM")) || !exists(systemdir))return fail("Existing Windows directory and SYSTEM folder required.");
    if(!mode){
        if(!exists(in("CGACOPY.STA")) && exists(in("CGACOPY.NEW"))){
            if(!load_plan_file("CGACOPY.NEW") || ini_state() || exists(in("CGADONE.STA")))
                return fail("Pending copy record is unrecognized; files kept.");
            /* No payload copying can precede the NEW-to-STA rename. */
            for(i=0;i<CGA_COUNT;i++)if(owned[i]==0){
                paths(i);if(exists(dstpath) || exists(tmppath))return fail("Unexpected files beside pending copy record; kept.");
            }
            if(remove(in("CGACOPY.NEW")))return fail("Could not remove owned pending record; retry UNDO.");
            puts("SETUP: pending copy plan cancelled; configuration unchanged.");return 0;
        }
        if(!load_plan())return fail("Copy record missing/damaged or from another packet; files kept.");
        if(exists(in("CGADONE.STA")) && !done_valid()){
            if(!whole)return fail("Cleanup marker damaged; files kept. SETUP RESTORE can use complete safety INIs.");
            if(!prepare_restore() || remove(in("CGADONE.STA")))return fail("Safety INIs/cleanup marker need diagnosis; files kept.");
        }
        if(!done_valid()){
            if(whole && ini_state() && !prepare_restore())return fail("Safety INIs incomplete; files kept.");
            if(ini_state() && undo_ini(whole))return 1;
        }
        if(done_valid() && !discard_ini_leftovers())return fail("Owned INI cleanup incomplete; retry UNDO.");
        if(!cleanup())return fail("Owned-copy cleanup incomplete; record kept for another UNDO.");
        puts("SETUP: CGA changes undone. Start Windows normally.");return 0;
    }
    if(strcmp(mode,"100") && strcmp(mode,"320") && strcmp(mode,"640"))return fail("Choose 100, 320 or 640.");
    if(readfile(in("SYSTEM.INI"))<0 || readfile(in("WIN.INI"))<0)
        return fail("Cannot read Windows INIs, or an INI exceeds 20000 bytes; nothing copied.");
    cga_small=!strcmp(mode,"100");
    if(!payload_location(argv[0]))return fail("Packet path too long.");
    if(exists(in("CGACOPY.NEW")))return fail("Incomplete copy record; no files changed. Keep it for diagnosis.");
    if(exists(in("CGADONE.STA")))return fail("Prior undo cleanup pending. Run SETUP UNDO first.");
    if(exists(in("CGACOPY.STA"))){
        if(!load_plan())return fail("Copy record damaged/different packet; files kept.");
        for(i=0;i<CGA_COUNT;i++)if(cga_files[i].target[0]){
            paths(i);
            if(!matches(dstpath,&cga_files[i]) || exists(tmppath))
                return fail("Incomplete/changed CGA installation. Run SETUP UNDO first.");
        }
        if(ini_state()){
            if(undo_ini(0))return 1;
            if(!done_valid() || !discard_ini_leftovers() || remove(in("CGADONE.STA")))
                return fail("Prior mode cleanup incomplete; run SETUP UNDO.");
        }
    }else{
        if(ini_state())return fail("CGA INI state exists without its copy record; files kept.");
        if(!preflight() || !save_plan())return fail("Preflight/copy record failed; configuration unchanged.");
        rc=copy_payload();
        if(rc<0)return 91;
        if(!rc){cleanup();return fail("Payload copy failed; configuration unchanged.");}
    }
    args[0]="CGASET";args[1]="ON";args[2]=(char *)dir;
    args[3]=cga_small ? "CGA100.DRV" : !strcmp(mode,"320") ? "CGA320.DRV" : "CGA640.DRV";
    args[4]="/C";args[5]=NULL;
    rc=cga_ini_main(cga_small ? 5 : 4,args);
    if(rc){if(!ini_state())cleanup();return 1;}
    puts("SETUP: selected CGA mode and fonts installed. Start Windows with WIN /R.");
    puts("Mode changes require exiting Windows and rerunning SETUP. Keep this packet for UNDO.");
    return 0;
}
