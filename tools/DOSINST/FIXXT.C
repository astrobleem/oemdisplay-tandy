/* Tiny own-media Windows XT finisher. C89, DOS 3.3+, 8086 small model.
 * No retained backups/readback by default. One recoverable rename per file.
 * Host prepares/qualifies owned wave bytes. Native Setup owns display install.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <fcntl.h>
#include <io.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <direct.h>
#ifndef HOST_TEST
#include <dos.h>
#else
#include <windows.h>
#endif
#include "SOUNDID.H"
#define PTH 200
#define CAP 14000
static char win[PTH],home[PTH],sys[PTH],savepath[PTH];
static char oldini[CAP+1],newini[CAP+1];
static unsigned char io[2048],other[2048];
static int backup,verify,checking,fresh,last=-1;
static unsigned long total,done;
static const char *names[]={"TSHELL.EXE","TSINPUT.DLL","TSHELL.INI","XTTEST.COM","XTCLEAN.COM","TNDYK3.DRV","WHEEL.DRV","C216N6.DRV","C23216.DRV","XTS6SYS.FON","XTS6FIX.FON","XTCSYS.FON","XTCFIX.FON","XTCOEM.FON","CGA.GR2","SETUP.INF","TABOUT.EXE","MATRIX.EXE","MAZE.EXE","STARFLD.EXE","PINBALL.EXE","XPCHIME.EXE","TCHIME.EXE","TEXIT.EXE","RESERVE.COM","WINXT.BAT","CPSET.EXE","WINBRDG.EXE","SHOOK.COM","SETAUTO.EXE","PANCMP2.DRV","XTPAN.EXE","TP.EXE","HPXY.DRV","XYCTL.EXE","WXTWHL.EXE","SOUND.DRV"};
static unsigned long sizes[]={72323UL,6281UL,999UL,39427UL,1071UL,7640UL,1820UL,54752UL,54768UL,4240UL,4240UL,4592UL,4208UL,4560UL,2104UL,49840UL,6479UL,14669UL,28013UL,17295UL,15487UL,5103UL,5071UL,9215UL,1512UL,332UL,36612UL,28656UL,1249UL,10976UL,55104UL,6415UL,12847UL,56704UL,21160UL,7222UL,SOUND_BYTES};
static int target[]={0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,1,2,2,1};
#define COUNT 37
#define KEEP_XRSYNC 4
static char media[PTH];
static int changed,needs[COUNT],ini_changed,forced=-1;
static const char *inifile="SYSTEM.INI";
static void stop(const char *s,const char *p){printf("\nSTOP: %s\n%s\n",s,p?p:"");exit(2);}
static void path(char *o,const char *d,const char *n){if(strlen(d)+strlen(n)+2>=PTH)stop("Path too long",d);strcpy(o,d);strcat(o,"\\");strcat(o,n);}
static int kind(const char *p){struct stat s;if(stat(p,&s)){if(errno==ENOENT)return 0;stop("Cannot inspect file",p);}return (s.st_mode&S_IFDIR)?2:1;}
static long length(const char *p){struct stat s;if(stat(p,&s)||!(s.st_mode&S_IFREG))stop("Missing regular file",p);return s.st_size;}
static void writable(const char *p){
#ifndef HOST_TEST
 unsigned a;if(!_dos_getfileattr(p,&a)&&(a&(_A_RDONLY|_A_HIDDEN|_A_SYSTEM)))stop("Protected target",p);
#else
 DWORD a=GetFileAttributesA(p);if(a!=INVALID_FILE_ATTRIBUTES&&(a&FILE_ATTRIBUTE_READONLY))stop("Readonly target",p);
#endif
}
static void regular_or_missing(const char *p){if(kind(p)==2)stop("File target is a directory",p);writable(p);}
static void progress(const char *n){int pct=(int)(total?done*100UL/total:0),i;if(pct<last)return;if(pct!=100&&last>=0&&pct<last+5)return;last=pct;printf("\r[");for(i=0;i<20;i++)putchar(i<pct/5?'#':' ');printf("] %3d%% %lu/%lu bytes %-12s",pct,done,total,n);fflush(stdout);}
static void writeall(int h,const unsigned char *b,unsigned n,const char *p){
#ifdef HOST_TEST
 const char *v=getenv("TINYXT_FAIL_WRITE");if(v&&atoi(v)>0&&strstr(p,"SIMPLE.NEW")){unsigned shortn=n>128?128:n;if(write(h,b,shortn)!=(int)shortn)stop("Write failed",p);close(h);stop("Injected short write",p);}
#endif
 if(write(h,b,n)!=(int)n)stop("Write failed (disk full?)",p);
}
static int create(const char *p){int h=open(p,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);if(h<0)stop("Cannot create new file",p);return h;}
static int flush_handle(int h){
#ifndef HOST_TEST
#ifdef _MSC_VER
 /* C6 lacks Watcom's wrapper for this same DOS 3.3 commit service. */
 union REGS r;
 r.h.ah=0x68;r.x.bx=h;intdos(&r,&r);return r.x.cflag!=0;
