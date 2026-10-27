/* The standalone panning installer reuses the checked DOS file transactions. */
#define PAN_UNIVERSAL 1
#define main pan_legacy_main
#include "FIXXT.C"
#undef main
#include "DRVPINS.H"
static void pan_upgrade(void){
 char value[512],source[PTH],target[PTH],n[PTH],o[PTH],j[PTH],*leaf,*comment;unsigned i;
 inifile="SYSTEM.INI";loadini();if(inivalue("display.drv",value)!=1)return;
 comment=strchr(value,';');if(comment)*comment=0;trim(value);leaf=strrchr(value,'\\');leaf=leaf?leaf+1:value;
 for(i=0;i<DRV_COUNT;i++)if(!stricmp(leaf,pan_drivers[i].name))break;
 if(i==DRV_COUNT)return;
 path(source,media,leaf);path(target,sys,leaf);
 if(strchr(value,'\\')&&stricmp(value,target))stop("Selected panning driver is outside Windows SYSTEM",value);
 if(!pinned_file(source,pan_drivers[i].size,pan_drivers[i].crc))stop("Panning driver source damaged",source);
 if(pinned_file(target,pan_drivers[i].size,pan_drivers[i].crc))return;
 if(!pinned_file(target,pan_drivers[i].oldsize,pan_drivers[i].oldcrc))stop("Different panning driver retained",target);
 total=pan_drivers[i].size;done=0;last=-1;space();recover(sys);
 begin(sys,leaf,n,o,j);copy_new(source,n,1);
 if(!pinned_file(n,pan_drivers[i].size,pan_drivers[i].crc))stop("Panning driver staged readback failed",n);
 commit(sys,leaf,n,o,j);puts("Two-axis software desktop installed.");
}
int main(int argc,char **argv){
 char executable[PTH],folder[PTH],*cut,*args[3];int result;
 if(argc>2){puts("Usage: SETUP [C:\\WINDOWS]");return 1;}
 if(!_fullpath(executable,argv[0],PTH))stop("Cannot resolve installer",argv[0]);
 cut=strrchr(executable,'\\');if(!cut)stop("Cannot resolve packet directory",argv[0]);
 if(stricmp(cut+1,"PANINST.EXE") && stricmp(cut+1,"PANINST")){*cut=0;path(folder,executable,"PAN");path(executable,folder,"PANINST.EXE");}
 {char source[PTH],directory[PTH],*slash;unsigned i;
  strcpy(directory,executable);slash=strrchr(directory,'\\');if(!slash)stop("Missing packet directory",directory);*slash=0;
  for(i=0;i<DRV_COUNT;i++){
   path(source,directory,pan_drivers[i].name);
   if(kind(source) && !pinned_file(source,pan_drivers[i].size,pan_drivers[i].crc))stop("Panning driver source damaged",source);
  }
 }
 args[0]=executable;args[1]="PANINIT";args[2]=argc==2?argv[1]:"C:\\WINDOWS";
 result=pan_legacy_main(3,args);if(!result)pan_upgrade();return result;
}
