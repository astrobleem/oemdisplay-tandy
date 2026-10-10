/* TINST.C - guarded DOS 3.3+ / 8088 helper installer, Microsoft C 6.
 * Snapshot files are create-new only. SETUP owns display installation.
 * Optional SHELLSEL recovery precedes snapshots; restore is explicit.
 * Build: CL /AS /G0 /W3 TINST.C
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <dos.h>
#include <direct.h>
#include <fcntl.h>
#include <io.h>
#include <process.h>
#ifdef INSTALL_DIAGNOSTICS
#include <time.h>
#define DIAG(x) x
#else
#define DIAG(x)
#endif
#define MAXF 256
#define PTH 80
#define HELP src
struct saved { char src[PTH]; char rel[24]; unsigned long size; };
static struct saved files[MAXF];
static int count, recovery, computer_changed, deep_verify;
#ifdef INSTALL_DIAGNOSTICS
static unsigned long copy_bytes, compare_bytes;
static clock_t copy_ticks, compare_ticks;
#endif
static char win[PTH], sys[PTH], src[PTH], bak[PTH], bakroot[PTH];
static unsigned char buf[4096], verifybuf[4096];
static unsigned long total;

static void fail(char *message, char *detail)
{
    printf("STOP: %s\n%s\n", message, detail ? detail : "");
    printf("Windows and Setup were NOT started.\n");
    if(recovery) puts("SHELLSEL recovery was requested. Review its result before retrying.");
    else if(computer_changed) puts("The optional Computer choice was prepared. Keep its CPINFO files and use the verified rollback instructions.");
    else puts("Original Windows files were not changed.");
    if (bak[0]) printf("Keep and review partial backup %s; do not use incomplete helpers.\n", bak);
    exit(1);
}
static void join(char *out, char *dir, char *name)
{
    if (strlen(dir)+strlen(name)+2>PTH) fail("Path too long.",dir);
    strcpy(out,dir); strcat(out,"\\"); strcat(out,name);
}
static int exists(char *path)
{
    unsigned a, r;
    r=_dos_getfileattr(path,&a);
    if (!r) return 1;
    if (r==2 || r==3) return 0;
    fail("Cannot safely inspect path.",path); return 0;
}
static int regular(char *path)
{
    unsigned a;
    return !_dos_getfileattr(path,&a) && !(a & (_A_SUBDIR|_A_VOLID));
}
static int safeleaf(char *s)
{
    int b=0,e=0,dot=0; char ch;
    if (!*s) return 0;
    while ((ch=*s++)!=0) {
        if (ch=='.') {if(dot || b==0) return 0; dot=1; continue;}
        if (!isalnum((unsigned char)ch) && ch!='_' && ch!='~' && ch!='-' && ch!='$') return 0;
        if (dot) e++; else b++;
    }
    return b<=8 && e<=3 && (!dot || e>0);
}
static int safepath(char *s)
{
    char t[PTH], *p, *q;
    if (strlen(s)>63 || strlen(s)<4 || !isalpha((unsigned char)s[0]) || s[1]!=':' || s[2]!='\\') return 0;
    strcpy(t,s+3); p=t;
    for (;;) {
        q=strchr(p,'\\'); if(q) *q=0;
        if (!safeleaf(p)) return 0;
        if(!q) break; p=q+1;
    }
    return 1;
}
static void add(char *path, char *rel)
{
    struct find_t f; int i;
    for(i=0;i<count;i++) if (!stricmp(files[i].src,path)) return;
    if (count>=MAXF) fail("Too many display/font files (maximum 256).",path);
    if (strlen(rel)>=sizeof(files[0].rel)) fail("Backup filename too long.",rel);
    if (_dos_findfirst(path,_A_RDONLY|_A_HIDDEN|_A_SYSTEM|_A_ARCH,&f) || (f.attrib&_A_SUBDIR)) fail("Required backup file missing or unreadable.",path);
    strcpy(files[count].src,path); strcpy(files[count].rel,rel);
    files[count].size=f.size; total+=f.size+4096UL; count++;
}
static void group(char *dir, char *sub, char *pattern)
{
    struct find_t f; char path[PTH], mask[PTH], rel[24]; unsigned r;
    join(mask,dir,pattern); r=_dos_findfirst(mask,_A_RDONLY|_A_HIDDEN|_A_SYSTEM|_A_ARCH,&f);
    while(!r) {
        if(!(f.attrib&_A_SUBDIR)) {
            if (!safeleaf(f.name)) fail("Unsupported DOS file name.",f.name);
            join(path,dir,f.name); sprintf(rel,"%s\\%s",sub,f.name); add(path,rel);
        }
        r=_dos_findnext(&f);
    }
    if(r!=2 && r!=3 && r!=18) fail("Cannot enumerate backup files.",mask);
}
static char *trim(char *s)
{
    char *end; while(*s && isspace((unsigned char)*s)) s++;
    end=s+strlen(s); while(end>s && isspace((unsigned char)end[-1])) *--end=0;
    return s;
}
static void ref(char *value)
{
    char name[PTH], path[PTH], rel[24]; char *p; int i;
    if (!*value) return;
    if(strlen(value)>=PTH) fail("An INI reference is too long.",value);
    strcpy(name,value); strupr(name); p=name;
    if (!strncmp(name,win,strlen(win)) && name[strlen(win)]=='\\') p=name+strlen(win)+1;
    if(!strncmp(p,"SYSTEM\\",7)) {
        p+=7; if(!safeleaf(p)) fail("Unsupported active resource path.",value);
        join(path,sys,p); sprintf(rel,"SYSTEM\\%s",p); add(path,rel); return;
    }
    if(!safeleaf(p)) fail("Resource is outside Windows root/SYSTEM; back it up manually first.",value);
    i=0; join(path,win,p);
    if(regular(path)) {sprintf(rel,"ROOT\\%s",p); add(path,rel); i=1;}
    join(path,sys,p);
    if(regular(path)) {sprintf(rel,"SYSTEM\\%s",p); add(path,rel); i=1;}
    if(!i) fail("An active display/font/grabber reference cannot be backed up.",value);
}
static void scanini(char *filename, int fonts)
{
    FILE *f; char path[PTH], line[512], *p, *v; int section=0, required=0, mask=0, k;
    char *keys[]={"display.drv","fonts.fon","fixedfon.fon","oemfonts.fon","286grabber","386grabber"};
    join(path,win,filename); f=fopen(path,"rt"); if(!f) fail("Cannot read INI.",path);
    while(fgets(line,sizeof(line),f)) {
        if(!strchr(line,'\n') && !feof(f)) fail("INI line exceeds 510 characters.",path);
        p=trim(line); if(*p==';' || !*p) continue;
        if(*p=='[') {section=!stricmp(p,fonts?"[fonts]":"[boot]"); continue;}
        if(!section) continue;
        v=strchr(p,'='); if(!v) continue; *v++=0; p=trim(p); v=trim(v);
        if(fonts) {ref(v); continue;}
        for(k=0;k<6;k++) if(!stricmp(p,keys[k])) {
            if(k<4) { if(!*v) fail("Required [boot] key is empty.",p); mask|=1<<k; required++; }
            ref(v); break;
        }
    }
    if(ferror(f) || fclose(f)) fail("INI read error.",path);
    if(!fonts && (mask!=15 || required!=4)) fail("Expected one each of display and three core-font [boot] keys.",path);
}
/* Read-only launcher eligibility query. 0=qualified TR5; 1=other; 2=error. */
static int shellsafe(char *dir)
{
    FILE *f; char path[PTH], line[512], value[PTH], *p, *v;
    int section=0, seen=0, bad=0, k;
    char *names[]={"TR53216.DRV","TR56404.DRV","TR51616.DRV","TR53204.DRV","TR56402.DRV"};
    if(!safepath(dir)) {puts("Cannot read shell eligibility: invalid Windows path."); return 2;}
    join(path,dir,"SYSTEM.INI"); f=fopen(path,"rt");
    if(!f) {puts("Cannot read shell eligibility: SYSTEM.INI is unavailable."); return 2;}
    while(fgets(line,sizeof(line),f)) {
        if(!strchr(line,'\n') && !feof(f)) {bad=1; break;}
        p=trim(line); if(*p==';' || !*p) continue;
        if(*p=='[') {section=!stricmp(p,"[boot]"); continue;}
        if(!section) continue;
        v=strchr(p,'='); if(!v) continue; *v++=0; p=trim(p); v=trim(v);
        if(stricmp(p,"display.drv")) continue;
        if(++seen!=1 || !*v || strlen(v)>=sizeof(value)) {bad=1; break;}
        strcpy(value,v);
    }
    if(ferror(f)) bad=1;
    if(fclose(f)) bad=1;
    if(bad || seen!=1) {puts("Cannot read shell eligibility: malformed [boot] display.drv."); return 2;}
    p=strrchr(value,'\\'); p=p?p+1:value;
    for(k=0;k<sizeof(names)/sizeof(names[0]);k++) if(!stricmp(p,names[k])) return 0;
    return 1;
}

