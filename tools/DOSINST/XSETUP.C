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
static void keep_helper(char *from)
{
 char to[PTH];FILE *f;unsigned n,a;U32 size=0;
 join(to,DEST,"XSETUP.EXE");if(!stricmp(from,to))return;
 f=fopen(from,"rb");if(!f)stop("Cannot keep the native launcher checker.",from);
 if(fseek(f,0L,SEEK_END)||(size=(U32)ftell(f))>1024UL*1024UL||fseek(f,0L,SEEK_SET)){fclose(f);stop("Cannot measure native helper.",from);}
 if(attr(to,&a)){fclose(f);verifyfile(to,from,NULL,size);return;}
 createout(to);while((n=fread(io,1,sizeof(io),f))!=0)putbytes(io,n,to);
 if(ferror(f)||fclose(f))stop("Cannot copy the native helper.",to);closeout(to);verifyfile(to,from,NULL,size);
}
int main(int argc,char **argv)
{
 char path[PTH],target[PTH],self[PTH],exe[PTH],*p;unsigned a,i,drive;int prepare=0,status,check=0;union REGS r;FILE *f;unsigned char mz[6];long image;
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
 if(attr(path,&a)){directory(path);strcpy(runtime,path);}
 else{
  join(archive,runtime,"XRSYNC.ZIP");
  if(attr(archive,&a)){zip_mode=1;zip_start=0;}
  else{
   f=fopen(exe,"rb");if(!f||fread(mz,1,6,f)!=6||mz[0]!='M'||mz[1]!='Z')stop("Cannot locate this driver packet.",exe);
   image=(long)zw(mz+4)*512L;if(zw(mz+2))image-=512L-zw(mz+2);
   if(fseek(f,image,SEEK_SET)||fread(mz,1,4,f)!=4||memcmp(mz,"PK\003\004",4)){fclose(f);stop("Keep XSETUP beside PAYLOAD or XRSYNC.ZIP, or use the complete XRSYNC.EXE download.",exe);}
   fclose(f);strcpy(archive,exe);zip_mode=1;zip_start=image;
  }
 }
 absolute(windir,argc==2?argv[1]:"C:\\WINDOWS");join(path,windir,"SYSTEM.INI");if(!attr(path,&a))stop("Windows 3.0 installation not found.",windir);
 adddir(windir);join(path,windir,"SYSTEM");if(attr(path,&a)){directory(path);adddir(path);}
 puts("Finding the installed Windows CGA support file and checking this disk.");
 for(i=0;i<NPINS;i++)if(pins[i].kind==1)find_support(i);
 for(i=0;i<NPINS;i++)if(pins[i].kind==0)public_source(i);
 if(attr(DEST,&a)){
  directory(DEST);
  /* Reuse only an already identical driver disk. Never overwrite different files. */
  for(i=0;i<NPINS;i++){
   join(target,DEST,pins[i].name);
   if(pins[i].kind==0){if(zip_mode){hashfile(target,&pins[i]);}else{join(path,runtime,pins[i].name);verifyfile(target,path,NULL,pins[i].size);}}
   else {expand(supportpath(i),(unsigned)pins[i].size);verifyfile(target,NULL,work,pins[i].size);}
  }
 }else{
  diskspace();if(mkdir(DEST))stop("Cannot create C:\\XR155.","");made=1;
  for(i=0;i<NPINS;i++)copyone(i);
 }
 /* Only this newly staged kit is changed. Windows settings belong to Setup. */
 keep_helper(exe);
 join(path,DEST,"RUNSYNC.BAT");f=fopen(path,"wt");if(!f)stop("Cannot create the driver launcher.",path);
 fprintf(f,"@ECHO OFF\nC:\\XR155\\XSETUP.EXE /CHECK %s\nIF ERRORLEVEL 1 GOTO END\nC:\\XR155\\RESERVE.COM\nIF ERRORLEVEL 1 GOTO END\n%c:\nCD %s\nWIN /R\n:END\n",windir,windir[0],windir+2);
 if(ferror(f)||fclose(f))stop("Cannot finish the driver launcher.",path);
 made=0;puts("Complete C:\\XR155 driver disk prepared from your installed Windows.");
 if(prepare)return 0;
 join(path,DEST,"RESERVE.COM");status=spawnl(P_WAIT,path,path,NULL);if(status!=0&&status!=0x300){printf("RESERVE child status=%d\n",status);stop("Video reservation failed. Windows Setup was not started.",path);}
 _dos_setdrive((unsigned)(windir[0]-'A'+1),&drive);if(chdir(windir+2))stop("Cannot enter Windows directory.",windir);
 join(path,windir,"SETUP.EXE");
 puts("In Setup choose Display / Other / C:\\XR155, select XRSYNC, then Complete Changes.");
 status=spawnl(P_WAIT,path,path,NULL);
 if(status<0||!installed()){printf("Setup child status=%d\n",status);stop("Setup did not select the complete XRSYNC display.",path);}
 puts("Setup returned. Next start: C:\\XR155\\RUNSYNC.BAT");return 0;
}
