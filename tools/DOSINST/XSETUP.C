#include "DOSCORE.H"
static char *trim(char *s)
{char *e;while(*s&&isspace((unsigned char)*s))s++;e=s+strlen(s);while(e>s&&isspace((unsigned char)e[-1]))*--e=0;return s;}
static int installed(void)
{
 static char *keys[]={"DISPLAY.DRV","FONTS.FON","FIXEDFON.FON","OEMFONTS.FON","286GRABBER"};
 static char *values[]={"XRSYNC.DRV","XTCSYS.FON","XTCFIX.FON","XTCOEM.FON","CGA.GR2"};
 FILE *f;char path[PTH],system[PTH],line[256],*p,*q;unsigned i,k,bits=0,a;int boot=0;
 join(path,windir,"SYSTEM.INI");f=fopen(path,"rt");if(!f)return 0;
 while(fgets(line,sizeof(line),f)){
  p=trim(line);strupr(p);if(*p=='['){boot=!strcmp(p,"[BOOT]");continue;}if(!boot)continue;
  q=strchr(p,'=');if(!q)continue;*q++=0;p=trim(p);q=trim(q);
  for(i=0;i<5;i++)if(!strcmp(p,keys[i])){if(strcmp(q,values[i])){fclose(f);return 0;}bits|=1U<<i;}
 }
 if(ferror(f)||fclose(f)||bits!=31)return 0;
 for(i=0;i<5;i++){
  k=pinindex(values[i]);join(system,windir,"SYSTEM");join(path,system,values[i]);
  if(!attr(path,&a)){join(path,windir,values[i]);if(!attr(path,&a))return 0;}
  hashfile(path,&pins[k]);
 }
 return 1;
}
static U32 file_size(char *path)
{
 FILE *f;long size;f=fopen(path,"rb");if(!f)stop("Cannot measure file.",path);
 if(fseek(f,0L,SEEK_END)||(size=ftell(f))<0||size>1024L*1024L||fclose(f))stop("File measurement failed.",path);
 return (U32)size;
}
static U32 image_size(char *path)
{
 FILE *f;unsigned char h[6];U32 size;
 f=fopen(path,"rb");if(!f||fread(h,1,6,f)!=6||fclose(f)||h[0]!='M'||h[1]!='Z')stop("Invalid native helper image.",path);
 size=(U32)zw(h+4)*512UL;if(zw(h+2))size-=512UL-zw(h+2);
 if(!size||size>file_size(path))stop("Native helper image is truncated.",path);return size;
}
static int helper_state(char *from,U32 image,U32 *retired)
{
 char to[PTH];FILE *a,*b;unsigned n,m,attrbits;U32 size,total=0;int prefix=1;
 join(to,DEST,"XSETUP.EXE");*retired=0;if(!attr(to,&attrbits))return 0;
 if(attrbits&(_A_SUBDIR|_A_VOLID))stop("Helper destination is not a file.",to);
 size=file_size(to);a=fopen(to,"rb");b=fopen(from,"rb");if(!a||!b)stop("Cannot compare retained helper.",to);
 while((n=fread(io,1,sizeof(io),a))!=0){
  m=total>=image?0:(image-total<n?(unsigned)(image-total):n);
  if(m&&(fread(verifybuf,1,m,b)!=m||memcmp(io,verifybuf,m)))prefix=0;total+=n;
 }
 if(ferror(a)||ferror(b)){fclose(a);fclose(b);stop("Helper comparison read failed.",to);}fclose(a);fclose(b);
 if(total!=size)stop("Helper changed during comparison.",to);
 if(prefix&&size==image)return 1;
 *retired=size;return 2;
}
static void temporary(char *path,char *stem)
{
 unsigned i,a;char name[13];
 for(i=0;i<100;i++){sprintf(name,"%s%05u.NEW",stem,i);join(path,DEST,name);if(!attr(path,&a))return;}
 stop("No free installer temporary name.",DEST);
}
static void verify_prefix(char *to,char *from,U32 size)
{
 FILE *a,*b;unsigned n;U32 left=size;
 if(file_size(to)!=size)stop("Retained helper length differs.",to);
 a=fopen(to,"rb");b=fopen(from,"rb");if(!a||!b)stop("Cannot verify native helper.",to);
 while(left){n=left>sizeof(io)?sizeof(io):(unsigned)left;
  if(fread(io,1,n,a)!=n||fread(verifybuf,1,n,b)!=n||memcmp(io,verifybuf,n)){fclose(a);fclose(b);stop("Native helper readback differs.",to);}left-=n;}
 if(ferror(a)||ferror(b)){fclose(a);fclose(b);stop("Native helper readback error.",to);}fclose(a);fclose(b);
}
static void keep_helper(char *from,U32 size,int state)
{
 char to[PTH],temp[PTH];FILE *f;unsigned n;U32 left=size;
 if(state==1)return;join(to,DEST,"XSETUP.EXE");temporary(temp,"XS");
 f=fopen(from,"rb");if(!f)stop("Cannot retain native helper.",from);createout(temp);
 while(left){n=left>sizeof(io)?sizeof(io):(unsigned)left;if(fread(io,1,n,f)!=n){fclose(f);stop("Native helper source read failed.",from);}putbytes(io,n,temp);left-=n;}
 if(ferror(f)||fclose(f))stop("Native helper source close failed.",from);closeout(temp);verify_prefix(temp,from,size);
 if(state==2&&remove(to))stop("Cannot replace the interrupted helper.",to);
 if(rename(temp,to))stop("Cannot commit native helper.",to);stream_output[0]=0;
}
static unsigned make_launcher(char *text)
{
 sprintf(text,"ECHO OFF\r\nC:\\XR155\\XSETUP.EXE /CHECK %s\r\nIF ERRORLEVEL 1 GOTO END\r\nC:\\XR155\\RESERVE.COM\r\nIF ERRORLEVEL 1 GOTO END\r\n%c:\r\nCD %s\r\nWIN /R\r\n:END\r\n",windir,windir[0],windir+2);
 return strlen(text);
}
static int launcher_state(char *text,unsigned size,U32 *retired)
{
 char path[PTH];FILE *f;unsigned a,n;
 *retired=0;join(path,DEST,"RUNSYNC.BAT");if(!attr(path,&a))return 0;
 if(a&(_A_SUBDIR|_A_VOLID))stop("Launcher destination is not a file.",path);
 f=fopen(path,"rb");if(!f)stop("Cannot inspect existing launcher.",path);n=fread(work,1,sizeof(work),f);
 if(ferror(f)||fclose(f))stop("Cannot read existing launcher.",path);
 if(n==size&&!memcmp(work,text,n))return 1;
 *retired=file_size(path);return 2;
}
static void write_launcher(char *text,unsigned size,int state)
{
 char to[PTH],temp[PTH];if(state==1)return;join(to,DEST,"RUNSYNC.BAT");temporary(temp,"RU");
 createout(temp);putbytes((unsigned char *)text,size,temp);closeout(temp);verifyfile(temp,NULL,(unsigned char *)text,size);
 if(state==2&&remove(to))stop("Cannot replace the previous launcher.",to);
 if(rename(temp,to))stop("Cannot commit launcher.",to);stream_output[0]=0;
}
int main(int argc,char **argv)
{
 char path[PTH],target[PTH],self[PTH],exe[PTH],launch[512],*p;unsigned a,i,drive,launchsize;unsigned char missing[NPINS];U32 retained,oldhelper,oldlauncher;int prepare=0,status,check=0,newdir,helperstate,launchstate;union REGS r;FILE *f;unsigned char mz[6];long image;
 setbuf(stdout,NULL);signal(SIGINT,onbreak);
 puts("XSETUP - DOS-native XRSYNC driver installation (8088 / DOS 3.20+)");
 if(argc==3&&!stricmp(argv[1],"/CHECK")){check=1;argv[1]=argv[2];argc=2;}
 if(argc>1&&!stricmp(argv[argc-1],"/PREP")){prepare=1;argc--;}
 if(argc>2){puts("Usage: XSETUP [C:\\WINDOWS]\nRun from plain DOS. No Python or other computer is required.");return 1;}
 r.h.ah=0x30;intdos(&r,&r);if(r.h.al<3||(r.h.al==3&&r.h.ah<20))stop("DOS 3.20 or later is required.","");
 not_windows();
 if(check){absolute(windir,argv[1]);if(!installed())stop("XRSYNC is not the selected, complete display installation.",windir);return 0;}
 if(!canonical(self,argv[0],PTH)||(p=strrchr(self,'\\'))==NULL)stop("Cannot locate this driver disk.",argv[0]);
 strcpy(exe,self);if(p==self+2)p[1]=0;else *p=0;absolute(runtime,self);join(path,runtime,"PAYLOAD");
 f=fopen(exe,"rb");if(!f||fread(mz,1,6,f)!=6||mz[0]!='M'||mz[1]!='Z')stop("Cannot locate this native helper.",exe);
 image=(long)zw(mz+4)*512L;if(zw(mz+2))image-=512L-zw(mz+2);
 if(!fseek(f,image,SEEK_SET)&&fread(mz,1,4,f)==4&&!memcmp(mz,"PK\003\004",4)){
  strcpy(archive,exe);zip_mode=1;zip_start=image;
 }
 fclose(f);
 if(!zip_mode){
  if(attr(path,&a)){directory(path);strcpy(runtime,path);}
  else{join(archive,runtime,"XRSYNC.ZIP");if(!attr(archive,&a))stop("Use complete XRSYNC.EXE, or keep XSETUP beside PAYLOAD or XRSYNC.ZIP.",exe);zip_mode=1;zip_start=0;}
 }
 absolute(windir,argc==2?argv[1]:"C:\\WINDOWS");join(path,windir,"SYSTEM.INI");if(!attr(path,&a))stop("Windows 3.0 installation not found.",windir);
 join(path,windir,"SETUP.EXE");if(!attr(path,&a))stop("Windows Setup is missing.",path);
 puts("Checking the complete supplied display packet.");
 for(i=0;i<NPINS;i++)if(pins[i].kind==0)public_source(i);
 newdir=!attr(DEST,&a);if(!newdir)directory(DEST);
 for(i=0;i<NPINS;i++){
  join(target,DEST,pins[i].name);missing[i]=!attr(target,&a);if(missing[i])continue;
  if(a&(_A_SUBDIR|_A_VOLID))stop("Payload destination is not a file.",target);
  if(pins[i].kind==0){if(zip_mode)hashfile(target,&pins[i]);else{join(path,runtime,pins[i].name);verifyfile(target,path,NULL,pins[i].size);}}
  else{expand(supportpath(i),(unsigned)pins[i].size);verifyfile(target,NULL,work,pins[i].size);}
 }
 retained=image_size(exe);helperstate=helper_state(exe,retained,&oldhelper);
 launchsize=make_launcher(launch);launchstate=launcher_state(launch,launchsize,&oldlauncher);
 diskspace(missing,helperstate==1?0:retained,launchstate==1?0:launchsize,oldhelper+oldlauncher);
 if(newdir){if(mkdir(DEST))stop("Cannot create C:\\XR155.","");made=1;}
 for(i=0;i<NPINS;i++)if(missing[i])copyone(i);
 /* Keep only the plain MZ checker; its ZIP overlay is not needed at startup. */
 keep_helper(exe,retained,helperstate);write_launcher(launch,launchsize,launchstate);
 made=0;puts("Complete supplied C:\\XR155 driver disk prepared.");
 if(prepare)return 0;
 join(path,DEST,"RESERVE.COM");status=spawnl(P_WAIT,path,path,NULL);if(status!=0&&status!=0x300){printf("RESERVE child status=%d\n",status);stop("Video reservation failed. Windows Setup was not started.",path);}
 _dos_setdrive((unsigned)(windir[0]-'A'+1),&drive);if(chdir(windir+2))stop("Cannot enter Windows directory.",windir);
 join(path,windir,"SETUP.EXE");
 puts("In Setup choose Display / Other / C:\\XR155, select XRSYNC, then Complete Changes.");
 status=spawnl(P_WAIT,path,path,NULL);
 if(status<0||!installed()){printf("Setup child status=%d\n",status);stop("Setup did not select the complete XRSYNC display.",path);}
 puts("Setup returned. Next start: C:\\XR155\\RUNSYNC.BAT");return 0;
}