/* Read-only byte comparator: 0=identical; 1=different; 2=I/O failure. */
static int comparefiles(char *left, char *right)
{
    int a,b,result=0; unsigned n,z,rc;
    if(_dos_open(left,O_RDONLY,&a)) return 2;
    if(_dos_open(right,O_RDONLY,&b)) {_dos_close(a); return 2;}
    do {
        if(_dos_read(a,buf,sizeof(buf),&n) || _dos_read(b,verifybuf,sizeof(verifybuf),&z)) {result=2; break;}
        if(n!=z || memcmp(buf,verifybuf,n)) {result=1; break;}
    } while(n);
    rc=_dos_close(a); rc|=_dos_close(b); if(rc) result=2;
    if(result) puts("File byte comparison failed. Do not start Windows.");
    return result;
}

static void copynew(char *from, char *to, unsigned long expected)
{
    int a,b,c; unsigned n,m,z,date,time,rc; unsigned long copied=0; DIAG(clock_t started=clock();)
    if(_dos_open(from,O_RDONLY,&a)) fail("Cannot open source.",from);
    if(_dos_creatnew(to,_A_NORMAL,&b)) {_dos_close(a); fail("Cannot create NEW backup/helper; refusing overwrite.",to);}
    if(_dos_getftime(a,&date,&time)) fail("Cannot read file timestamp.",from);
    do {
        if(_dos_read(a,buf,sizeof(buf),&n)) fail("Source read failed.",from);
        if(n && (_dos_write(b,buf,n,&m) || m!=n)) fail("Copy failed (disk full or write error).",to);
        copied+=n; DIAG(copy_bytes+=n;)
        if(copied>expected) fail("Source size changed during backup.",from);
    } while(n);
    if(copied!=expected) fail("Source size changed during backup.",from);
    if(_dos_setftime(b,date,time)) fail("Cannot preserve backup timestamp.",to);
    rc=_dos_close(b); rc|=_dos_close(a); if(rc) fail("File close failed.",to);
    DIAG(copy_ticks+=clock()-started;)
    if(!deep_verify) return;
    DIAG(started=clock();)
    if(_dos_open(from,O_RDONLY,&a) || _dos_open(to,O_RDONLY,&c)) fail("Cannot reopen copy for verification.",to);
    do {
        if(_dos_read(a,buf,sizeof(buf),&n) || _dos_read(c,verifybuf,sizeof(verifybuf),&z) || n!=z || memcmp(buf,verifybuf,n)) fail("Byte-for-byte copy verification failed.",to);
    } while(n);
    DIAG(compare_bytes+=copied; compare_ticks+=clock()-started;)
    rc=_dos_close(a); rc|=_dos_close(c); if(rc) fail("Verification close failed.",to);
}
static int newtext(char *path)
{
    int h; if(_dos_creatnew(path,_A_NORMAL,&h)) fail("Cannot create NEW text file.",path); return h;
}
static void put(int h,char *s)
{
    unsigned n,z; n=strlen(s); if(_dos_write(h,s,n,&z) || z!=n) fail("Text write failed (possibly disk full).",bak);
}
static void closeout(int h)
{
    if(_dos_close(h)) fail("Text close failed.",bak);
}
/* Setup's second disk prompt must not resolve "." against Windows.
 * Preserve the exact media INF; create/close the localized INF before renames.
 * No driver files or installed Windows INIs are written here.
 */
