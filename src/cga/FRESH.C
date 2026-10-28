/* DOS 3.3+, 8086. Launch original Windows 3.0 Setup with a closed OEM kit.
 * No OS files or installed settings are changed by this launcher.
 * Copyright 2026. Permission to use, modify and redistribute this source.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <dos.h>
#include <direct.h>
#include <process.h>
typedef unsigned long U32;
typedef char fresh_u32_check[sizeof(U32)==4?1:-1];
#include "CRCFAST.H"
typedef struct {const char *name;U32 size,crc;} FRESHPIN;
#include "FRESHID.H"
static char source[160],setup[160],kit[160],path[160];
static unsigned char buffer[1024];

static int join(char *out,const char *dir,const char *name)
{
    unsigned n=(unsigned)strlen(dir);
    if(!n || n+strlen(name)+2>160)return 0;
    strcpy(out,dir);
    if(out[n-1]!='\\')strcat(out,"\\");
    strcat(out,name);return 1;
}

static int matches(const char *file,U32 size,U32 crc)
{
    FILE *f;unsigned n;U32 used=0,c=0xffffffffUL;int ok;
    f=fopen(file,"rb");if(!f)return 0;
    while((n=(unsigned)fread(buffer,1,sizeof(buffer),f))!=0){
        used+=n;c=fast_crc(c,buffer,n);if(used>size)break;
    }
    ok=!ferror(f) && used==size && (c^0xffffffffUL)==crc;
    if(fclose(f))ok=0;return ok;
}

static int plain_dos(void)
{
    union REGS r;
    memset(&r,0,sizeof(r));r.h.ah=0x30;int86(0x21,&r,&r);
    if(r.h.al<3 || (r.h.al==3 && r.h.ah<30))return 0;
    memset(&r,0,sizeof(r));r.x.ax=0x1600;int86(0x2f,&r,&r);
    if(r.h.al && r.h.al!=0x80)return 0;
    memset(&r,0,sizeof(r));r.x.ax=0x4680;int86(0x2f,&r,&r);
    return r.x.ax!=0;
}

int main(int argc,char **argv)
{
    int check=argc==3 && !stricmp(argv[1],"/CHECK");
    unsigned i;char *last,*args[2],answer[16];
    if((argc!=2 && !check) || !strcmp(argv[1],"/?")){
        puts("CGA fresh Windows 3.0 Setup - 640x200 monochrome");
        puts("FRESH A:\\                 Original first Windows Setup disk");
        puts("FRESH C:\\W30SRC           Original Windows media in one folder");
        puts("FRESH /CHECK C:\\W30SRC    Verify inputs without starting Setup");
        puts("English retail Windows 3.0, IBM CGA RGBI, 640K, plain DOS 3.3+.");
        puts("Keep FRESH640 beside FRESH.EXE. Read FRESH.TXT before installing.");
        return 1;
    }
    if(!plain_dos()){puts("Exit Windows completely; DOS 3.3+ is required.");return 2;}
    if(!_fullpath(source,argv[check?2:1],sizeof(source)) || strlen(source)>110 ||
       !join(setup,source,"SETUP.EXE") || !matches(setup,202432UL,0x4a674ebdUL) ||
       !join(path,source,"SETUP.INF") || !matches(path,49046UL,0x92333a90UL)){
        puts("Original English retail Windows 3.0 Setup files not recognized.");
        puts("Use the first original disk or a complete original-media folder.");
        puts("No files changed.");return 3;
    }
    if(!_fullpath(kit,argv[0],sizeof(kit)) || !(last=strrchr(kit,'\\'))){
        puts("Cannot locate this kit. Run FRESH from its extracted directory.");return 4;
    }
    last[1]=0;
    if(strlen(kit)>110){puts("Extract the kit in a shorter DOS directory.");return 4;}
    strcat(kit,"FRESH640");
    for(i=0;i<FRESH_COUNT;i++)if(!join(path,kit,fresh_files[i].name) ||
       !matches(path,fresh_files[i].size,fresh_files[i].crc)){
        printf("Missing or changed kit file: %s\nExtract the complete kit again. No files changed.\n",fresh_files[i].name);return 4;
    }
    puts("Original Setup and CGA fresh-install files verified.");
    printf("Display driver path: %s\n",kit);
    if(check)return 0;
    puts("Write down that path. In original Windows Setup:");
    puts("  1. Choose a new Windows directory.");
    puts("  2. At System Information, choose Display, then Other (last choice).");
    puts("  3. Enter the display driver path above and select Windows XT IBM CGA.");
    puts("  4. Confirm No Changes to accept the hardware list; finish Setup normally.");
    puts("     Give the same driver path whenever Windows requests our driver disk.");
    puts("Use your original Windows disks for all Microsoft file requests.");
    puts("After Setup, use WIN /R. See FRESH.TXT for other CGA modes.");
    printf("Press ENTER to start original Setup, or Q then ENTER to cancel: ");fflush(stdout);
    if(!fgets(answer,sizeof(answer),stdin) || (answer[0]!='\r' && answer[0]!='\n')){
        puts("Cancelled. No files changed.");return 0;
    }
    if(source[1]!=':' || _chdrive(toupper(source[0])-'A'+1) || chdir(source)){
        puts("Cannot enter the original media directory. No files changed.");return 5;
    }
    args[0]=setup;args[1]=NULL;
    execv(setup,(const char * const *)args);
    perror("Original Windows Setup could not start");return 5;
}