#else
 return _dos_commit(h);
#endif
#else
 return !FlushFileBuffers((HANDLE)_get_osfhandle(h));
#endif
}
static void closeout(int h,const char *p){if(flush_handle(h)) {close(h);stop("Flush failed",p);}if(close(h))stop("Close failed",p);}
static int equal(const char *a,const char *b){FILE *x,*y;unsigned n,m;int ok=1;x=fopen(a,"rb");y=fopen(b,"rb");if(!x||!y)stop("Cannot compare requested files",a);do{n=(unsigned)fread(io,1,sizeof(io),x);m=(unsigned)fread(other,1,sizeof(other),y);if(n!=m||memcmp(io,other,n))ok=0;}while(n&&m&&ok);if(ferror(x)||ferror(y))ok=0;if(fclose(x)||fclose(y))ok=0;return ok;}
static void copy_new(const char *a,const char *b,int count){FILE *f;int h;unsigned n;unsigned long sum=0,want=(unsigned long)length(a);f=fopen(a,"rb");if(!f)stop("Cannot open input",a);h=create(b);while((n=(unsigned)fread(io,1,sizeof(io),f))!=0){sum+=n;if(sum>want)stop("Source changed length",a);writeall(h,io,n,b);if(count){done+=n;progress(strrchr(a,'\\')+1);}}if(ferror(f)||fclose(f)||sum!=want)stop("Input read/length failed",a);closeout(h,b);if((unsigned long)length(b)!=want)stop("Output length failed",b);if(verify&&!equal(a,b))stop("Requested readback failed",b);}
static int allowed(const char *n){unsigned i;if(!stricmp(n,"SYSTEM.INI")||!stricmp(n,"WIN.INI")||!stricmp(n,"PROFILE.TXT"))return 1;for(i=0;i<COUNT;i++)if(!stricmp(n,names[i]))return 1;return 0;}
/* Temporary OLD is discarded after a checked rename; it is not a rollback archive. */
static void recover(const char *dir){char j[PTH],n[PTH],o[PTH],p[PTH],leaf[20];FILE *f;int had;
 path(j,dir,"SIMPLE.JRN");path(n,dir,"SIMPLE.NEW");path(o,dir,"SIMPLE.OLD");
 if(!kind(j)){if(kind(n)||kind(o))stop("Unowned temporary file",dir);return;}
 f=fopen(j,"rt");if(!f||fscanf(f,"TINYXT1 %19s %d",leaf,&had)!=2||!allowed(leaf)||(had!=0&&had!=1)){if(f)fclose(f);stop("Unknown temporary replacement",dir);}if(fclose(f))stop("Journal close failed",j);
 path(p,dir,leaf);regular_or_missing(p);regular_or_missing(n);regular_or_missing(o);
 if(kind(o)){if(kind(p)){if(remove(o))stop("Cannot finish completed replacement",o);}else if(rename(o,p))stop("Cannot restore interrupted rename",p);}
 else if(had&&!kind(p))stop("Original missing after interrupted rename",p);
 if(kind(n)&&remove(n))stop("Cannot discard incomplete staging",n);if(remove(j))stop("Cannot finish replacement cleanup",j);
}
static void begin(const char *dir,const char *leaf,char *n,char *o,char *j){char p[PTH],b[PTH],line[60];int h;
 recover(dir);path(p,dir,leaf);regular_or_missing(p);path(n,dir,"SIMPLE.NEW");path(o,dir,"SIMPLE.OLD");path(j,dir,"SIMPLE.JRN");
 if(backup&&kind(p)){path(b,savepath,!stricmp(leaf,"SYSTEM.INI")?"SYSTEM.INI":leaf);copy_new(p,b,0);}
 sprintf(line,"TINYXT1 %s %d\r\n",leaf,kind(p)?1:0);h=create(j);writeall(h,(unsigned char *)line,(unsigned)strlen(line),j);closeout(h,j);
}
static void commit(const char *dir,const char *leaf,const char *n,const char *o,const char *j){char p[PTH];path(p,dir,leaf);if(kind(p)&&rename(p,o))stop("Cannot rename original",p);if(rename(n,p))stop("Cannot commit complete new file",p);if(kind(o)&&remove(o))stop("Cannot remove temporary original",o);if(remove(j))stop("Cannot finish journal",j);}
static void replace_file(const char *a,const char *dir,const char *leaf){char n[PTH],o[PTH],j[PTH];begin(dir,leaf,n,o,j);copy_new(a,n,1);commit(dir,leaf,n,o,j);}
static void trim(char *s){char *p=s;size_t n;while(*p==' '||*p=='\t')p++;if(p!=s)memmove(s,p,strlen(p)+1);n=strlen(s);while(n&&isspace((unsigned char)s[n-1]))s[--n]=0;}
static void loadini(void){char p[PTH];FILE *f;unsigned n;path(p,win,inifile);if(length(p)>CAP)stop("SYSTEM.INI exceeds bounded limit",p);f=fopen(p,"rb");if(!f)stop("Cannot read SYSTEM.INI",p);n=(unsigned)fread(oldini,1,CAP,f);if(ferror(f)||fclose(f))stop("INI read failed",p);oldini[n]=0;if(strlen(oldini)!=n)stop("INI contains binary data",p);}
static int inivalue(const char *key,char *out){char line[300],*p=oldini,*e,*eq;unsigned n;int boot=0,sections=0,seen=0;
 out[0]=0;while(*p){e=strchr(p,'\n');n=e?(unsigned)(e-p)+1:(unsigned)strlen(p);if(n>=sizeof(line))stop("INI line too long","");memcpy(line,p,n);line[n]=0;trim(line);if(line[0]=='['){char *q=strchr(line,']');if(!q)stop("Malformed INI section","");*q=0;boot=!stricmp(line+1,"boot");if(boot)sections++;}else if(boot&&(eq=strchr(line,'='))!=NULL){*eq=0;trim(line);if(!stricmp(line,key)){if(++seen>1)stop("Duplicate intended INI setting",key);strcpy(out,eq+1);trim(out);}}p+=n;}
 if(sections!=1)stop("Expected one boot section","");return seen;
}