static void sourceinf(void)
{
    FILE *f;
    int h, section=0, rows=0;
    char original[PTH], saved[PTH], temp[PTH], line[512], check[512];
    char *p;
    join(original,src,"OEMSETUP.INF");
    join(saved,src,"OEMBASE.INF");
    join(temp,src,"OEMSETUP.NEW");
    f=fopen(original,"rt");
    if(!f) fail("Cannot read source INF.",original);
    h=newtext(temp);
    while(fgets(line,sizeof(line),f)) {
        if(!strchr(line,'\n') && !feof(f))
            fail("Source INF line too long.",original);
        strcpy(check,line); p=trim(check);
        if(*p=='[') section=!stricmp(p,"[disks]");
        if(section && !strcmp(p,
           "a = ., \"Windows XT All-in-One\", OEMSETUP.INF")) {
            sprintf(line,
              "a = %s, \"Windows XT All-in-One\", OEMSETUP.INF\n",src);
            rows++;
        }
        /* Text input normalizes CRLF; output stays explicit DOS CRLF. */
        p=strchr(line,'\n'); if(p) *p=0;
        put(h,line); put(h,"\r\n");
    }
    if(ferror(f) || fclose(f) || rows!=1)
        fail("Expected one original Windows XT disk path.",original);
    closeout(h);
    /* The preserved original is the rollback copy, never overwritten. */
    if(rename(original,saved) || rename(temp,original))
        fail("Source INF rename failed; keep partial files.",src);
}