static int pinned_file(const char *name,unsigned long bytes,
                       unsigned long expected){
 static unsigned long tab[16]={0,0x1db71064UL,0x3b6e20c8UL,
  0x26d930acUL,0x76dc4190UL,0x6b6b51f4UL,0x4db26158UL,
  0x5005713cUL,0xedb88320UL,0xf00f9344UL,0xd6d6a3e8UL,
  0xcb61b38cUL,0x9b64c2b0UL,0x86d3d2d4UL,0xa00ae278UL,
  0xbdbdf21cUL};
 FILE *f;unsigned n,i;unsigned long c=0xffffffffUL,total=0;
 if(kind(name)!=1||(unsigned long)length(name)!=bytes)return 0;
 f=fopen(name,"rb");if(!f)return 0;
 while((n=(unsigned)fread(io,1,sizeof(io),f))!=0){
  total+=n;if(total>bytes){fclose(f);return 0;}
  for(i=0;i<n;i++){
   c^=io[i];c=(c>>4)^tab[(unsigned)c&15];
   c=(c>>4)^tab[(unsigned)c&15];
  }
 }
 if(ferror(f)||fclose(f))return 0;
 return total==bytes&&(c^0xffffffffUL)==expected;
}
static void sound_files(void){
 char p[PTH];
 path(p,win,"SYSTEM.DRV");
 if(kind(p))stop("A root SYSTEM.DRV shadows the supported system",p);
 path(p,sys,"SYSTEM.DRV");
 if(!pinned_file(p,2784UL,0x3ff05fecUL))
  stop("The installed real-mode SYSTEM.DRV is incompatible",p);
 path(p,media,SOUND_FILE);
 if(!pinned_file(p,SOUND_BYTES,SOUND_CRC))
  stop("The canonical SOUND.DRV source is missing or damaged",p);
 path(p,win,SOUND_FILE);
 if(kind(p)&&!pinned_file(p,SOUND_BYTES,SOUND_CRC))
  stop("A different root SOUND.DRV shadows the canonical driver",p);
}
static void sound_selection(void){
 char v[300],*comment;
 if(inivalue("system.drv",v)!=1)
  stop("One generic SYSTEM.DRV selection is required","");
 comment=strchr(v,';');if(comment)*comment=0;trim(v);
 if(stricmp(v,"SYSTEM.DRV"))
  stop("The installed SYSTEM driver is incompatible with SOUND",v);
 if(inivalue("sound.drv",v)!=1)
  stop("One existing boot sound.drv entry is required","");
}