static void makefiles(void)
{
    int h,i; char path[PTH], target[PTH], line[512];
    join(path,bak,"FILES.TXT"); h=newtext(path);
    sprintf(line,"Tandy display pre-SETUP rollback snapshot\r\nWindows=%s\r\nSource=%s\r\nCopy read/write/close checks completed. Deep verification=%s.\r\n\r\n",win,src,deep_verify?"ON":"OFF"); put(h,line);
    for(i=0;i<count;i++) {sprintf(line,"%s <- %s (%lu bytes)\r\n",files[i].rel,files[i].src,files[i].size); put(h,line);}
    closeout(h);
    join(path,bak,"RESTORE.BAT"); h=newtext(path);
    put(h,"@ECHO OFF\r\nREM Run only after exiting Windows completely, at a real DOS prompt.\r\nIF NOT \"%1\"==\"YES\" GOTO USAGE\r\nIF NOT \"%2\"==\"\" GOTO USAGE\r\n");
    sprintf(line,"IF NOT EXIST %s\\DONE.TAG GOTO FAIL\r\n",bak); put(h,line);
    sprintf(line,"IF EXIST %s\\SHREADY.TAG IF EXIST %s\\SHREADY.OFF GOTO FAIL\r\n",src,src); put(h,line);
    sprintf(line,"IF NOT EXIST %s\\TINST.EXE GOTO FAIL\r\n",src); put(h,line);
    /* Preflight ALL inputs before restoring any original. */
    for(i=0;i<count;i++) {sprintf(line,"IF NOT EXIST %s\\%s GOTO FAIL\r\n",bak,files[i].rel); put(h,line);}
    /* Reject edited/foreign Computer metadata before any rollback writes.
     * RESTORE validates its journal and exact generated states itself. */
    sprintf(line,"IF NOT EXIST %s\\CPSET.EXE GOTO FAIL\r\n%s\\CPSET.EXE RESTORE %s\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n",src,src,win); put(h,line);
    sprintf(line,"IF NOT EXIST %s\\WAVE01\\META.TXT GOTO WAVEOFF\r\nIF NOT EXIST %s\\WAVEXT.EXE GOTO FAIL\r\n%s\\WAVEXT.EXE RESTORE %s %s\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n:WAVEOFF\r\n",src,src,src,win,src); put(h,line);
    sprintf(line,"IF NOT EXIST %s\\SHELLSEL.EXE GOTO RECCHECK\r\n%s\\SHELLSEL.EXE RECOVER %s\\SYSTEM.INI\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n:RECCHECK\r\n",src,src,win); put(h,line);
    sprintf(line,"IF NOT EXIST %s\\XTMODE.EXE GOTO FAIL\r\n%s\\XTMODE.EXE FORGET %s\\SYSTEM.INI\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n",src,src,win); put(h,line);
    sprintf(line,"IF EXIST %s\\TSHELL.JRN GOTO FAIL\r\nIF EXIST %s\\TSHELL.NEW GOTO FAIL\r\nIF EXIST %s\\TSHELL.OLD GOTO FAIL\r\nIF EXIST %s\\TSHELL.RST GOTO FAIL\r\n",win,win,win,win); put(h,line);
    sprintf(line,"%s\\TINST.EXE /ZERO\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n",src); put(h,line);
    sprintf(line,"IF NOT EXIST %s\\SHREADY.TAG GOTO FILES\r\nREN %s\\SHREADY.TAG SHREADY.OFF\r\nIF EXIST %s\\SHREADY.TAG GOTO FAIL\r\nIF NOT EXIST %s\\SHREADY.OFF GOTO FAIL\r\n:FILES\r\n",src,src,src,src); put(h,line);
    for(i=0;i<count;i++) {
        sprintf(line,"COPY /B %s\\%s %s > NUL\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n",bak,files[i].rel,files[i].src); put(h,line);
        sprintf(line,"%s\\TINST.EXE /COMPARE %s\\%s %s\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n",src,bak,files[i].rel,files[i].src); put(h,line);
    }
    put(h,"ECHO Original Windows configuration and resources restored.\r\nECHO Added driver files and helpers remain; the restored INIs select the old display.\r\nGOTO DONE\r\n:USAGE\r\nECHO Exit Windows. This overwrites Windows files with the pre-install snapshot.\r\n");
    sprintf(line,"ECHO To restore: %s\\RESTORE YES\r\n",bak); put(h,line);
    put(h,"GOTO DONE\r\n:FAIL\r\nECHO Restore incomplete or blocked. Do not start Windows; check the backup/disk.\r\n:DONE\r\n"); closeout(h);
    join(path,bak,"DONE.TAG"); h=newtext(path); put(h,"Original-file snapshot complete. I/O and size checks passed.\r\n"); closeout(h);
    /* Payload and support files run in place. Never copy RESERVE onto itself. */
    join(path,HELP,"WINXT.BAT"); h=newtext(path);
    put(h,"@ECHO OFF\r\nREM Generated for this installation. Run only from a real DOS prompt.\r\nIF NOT \"%1\"==\"\" IF NOT \"%1\"==\"SETUP\" IF NOT \"%1\"==\"setup\" GOTO USAGE\r\nIF NOT \"%2\"==\"\" GOTO USAGE\r\n");
    sprintf(line,"IF NOT EXIST %s\\READY.TAG GOTO NOHELP\r\nIF NOT EXIST %s\\RESERVE.COM GOTO NOHELP\r\n",src,src); put(h,line);
    sprintf(line,"IF NOT EXIST %s\\WIN.COM GOTO NOWIN\r\nIF \"%%1\"==\"SETUP\" IF NOT EXIST %s\\SETUP.EXE GOTO NOWIN\r\nIF \"%%1\"==\"setup\" IF NOT EXIST %s\\SETUP.EXE GOTO NOWIN\r\n",win,win,win); put(h,line);
    sprintf(line,"IF NOT EXIST %s\\SHELLSEL.EXE GOTO RECOVERED\r\n%s\\SHELLSEL.EXE RECOVER %s\\SYSTEM.INI\r\nIF ERRORLEVEL 1 GOTO RECFAIL\r\n:RECOVERED\r\n",src,src,win); put(h,line);
    sprintf(line,"IF NOT EXIST %s\\XTMODE.EXE GOTO NOHELP\r\n%s\\XTMODE.EXE RECOVER %s\\SYSTEM.INI\r\nIF ERRORLEVEL 1 GOTO MODEFAIL\r\n",src,src,win); put(h,line);
    put(h,"IF \"%1\"==\"SETUP\" GOTO MODESET\r\nIF \"%1\"==\"setup\" GOTO MODESET\r\n");
    sprintf(line,"%s\\XTMODE.EXE GUARD %s\\SYSTEM.INI\r\nIF ERRORLEVEL 1 GOTO MODEFAIL\r\nGOTO MODEOK\r\n:MODESET\r\n",src,win); put(h,line);
    sprintf(line,"%s\\XTMODE.EXE ACCEPT %s\\SYSTEM.INI\r\nIF ERRORLEVEL 1 GOTO MODEFAIL\r\n:MODEOK\r\n",src,win); put(h,line);
    sprintf(line,"IF \"%%1\"==\"SETUP\" GOTO CPCHECK\r\nIF \"%%1\"==\"setup\" GOTO CPCHECK\r\nGOTO CPOK\r\n:CPCHECK\r\nIF NOT EXIST %s\\CPSET.EXE GOTO CPFAIL\r\n%s\\CPSET.EXE CHECK %s\r\nIF ERRORLEVEL 1 GOTO CPFAIL\r\n:CPOK\r\n",src,src,win); put(h,line);
    sprintf(line,"%s\\RESERVE.COM\r\nIF ERRORLEVEL 1 GOTO FAILED\r\n",src); put(h,line);
    sprintf(line,"%c:\r\nCD %s\r\nIF ERRORLEVEL 1 GOTO NOWIN\r\nIF \"%%1\"==\"SETUP\" GOTO SETUP\r\nIF \"%%1\"==\"setup\" GOTO SETUP\r\n",win[0],win); put(h,line);
    /* Optional shell is authorized by its own verified completion marker. */
    if(!stricmp(src,"C:\\WINXT") && !stricmp(win,"C:\\WINDOWS")) {
        put(h,"IF NOT EXIST C:\\WINXT\\SHREADY.TAG GOTO PLAIN\r\nIF NOT EXIST C:\\WINXT\\TSTART.BAT GOTO PLAIN\r\nIF NOT EXIST C:\\WINDOWS\\TSHELL.EXE GOTO PLAIN\r\nIF NOT EXIST C:\\WINDOWS\\TSINPUT.DLL GOTO PLAIN\r\nIF NOT EXIST C:\\WINDOWS\\TSHELL.INI GOTO PLAIN\r\nIF NOT EXIST C:\\WINXT\\TINST.EXE GOTO SHELLERR\r\nC:\\WINXT\\TINST.EXE /SHELLSAFE C:\\WINDOWS\r\nIF ERRORLEVEL 2 GOTO SHELLERR\r\nIF ERRORLEVEL 1 GOTO PLAIN\r\nC:\\WINXT\\TSTART.BAT\r\nGOTO DONE\r\n:PLAIN\r\n");
    }
    sprintf(line,"%s\\WIN.COM /R\r\nGOTO DONE\r\n:SETUP\r\n",win); put(h,line);
    /* DOS SETUP detects an existing installation from its working directory.
     * sourceinf already makes the OEM disk path absolute. */
    sprintf(line,"%c:\r\nCD %s\r\nIF ERRORLEVEL 1 GOTO NOWIN\r\nECHO Optional Computer: Tandy 1000 EX/HX (WindowsXT). It preserves your current keyboard.\r\nECHO Select Other display, then enter this source path: %s\r\n%s\\SETUP.EXE\r\n",win[0],win,src,win); put(h,line);
    sprintf(line,"ECHO Windows Setup returned to DOS.\r\nECHO If a disk/source prompt appears, use %s each time.\r\n",src); put(h,line);
    if(!stricmp(src,"C:\\WINXT") && !stricmp(win,"C:\\WINDOWS"))
        put(h,"ECHO Next, optionally install the Start bar: C:\\WINXT\\TSSETUP\r\n");
    sprintf(line,"ECHO Start Windows with %s\\WINXT\r\nECHO Keep rollback instructions in %s\\BACKUP.TXT\r\nGOTO DONE\r\n",src,src); put(h,line);
    put(h,":CPFAIL\r\nECHO Computer-choice check refused. Windows and Setup were not started.\r\nECHO Read CPSET.TXT; a changed keyboard may require RESTORE then APPLY.\r\nGOTO DONE\r\n"); put(h,":MODEFAIL\r\nECHO Mode recovery/resource check refused. Keep all XTMODE and XTFILES sidecars.\r\nECHO Windows and Setup were not started.\r\nGOTO DONE\r\n:RECFAIL\r\nECHO Shell recovery failed. Windows and Setup were not started.\r\nGOTO DONE\r\n"); put(h,":SHELLERR\r\nECHO Shell display check failed. Check SYSTEM.INI before starting Windows.\r\nGOTO DONE\r\n:NOHELP\r\nECHO Incomplete helper installation. Windows and Setup were not started.\r\nGOTO DONE\r\n:NOWIN\r\nECHO Windows files or directory unavailable. Nothing started.\r\nGOTO DONE\r\n"); put(h,":FAILED\r\nECHO Video reservation failed. Windows and Setup were not started.\r\nGOTO DONE\r\n:USAGE\r\nECHO Use WINXT or WINXT SETUP from the support folder\r\n:DONE\r\n"); closeout(h);
    join(path,HELP,"MODES.BAT"); h=newtext(path);
    put(h,"@ECHO OFF\r\nIF NOT \"%3\"==\"\" GOTO USAGE\r\n");
    sprintf(line,"IF NOT EXIST %s\\READY.TAG GOTO FAIL\r\nIF NOT EXIST %s\\XTMODE.EXE GOTO FAIL\r\n",src,src); put(h,line);
    sprintf(line,"%s\\XTMODE.EXE INSTALL %s\\SYSTEM.INI %s\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n",src,win,src); put(h,line);
    sprintf(line,"%s\\XTMODE.EXE RECOVER %s\\SYSTEM.INI\r\nIF ERRORLEVEL 1 GOTO FAIL\r\nIF NOT \"%%1\"==\"\" GOTO SELECT\r\n",src,win); put(h,line);
    sprintf(line,"%s\\XTMODE.EXE MENU %s\\SYSTEM.INI\r\nGOTO DONE\r\n:SELECT\r\n%s\\XTMODE.EXE SET %s\\SYSTEM.INI %%1 %%2\r\nGOTO DONE\r\n",src,win,src,win); put(h,line);
    put(h,":FAIL\r\nECHO Mode install/recovery refused. Windows was not started. Keep sidecars.\r\nGOTO DONE\r\n:USAGE\r\nECHO Use MODES, MODES 6404, or MODES TEXT /TEXT after exiting Windows.\r\n:DONE\r\n"); closeout(h);
    join(path,HELP,"BACKUP.TXT"); h=newtext(path); sprintf(line,"Original Windows=%s\r\nBackup=%s\r\nSource=%s\r\nRestore at real DOS: %s\\RESTORE YES\r\n",win,bak,src,bak); put(h,line); closeout(h);
    /* Add the optional choice after completed snapshots and recovery script.
     * APPLY never selects Computer or edits SYSTEM.INI/keyboard binaries. */
    join(path,src,"CPSET.EXE");
    computer_changed=1;
    if(deep_verify?spawnl(P_WAIT,path,path,"APPLY",win,"/VERIFY",NULL):spawnl(P_WAIT,path,path,"APPLY",win,NULL))
        fail("Optional Computer choice refused; Setup was not started.",src);
    /* Original independent wave updater changes only guarded starters/add-on.
     * The installer guard remains PARTIAL until that transaction verifies. */
    join(path,src,"WAVEXT.EXE");
    if(spawnl(P_WAIT,path,path,"APPLY",win,src,NULL))
        fail("Independent wave preparation refused; Setup was not started.",src);
    /* WAVEXT APPLY defaults are owned by the updater; explicit diagnostics use
     * its existing VERIFY command and accept the documented static fallback. */
    if(deep_verify) {int status=spawnl(P_WAIT,path,path,"VERIFY",win,src,NULL);
        if(status<0||status>1)fail("Explicit wave verification refused.",src);}
    /* Atomic final transition: interruption leaves PARTIAL.TAG, never READY.TAG. */
    join(path,HELP,"PARTIAL.TAG"); join(target,HELP,"READY.TAG");
    if(rename(path,target)) fail("Cannot commit ready marker.",target);
}
int main(int argc,char **argv)
{
    char path[PTH],rel[24],out[PTH]; int i, n; DIAG(clock_t phase;) unsigned a; struct diskfree_t disk; unsigned long freebytes;
    char *patterns[]={"*.DRV","*.FON","*.FOT","*.TTF","*.GR2","*.GR3","*.LGO","*.RLE","*.INI"};
    char *required[]={"XTMODE.EXE","CPSET.EXE","CPSET.TXT","WAVEXT.EXE","XTWAVE.DAT","XTCLEAN.COM","OEMSETUP.INF","RESERVE.COM","CGA.GR2","XTSTATIC.LGO","WXTSPL01.RLE","TR53216.DRV","TR56404.DRV","TR51616.DRV","TR53204.DRV","TR56402.DRV","TXTMODE.DRV","XTTSYS.FON","XTCFIX.FON","XTCOEM.FON","XTCSYS.FON","XTEFIX.FON","XTEOEM.FON","XTESYS.FON"};
    char *original[]={"SYSTEM.INI","WIN.INI","WIN.COM"};
    char *boot[]={"CONFIG.SYS","AUTOEXEC.BAT"};
    char *generated[]={"MODES.BAT","WINXT.BAT","BACKUP.TXT","READY.TAG","READY.NEW","PARTIAL.TAG","SHREADY.TAG","OEMBASE.INF","OEMSETUP.NEW"};
    if(argc==2 && !stricmp(argv[1],"/ZERO")) return 0;
    if(argc>=2 && !stricmp(argv[1],"/COMPARE")) {
        if(argc!=4) return 2;
        return comparefiles(argv[2],argv[3]);
    }
    if(argc>=2 && !stricmp(argv[1],"/SHELLSAFE")) {
        if(argc>3 || (argc==3 && strlen(argv[2])>=PTH)) {puts("Use TINST /SHELLSAFE [C:\\WINDOWS]"); return 2;}
        strcpy(win,argc==3?argv[2]:"C:\\WINDOWS"); strupr(win);
        n=strlen(win); if(n>3 && win[n-1]=='\\') win[n-1]=0;
        return shellsafe(win);
    }
    if(argc>1 && !stricmp(argv[argc-1],"/VERIFY")) {deep_verify=1; argc--;}
    puts("WINXT guarded DOS installer (8088)\n");
    puts(deep_verify?"Deep copy verification ON.":"Fast copies: I/O checks ON; deep verification OFF. Use /VERIFY to enable.");
    if(argc>2 || (argc==2 && (!strcmp(argv[1],"/?") || !stricmp(argv[1],"HELP")))) {
        puts("From the flat WINXT source directory: INSTALL [C:\\WINDOWS] [/VERIFY]\nUse real DOS, not a Windows DOS box. Existing helper installs are never replaced."); return 1;
    }
    strcpy(win,"C:\\WINDOWS");
    if(argc==2) {if(strlen(argv[1])>=PTH) fail("Windows path too long.",argv[1]); strcpy(win,argv[1]);}
    strupr(win); n=strlen(win); if(n>3 && win[n-1]=='\\') win[n-1]=0;
    if(!safepath(win)) fail("Use an absolute drive:\\8.3\\directory path without spaces.",win);
    if(!getcwd(src,sizeof(src))) fail("Cannot determine source directory.",""); strupr(src);
    if(!safepath(src)) fail("Source must be a DOS 8.3 directory, normally C:\\WINXT.",src);
    if(strlen(src)>31) fail("Support path too long for nested DOS backup paths (maximum 31).",src);
    if(!stricmp(src,win)) fail("Support source must be separate from the Windows directory.",src);
    for(i=0;i<sizeof(generated)/sizeof(generated[0]);i++) {
        join(path,src,generated[i]);
        if(exists(path)) fail("Existing installation, partial marker, or generated file; refusing overwrite.",path);
    }
    join(bakroot,src,"BACKUP");
    if(exists(bakroot) && (_dos_getfileattr(bakroot,&a) || !(a&_A_SUBDIR)))
        fail("BACKUP exists but is not a directory.",bakroot);
    if(_dos_getfileattr(win,&a) || !(a&_A_SUBDIR)) fail("Windows directory not found.",win);
    if(2*strlen(src)+strlen(win)+42>126)fail("Mode installer command exceeds DOS command-tail limit.",src);
    join(sys,win,"SYSTEM");
    if(_dos_getfileattr(sys,&a) || !(a&_A_SUBDIR)) fail("Windows SYSTEM directory not found.",sys);
    for(i=0;i<sizeof(required)/sizeof(required[0]);i++) {join(path,src,required[i]); if(!regular(path)) fail("Flat source folder is incomplete.",path);}
    join(path,win,"SETUP.EXE"); if(!regular(path)) fail("Windows DOS SETUP.EXE missing.",path);
    { char *side[]={"XTMODE.JRN","XTMODE.NEW","XTMODE.OLD","XTMODE.RST","XTFILES.JRN","XTFILES.NEW","XTFILES.RDY"};
      for(i=0;i<sizeof(side)/sizeof(side[0]);i++){join(path,win,side[i]);if(exists(path))fail("Existing mode history; run XTMODE FORGET before reinstalling.",path);} }
    /* A new integration never adopts an older standalone CPSET journal.
     * CHECK is read-only and precedes all recovery/snapshot/source mutations. */
    {
        char *side[]={"CPINFO.SAV","CPINFO.BAK","CPINFO.NEW","CPINFO.OLD","CPINFO.RST","CPINFO.CUR"};
        for(i=0;i<sizeof(side)/sizeof(side[0]);i++) {
            join(path,sys,side[i]);
            if(exists(path)) fail("Existing Computer-choice transaction. Keep it and follow CPSET.TXT before a new install.",path);
        }
    }
    join(path,src,"CPSET.EXE");
    if(deep_verify?spawnl(P_WAIT,path,path,"CHECK",win,"/VERIFY",NULL):spawnl(P_WAIT,path,path,"CHECK",win,NULL))
        fail("Computer-choice preflight refused; no install snapshot started.",src);
    join(path,src,"SHELLSEL.EXE");
    if(regular(path)) {
        recovery=1; join(out,win,"SYSTEM.INI");
        puts("Checking for an interrupted optional-shell selection before snapshot...");
        if(spawnl(P_WAIT,path,path,"RECOVER",out,NULL)) fail("Optional shell recovery failed; no snapshot started.",path);
    }
    for(i=0;i<3;i++) {join(path,win,original[i]); sprintf(rel,"ROOT\\%s",original[i]); add(path,rel);}
    for(i=0;i<2;i++) {sprintf(path,"C:\\%s",boot[i]); if(exists(path)) {sprintf(rel,"BOOT\\%s",boot[i]); add(path,rel);}}
    scanini("SYSTEM.INI",0); scanini("WIN.INI",1);
    for(i=0;i<sizeof(patterns)/sizeof(patterns[0]);i++) {group(win,"ROOT",patterns[i]); group(sys,"SYSTEM",patterns[i]);}
    for(i=0;i<count;i++) {
        if(strlen(src)+20+strlen(bakroot)+6+strlen(files[i].rel)+1+strlen(files[i].src)>126)
            fail("Paths would exceed the DOS rollback command-line limit.",files[i].src);
    }
    if(_dos_getdiskfree(src[0]-'A'+1,&disk)) fail("Cannot inspect support-drive free space.","");
    freebytes=(unsigned long)disk.avail_clusters*disk.sectors_per_cluster*disk.bytes_per_sector;
    if(freebytes<total+131072UL) fail("Not enough support-drive space for backup and helpers.","Free disk space, then try again. No files were changed.");
    for(n=1;n<=999;n++) {sprintf(path,"%s\\B%03d",bakroot,n); if(!exists(path)) break;}
    if(n>999) fail("All BACKUP\\B001 through BACKUP\\B999 names are occupied.",bakroot);
    {
        int h; char mark[PTH];
        join(mark,src,"PARTIAL.TAG"); h=newtext(mark);
        put(h,"Installation guard. Valid only after rename to READY.TAG.\r\n"); closeout(h);
    }
    if(!exists(bakroot) && mkdir(bakroot)) fail("Cannot create nested BACKUP directory.",bakroot);
    if(mkdir(path)) fail("Cannot create a new rollback directory.",path); strcpy(bak,path);
    join(path,bak,"ROOT"); if(mkdir(path)) fail("Cannot create rollback ROOT.",path);
    join(path,bak,"SYSTEM"); if(mkdir(path)) fail("Cannot create rollback SYSTEM.",path);
    join(path,bak,"BOOT"); if(mkdir(path)) fail("Cannot create rollback BOOT.",path);
    printf("Backing up %d original files to %s ...\n",count,bak);
    DIAG(phase=clock();)
    for(i=0;i<count;i++) {join(out,bak,files[i].rel); copynew(files[i].src,out,files[i].size);}
    DIAG(printf("Backup phase: %lu clock ticks (%lu ticks/sec); copied=%lu; compared=%lu bytes.\n",(unsigned long)(clock()-phase),(unsigned long)CLOCKS_PER_SEC,copy_bytes,compare_bytes);)
    DIAG(printf("Copy I/O ticks=%lu; deep comparison ticks=%lu.\n",(unsigned long)copy_ticks,(unsigned long)compare_ticks);)
    DIAG(phase=clock();)
    sourceinf();
    makefiles();
    DIAG(printf("Helper phase: %lu clock ticks (%lu ticks/sec).\n",(unsigned long)(clock()-phase),(unsigned long)CLOCKS_PER_SEC);)
    printf("Completed backup: %s\nSupport/source: %s\n",bak,src);
    if(recovery) puts("Snapshot follows checked shell recovery. Windows SETUP is next.");
    else puts("Optional Computer choice added; active settings and keyboard are unchanged. Windows SETUP is next.");
    printf("Choose Other display and give source path: %s\n",src);
    printf("After Setup, start Windows with %s\\WINXT\n",src);
    return 0;
}