/* Replace only the owned key, remove its duplicates, and add missing entries.
 * All unrelated lines, sections and order survive byte-for-byte. */
static void append_key(unsigned *used,const char *wanted,const char *key){
 unsigned n=(unsigned)strlen(wanted);
 if(*used&&newini[*used-1]!='\r'&&newini[*used-1]!='\n'){
  if(*used+2>CAP)stop("INI too large",key);
  newini[(*used)++]='\r';newini[(*used)++]='\n';
 }
 if(*used+n>CAP)stop("INI too large",key);
 memcpy(newini+*used,wanted,n);*used+=n;
}
static void changeini(const char *section,const char *key,const char *value){
 char line[300],name[300],wanted[300],*p=oldini,*e,*eq,*q;
 unsigned n,used=0;int active=0,found=0,section_seen=0,inserted=0;
 sprintf(wanted,"%s=%s\r\n",key,value);
 while(*p){e=strchr(p,'\n');n=e?(unsigned)(e-p)+1:(unsigned)strlen(p);
  if(n>=sizeof(line))stop("INI line too long",key);
  memcpy(line,p,n);line[n]=0;strcpy(name,line);trim(name);
  if(name[0]=='['){
   if(active&&!inserted){append_key(&used,wanted,key);inserted=1;}
   q=strchr(name,']');if(!q)stop("Bad INI section",section);*q=0;
   active=!stricmp(name+1,section);if(active&&++section_seen>1)stop("Duplicate owned section",section);
  }else if(active&&(eq=strchr(name,'='))!=NULL&&name[0]!=';'){
   *eq=0;trim(name);if(!stricmp(name,key)){found++;
    if(!inserted){strcpy(line,wanted);n=(unsigned)strlen(line);inserted=1;}else n=0;
   }
  }
  if(used+n>CAP)stop("INI too large",key);memcpy(newini+used,line,n);used+=n;p+=e?(unsigned)(e-p)+1:(unsigned)strlen(p);
 }
 if(!inserted){
  if(!section_seen){sprintf(line,"\r\n[%s]\r\n",section);n=(unsigned)strlen(line);if(used+n>CAP)stop("INI too large",key);memcpy(newini+used,line,n);used+=n;}
  append_key(&used,wanted,key);
 }
 newini[used]=0;if(strcmp(oldini,newini)){printf("INI %s [%s] %s\n", inifile,section,key);ini_changed=1;}
 strcpy(oldini,newini);
}
static int current(const char *source,const char *dest){
 unsigned char first[32],last[32],got[32];long len;int a,b;
 const char *leaf;
 if(kind(dest)!=1)return 0;len=length(source);if(length(dest)!=len)return 0;
 leaf=strrchr(source,'\\');leaf=leaf?leaf+1:source;
 if(verify||!stricmp(leaf,"XTCLEAN.COM")||
    !stricmp(leaf,SOUND_FILE)||!stricmp(leaf,"TSHELL.EXE")||
    !stricmp(leaf,"TCHIME.EXE")||!stricmp(leaf,"XPCHIME.EXE")||
    !stricmp(leaf,"TEXIT.EXE")||!stricmp(leaf,"TP.EXE"))
  return equal(source,dest);
 a=open(source,O_RDONLY|O_BINARY);b=open(dest,O_RDONLY|O_BINARY);
 if(a<0||b<0)stop("Cannot sample payload",dest);
 if(len<64){close(a);close(b);return equal(source,dest);}
 if(read(a,first,32)!=32||read(b,got,32)!=32)stop("Payload header read failed",dest);
 if(memcmp(first,got,32)){close(a);close(b);return 0;}
 if(lseek(a,len-32,SEEK_SET)<0||lseek(b,len-32,SEEK_SET)<0||read(a,last,32)!=32||read(b,got,32)!=32)stop("Payload end read failed",dest);
 if(close(a)||close(b))stop("Payload close failed",dest);return !memcmp(last,got,32);
}
static int profile(void){char v[300],p[PTH],*comment;FILE *f;
 /* Installed XRSYNC owns its display, fonts, grabber and panning settings.
    It takes priority over stale PROFILE.TXT and legacy install defaults. */
 inivalue("display.drv",v);
 comment=strchr(v,';');if(comment)*comment=0;trim(v);
 if(!stricmp(v,"XRSYNC.DRV")){
  path(p,sys,"XRSYNC.DRV");
  if(kind(p)!=1)stop("Selected XRSYNC driver is missing",p);
  return KEEP_XRSYNC;
 }
 if(forced>=0)return forced;
 path(p,home,"PROFILE.TXT");
 if(!fresh&&kind(p)==1){f=fopen(p,"rt");if(!f||!fgets(v,sizeof(v),f)||fclose(f))stop("Profile record read failed",p);trim(v);}
 else inivalue("display.drv",v);
 if(!stricmp(v,"C216N6.DRV"))return 0;
 if(!stricmp(v,"C23216.DRV"))return 1;
 if(!stricmp(v,"PANCMP2.DRV"))return 2;
 if(!stricmp(v,"HPXY.DRV"))return 3;
 stop("Choose a packaged display in Setup; repair retains saved profile",v);return 3;
}
static void not_windows(void){
#ifndef HOST_TEST
 union REGS r;r.x.ax=0x1600;int86(0x2f,&r,&r);if(r.h.al&&r.h.al!=0x80)stop("Exit Windows fully to plain DOS","");r.x.ax=0x4680;int86(0x2f,&r,&r);if(!r.x.ax)stop("Exit Windows real mode fully to DOS","");r.x.ax=0x3000;int86(0x21,&r,&r);if(r.h.al<3||(r.h.al==3&&r.h.ah<30))stop("DOS 3.3 or later required","");
#endif
}
static void marker(char *out){sprintf(out,"Windows XT simple R1\r\n%s\r\n%s\r\n",win,home);}
static int ready(void){char p[PTH],want[2*PTH+50],got[2*PTH+50];FILE *f;unsigned n;path(p,home,"SIMPLE.OK");if(kind(p)!=1)return 0;marker(want);f=fopen(p,"rb");if(!f)return 0;n=(unsigned)fread(got,1,sizeof(got)-1,f);if(ferror(f)||fclose(f))return 0;got[n]=0;return !strcmp(want,got);}
static int textmatches(const char *p,const char *text){
 FILE *f;char got[320];unsigned want=(unsigned)strlen(text),n;
 if(kind(p)!=1||length(p)!=(long)want)return 0;f=fopen(p,"rb");if(!f)return 0;
 n=(unsigned)fread(got,1,sizeof(got),f);if(ferror(f)||fclose(f))return 0;
 return n==want&&!memcmp(got,text,want);
}

static int display_payload(const char *name){
 return !stricmp(name,"C216N6.DRV")||!stricmp(name,"C23216.DRV")||
  !stricmp(name,"PANCMP2.DRV")||!stricmp(name,"HPXY.DRV")||
  !stricmp(name,"XYCTL.EXE")||!stricmp(name,"XTPAN.EXE")||
  !stricmp(name,"XTS6SYS.FON")||!stricmp(name,"XTS6FIX.FON")||
  !stricmp(name,"XTCSYS.FON")||!stricmp(name,"XTCFIX.FON")||
  !stricmp(name,"XTCOEM.FON")||!stricmp(name,"CGA.GR2")||
  !stricmp(name,"SETUP.INF");
}
static void checkfiles(int mode){char p[PTH],a[PTH];unsigned i;
 for(i=0;i<COUNT;i++){
  if(mode==KEEP_XRSYNC&&display_payload(names[i])){needs[i]=0;continue;}
  if((!stricmp(names[i],"C216N6.DRV")&&mode!=0)||(!stricmp(names[i],"C23216.DRV")&&mode!=1)||(!stricmp(names[i],"PANCMP2.DRV")&&mode!=2)||(!stricmp(names[i],"XTPAN.EXE")&&mode!=2)||(!stricmp(names[i],"HPXY.DRV")&&mode!=3)||(!stricmp(names[i],"XYCTL.EXE")&&mode!=3)||((!stricmp(names[i],"XTS6SYS.FON")||!stricmp(names[i],"XTS6FIX.FON"))&&mode!=0)||((!stricmp(names[i],"XTCSYS.FON")||!stricmp(names[i],"XTCFIX.FON"))&&mode==0)){needs[i]=0;continue;}
  path(p,media,names[i]);if((unsigned long)length(p)!=sizes[i])stop("Repair source size differs",p);
  path(a,target[i]==2?home:target[i]?sys:win,names[i]);regular_or_missing(a);
  if(i==2&&kind(a)==1){if(length(a)>CAP)stop("Existing shell settings too large",a);needs[i]=0;continue;}
  needs[i]=!current(p,a);if(needs[i])total+=sizes[i];
 }
 path(p,win,"WIN.COM");if(kind(p)!=1)stop("Finish stock Windows Setup first",p);
}
static void space(void){unsigned long freebytes=0,need=total+CAP+65536UL;
#ifndef HOST_TEST
 struct diskfree_t d;if(_dos_getdiskfree((unsigned)(toupper(win[0])-'A'+1),&d))stop("Cannot inspect free space",win);freebytes=(unsigned long)d.avail_clusters*d.sectors_per_cluster*d.bytes_per_sector;
#else
 char drive[4];ULARGE_INTEGER a,b,c;drive[0]=win[0];drive[1]=':';drive[2]='\\';drive[3]=0;if(!GetDiskFreeSpaceExA(drive,&a,&b,&c))stop("Cannot inspect free space",win);freebytes=a.HighPart?0xffffffffUL:a.LowPart;
#endif
 if(freebytes<need)stop("Not enough free space for checked temporary writes",win);
}

static int sectionvalue(const char *section,const char *key,char *out){
 char line[512],*p=oldini,*e,*q,*eq;unsigned n;int active=0,seen=0;
 out[0]=0;
 while(*p){e=strchr(p,'\n');n=e?(unsigned)(e-p)+1:(unsigned)strlen(p);
  if(n>=sizeof(line))stop("INI line too long",key);memcpy(line,p,n);line[n]=0;trim(line);
  if(line[0]=='['){q=strchr(line,']');if(!q)stop("Bad INI section",section);*q=0;active=!stricmp(line+1,section);}
  else if(active&&line[0]!=';'&&(eq=strchr(line,'='))!=NULL){*eq=0;trim(line);if(!stricmp(line,key)){if(++seen>1)stop("Duplicate profile startup key",key);strcpy(out,eq+1);trim(out);}}
  p+=n;
 }return seen;
}
static int owned_startup(const char *token){
 char copy[512],*leaf,*p;size_t n=strlen(token);
 if(n>=sizeof(copy))return 0;memcpy(copy,token,n+1);
 if(copy[0]=='"'){memmove(copy,copy+1,strlen(copy));n=strlen(copy);if(n&&copy[n-1]=='"')copy[n-1]=0;}
 leaf=copy;for(p=copy;*p;p++)if(*p=='\\'||*p=='/')leaf=p+1;
 return !stricmp(leaf,"XTPAN.EXE")||!stricmp(leaf,"XYCTL.EXE")||!stricmp(leaf,"WXTWHL.EXE");
}
static void startup_token(char *out,const char *leaf){
 char raw[PTH];sprintf(raw,"%s\\%s",home,leaf);
 if(strchr(raw,' '))sprintf(out,"\"%s\"",raw);else strcpy(out,raw);
}
static void panini(int mode){
 char p[PTH],n[PTH],o[PTH],j[PTH],run[512],result[512],border[512],token[PTH+4],word[512];
 unsigned i=0,k=0,w;int quoted,comma=0,space=0,h;
 if(mode==KEEP_XRSYNC)return;
 inifile="WIN.INI";ini_changed=0;loadini();sectionvalue("windows","run",run);
 while(run[i]){
  if(run[i]==' '||run[i]=='\t'||run[i]==','){
   if(run[i]==',')comma=1;else if(!comma)space=1;
   i++;continue;
  }
  w=0;quoted=0;
  do{char c=run[i];if(c=='"')quoted=!quoted;if(w+1>=sizeof(word))stop("Startup token too long","");word[w++]=c;i++;}
  while(run[i]&&(quoted||(run[i]!=' '&&run[i]!='\t'&&run[i]!=',')));
  word[w]=0;
  if(!owned_startup(word)){
   if(k){if(k+2>=sizeof(result))stop("Startup run value too long","");result[k++]=comma?',':' ';if(comma)result[k++]=' ';}
   if(k+w>=sizeof(result))stop("Startup run value too long","");memcpy(result+k,word,w);k+=w;
  }
  comma=space=0;
 }
 result[k]=0;
 if(mode==2||mode==3){startup_token(token,mode==2?"XTPAN.EXE":"XYCTL.EXE");if(k){if(k+1>=sizeof(result))stop("Startup run value too long","");result[k++]=' ';}if(k+strlen(token)>=sizeof(result))stop("Startup run value too long","");strcpy(result+k,token);k+=(unsigned)strlen(token);}
 startup_token(token,"WXTWHL.EXE");if(k){if(k+1>=sizeof(result))stop("Startup run value too long","");result[k++]=' ';}if(k+strlen(token)>=sizeof(result))stop("Startup run value too long","");strcpy(result+k,token);k+=(unsigned)strlen(token);
 if(strcmp(run,result))changeini("windows","run",result);
 if(mode==2){sectionvalue("windows","BorderWidth",border);if(strcmp(border,"1"))changeini("windows","BorderWidth","1");}
 if(!ini_changed){inifile="SYSTEM.INI";return;}
 if(checking)stop("Owned panning startup token/BorderWidth needs repair","");
 begin(win,"WIN.INI",n,o,j);h=create(n);writeall(h,(unsigned char*)oldini,(unsigned)strlen(oldini),n);closeout(h,n);commit(win,"WIN.INI",n,o,j);puts("WIN.INI optional panning entries updated; other startup commands preserved.");inifile="SYSTEM.INI";
}
int main(int argc,char **argv){char p[PTH],a[PTH],v[300],n[PTH],o[PTH],j[PTH],m[2*PTH+50];unsigned i;int mode,h,rep;
 setbuf(stdout,NULL);
 if(argc==2&&!stricmp(argv[1],"/FAIL"))return 2;
 if(argc<4||argc>7){puts("FIXXT INSTALL|REPAIR|CHECK C:\\WINDOWS C:\\WINXT [/VERIFY] [/FRESH]");return 2;}
 checking=!stricmp(argv[1],"CHECK");rep=!stricmp(argv[1],"REPAIR");
 if(!checking&&!rep&&stricmp(argv[1],"INSTALL"))return 2;
 if(strlen(argv[2])>=PTH-30||strlen(argv[3])>=PTH-30)stop("Path too long","");strcpy(win,argv[2]);strcpy(home,argv[3]);strupr(win);strupr(home);
 if(strlen(win)>=PTH-30||strlen(home)>=PTH-30||win[1]!=':'||win[2]!='\\'||home[1]!=':'||home[2]!='\\'||!stricmp(win,home))stop("Separate absolute DOS paths required","");
 path(sys,win,"SYSTEM");path(media,home,"FILES");
 if(kind(win)!=2||kind(sys)!=2||kind(media)!=2)stop("Required directories missing",win);
 for(i=4;i<(unsigned)argc;i++){if(!stricmp(argv[i],"/VERIFY"))verify=1;else if(!stricmp(argv[i],"/FRESH"))fresh=1;else if(!stricmp(argv[i],"/160")){forced=0;fresh=1;}else if(!stricmp(argv[i],"/320")){forced=1;fresh=1;}else if(!stricmp(argv[i],"/PAN")){forced=2;fresh=1;}else if(!stricmp(argv[i],"/XR1")){forced=3;fresh=1;}else stop("Unknown option",argv[i]);}
 not_windows();sound_files();
 recover(win);recover(sys);recover(home);loadini();
 sound_selection();mode=profile();checkfiles(mode);
 changeini("boot","sound.drv",SOUND_FILE);
 changeini("boot","shell","TSHELL.EXE");changeini("boot","keyboard.drv","TNDYK3.DRV");
 changeini("boot","mouse.drv","WHEEL.DRV");changeini("keyboard","type","1");
 if(mode!=KEEP_XRSYNC){
 changeini("boot","display.drv",mode==3?"HPXY.DRV":mode==2?"PANCMP2.DRV":mode?"C23216.DRV":"C216N6.DRV");
 changeini("boot","fonts.fon",mode?"XTCSYS.FON":"XTS6SYS.FON");
 changeini("boot","fixedfon.fon",mode?"XTCFIX.FON":"XTS6FIX.FON");
 changeini("boot","oemfonts.fon","XTCOEM.FON");changeini("boot","286grabber","CGA.GR2");
 }
 changeini("boot.description","system.drv","Tandy 1000 EX/HX (WindowsXT)");
 changeini("boot.description","keyboard.typ","PC/XT - Type keyboard (84 keys)");
 changeini("boot.description","mouse.drv","Tandy serial wheel mouse (COM1/IRQ4)");
 if(mode!=KEEP_XRSYNC)changeini("boot.description","display.drv",mode==3?"Tandy EX/HX accepted HPXY 640x200 wide-font mode":mode==2?"Tandy EX/HX optional compact panning 320x400":mode?"Tandy EX/HX 320x200 compact 16 colors":"Tandy EX/HX 160x200 small fonts (accepted narrow160)");
 if(ini_changed)total+=(unsigned long)strlen(oldini);for(i=0;i<COUNT;i++)changed+=needs[i];
 if(checking){if(ini_changed||changed)stop("Owned entries or payloads need FIXXT REPAIR","");panini(mode);puts("Owned entries and cheap payload samples match.");return 0;}
 if(changed||ini_changed){space();puts("Repair/copy only missing or outdated payloads and owned INI keys.");progress("");
  for(i=0;i<COUNT;i++)if(needs[i]){path(p,media,names[i]);replace_file(p,target[i]==2?home:target[i]?sys:win,names[i]);}putchar('\n');
  if(ini_changed){begin(win,"SYSTEM.INI",n,o,j);h=create(n);writeall(h,(unsigned char*)oldini,(unsigned)strlen(oldini),n);closeout(h,n);commit(win,"SYSTEM.INI",n,o,j);done+=(unsigned long)strlen(oldini);progress("SYSTEM.INI");putchar('\n');}
 }else puts("No-op: all owned entries match; no payloads copied or INIs written.");
 path(p,home,"PROFILE.TXT");sprintf(v,"%s\r\n",mode==KEEP_XRSYNC?"XRSYNC.DRV":mode==3?"HPXY.DRV":mode==2?"PANCMP2.DRV":mode==1?"C23216.DRV":"C216N6.DRV");
 if(!textmatches(p,v)){begin(home,"PROFILE.TXT",n,o,j);h=create(n);writeall(h,(unsigned char*)v,(unsigned)strlen(v),n);closeout(h,n);commit(home,"PROFILE.TXT",n,o,j);}
 path(p,home,"SIMPLE.OK");if(!kind(p)){marker(m);h=create(p);writeall(h,(unsigned char*)m,(unsigned)strlen(m),p);closeout(h,p);}
 printf("Complete: %d payloads copied, SYSTEM.INI %s. No WIN.COM/wave rebuild.\n",changed,ini_changed?"updated":"unchanged");panini(mode);return 0;
}
