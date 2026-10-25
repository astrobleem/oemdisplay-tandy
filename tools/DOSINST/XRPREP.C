/* Native port of XR1PACK/PREPARE.PY's closed fresh/update recipe.
 * Windows OS files come from the installed system/media; display support
 * including the supplied CGA grabber is included in the packet.
 * The existing runtime and installation transactions remain responsible
 * for the active Windows installation. This program only stages C: files.
 */
#define FAST_CRC
#define ZIP_INDEX
#define DEST "C:\\WINXT"
#define PINFILE "XR1PINS.H"
#define SZHEADER "XRSTRM.H"
#include "DOSCORE.H"
#include "XRFILES.H"
#include "XRINPUT.H"
#include "VARSET.H"
#include <malloc.h>

static char roots[3][PTH],input[PTH],original[PTH],loader[PTH];
static unsigned root_count;
static char cache_root[PTH];
static unsigned char *setup_bytes,*setup_result,*cnf_bytes;
static unsigned setup_used;
static unsigned char checked_existing[NFILES],replace_existing[NFILES];
struct sink { unsigned char *memory;U32 limit,used,crc;int compare,write,different,checksum;FILE *file; };

static void reject_input(char *message,char *path)
{
 unsigned n=strlen(cache_root);
 if(n&&!strnicmp(path,cache_root,n)&&path[n]=='\\')remove(path);
 stop(message,path);
}

static int emit(unsigned char *p,unsigned n,void *ctx)
{
 struct sink *s=(struct sink *)ctx;unsigned char *other=verifybuf;
 if(s->used+n>s->limit)return 1;
 if(s->checksum)s->crc=crc_add(s->crc,p,n);
 if(s->memory)memcpy(s->memory+(unsigned)s->used,p,n);
 if(s->write)putbytes(p,n,"XR1 output");
 if(s->compare){unsigned got=fread(other,1,n,s->file);if(ferror(s->file))return 1;if(got!=n||memcmp(p,other,n))s->different=1;}
 s->used+=n;return 0;
}
static void read_stream(char *path,U32 want,struct sink *sink)
{
 FILE *f;unsigned char h[14];unsigned n;U32 total=0;char *error;
 f=fopen(path,"rb");if(!f)stop("Cannot read required input.",path);
 n=fread(h,1,14,f);if(fseek(f,0L,SEEK_SET)){fclose(f);stop("Cannot seek input.",path);}
 if(n>=8&&!memcmp(h,"SZDD\210\360\047\063",8)){
  error=szdd_stream(f,want,ring,io,emit,sink);
  if(error){fclose(f);reject_input(error,path);}
 }else{
  while((n=fread(io,1,sizeof(io),f))!=0){total+=n;
   if(total>want||emit(io,n,sink)){fclose(f);stop("Input/output bounds or readback mismatch.",path);}}
  if(total!=want){fclose(f);stop("Required input has a different size.",path);}
 }
 if(ferror(f)||fclose(f))stop("Input read/close failure.",path);
}
static int candidate(char *path,U32 want)
{
 FILE *f;unsigned a,n;unsigned char h[14];long size;
 if(!attr(path,&a)||a&(_A_SUBDIR|_A_VOLID))return 0;
 f=fopen(path,"rb");if(!f)stop("Cannot inspect input.",path);
 n=fread(h,1,14,f);if(fseek(f,0L,SEEK_END)||(size=ftell(f))<0||ferror(f)||fclose(f))stop("Cannot measure input.",path);
 if(n>=8&&!memcmp(h,"SZDD\210\360\047\063",8))return n==14&&h[8]=='A'&&zd(h+10)==want;
 return (U32)size==want;
}
static int locate_input(char *name,U32 size,char *out)
{
 unsigned i,v;char leaf[13],path[PTH];
 for(i=0;i<root_count;i++)for(v=0;v<3;v++){
  strcpy(leaf,name);if(v)leaf[strlen(leaf)-1]=v==1?'_':'$';join(path,roots[i],leaf);
  if(candidate(path,size)){strcpy(out,path);return 1;}
 }
 if(!strcmp(name,"SETUP.INF"))for(i=0;i<root_count;i++){
  join(path,roots[i],"CPINFO.BAK");if(candidate(path,size)){strcpy(out,path);return 1;}
 }
 return 0;
}
static void find_input(char *name,U32 size,char *out)
{ if(!locate_input(name,size,out))stop("Required Windows 3.0 input missing or different. Nothing in Windows was changed.",name); }
static void critical(char *name,unsigned size,char *sha,unsigned char *memory,char *path)
{
 struct sink sink;unsigned i,j,n;FILE *f;
 memset(&sink,0,sizeof(sink));sink.memory=memory;sink.limit=size;
 if(!locate_input(name,size,path)){
  if(!strcmp(name,"SETUP.INF")&&locate_input(name,49095UL,path)){
   sink.limit=49095UL;read_stream(path,49095UL,&sink);
   if((crc_add(0xffffffffUL,memory,49095U)^0xffffffffUL)!=VARIANT_CRC)reject_input("Different installed Windows Setup metadata.",path);
   for(i=j=0;i<NVAR;i++){
    n=variation[i].ch?1:variation[i].end-variation[i].start;
    if(n>49046U-j)stop("Metadata normalization exceeds its bound.",path);
    if(variation[i].ch)setup_result[j]=(unsigned char)variation[i].ch;
    else memcpy(setup_result+j,memory+variation[i].start,n);
    j+=n;
   }
   if(j!=49046U||(crc_add(0xffffffffUL,setup_result,j)^0xffffffffUL)!=SETUP_INPUT_CRC)stop("Installed metadata normalization differs.",path);
   memcpy(memory,setup_result,j);return;
  }
  if(!strcmp(name,"WIN.CNF"))for(i=0;i<root_count;i++){
   join(path,roots[i],"WIN.COM");f=fopen(path,"rb");if(!f)continue;
   if(fread(memory,1,size,f)==size&&!ferror(f)&&(crc_add(0xffffffffUL,memory,size)^0xffffffffUL)==CNF_CRC){fclose(f);return;}
   fclose(f);
  }
  stop("Required Windows 3.0 input missing or different.",name);
 }
 read_stream(path,size,&sink);sha=sha;
 if((crc_add(0xffffffffUL,memory,size)^0xffffffffUL)!=(!strcmp(name,"SETUP.INF")?SETUP_INPUT_CRC:!strcmp(name,"WIN.CNF")?CNF_CRC:CGA_CRC))reject_input("Windows 3.0 input CRC/version differs.",path);
}
static void setup_generate(void)
{
 unsigned i,n;
 setup_used=0;
 for(i=0;i<NOPS;i++){
  if(operations[i].text){n=strlen(operations[i].text);
   if(n>49840U-setup_used)stop("Setup insertion overflow.","");
   memcpy(setup_result+setup_used,operations[i].text,n);
  }else{
   if(operations[i].end<operations[i].start||operations[i].end>49046U)stop("Setup copy range invalid.","");
   n=operations[i].end-operations[i].start;
   if(n>49840U-setup_used)stop("Setup copy overflow.","");
   memcpy(setup_result+setup_used,setup_bytes+operations[i].start,n);
  }
  setup_used+=n;
 }
 if(setup_used!=49840U)stop("Generated Setup length differs.","");
 if((crc_add(0xffffffffUL,setup_result,setup_used)^0xffffffffUL)!=SETUP_OUTPUT_CRC)stop("Generated Setup CRC differs.","");
}
static void payload(unsigned i,struct sink *sink)
{
 struct file_record *r=&files[i];char path[PTH];unsigned left,n,k;
 if(r->kind==0){k=pinindex(r->source);if(zip_mode)zip_feed(k,emit,sink);
  else{join(path,runtime,r->source);read_stream(path,r->size,sink);}}
 else if(r->kind==1){find_input(r->source,r->size,path);sink->checksum=1;sink->crc=0xffffffffUL;read_stream(path,r->size,sink);sink->checksum=0;
  if((sink->crc^0xffffffffUL)!=input_crcs[i])reject_input("Windows OS input CRC/version differs.",path);}
 else if(r->kind==2){left=setup_used;while(left){n=left>4096?4096:left;if(emit(setup_result+setup_used-left,n,sink))stop("Setup output/readback failed.",r->path);left-=n;}}
 else if(r->kind==3){if(emit(cnf_bytes,3456,sink))stop("Loader output/readback failed.",r->path);}
 else if(r->kind==4){
  if(emit(cnf_bytes,3456,sink))stop("Startup loader prefix failed.",r->path);
  k=pinindex("XTLOGO.LGO");if(zip_mode)zip_feed(k,emit,sink);
  else{join(path,runtime,"XTLOGO.LGO");read_stream(path,35971UL,sink);}
 }else stop("Unknown compiled preparation rule.",r->path);
 if(sink->used!=sink->limit)stop("Prepared file length differs.",r->path);
}
static void parents(char *path)
{
 char *p;unsigned a;
 for(p=path+3;*p;p++)if(*p=='\\'){
  *p=0;if(attr(path,&a)){if(!(a&_A_SUBDIR))stop("Output parent is a file.",path);}
  else if(mkdir(path))stop("Cannot create output directory.",path);*p='\\';
 }
}
static int compared(struct sink *sink,char *path)
{
 int different=sink->different,bad=ferror(sink->file);
 if(fgetc(sink->file)!=EOF)different=1;if(ferror(sink->file))bad=1;
 if(fclose(sink->file))bad=1;sink->file=NULL;
 if(bad)stop("Output comparison read failed.",path);return !different;
}
static void stage_name(char *out,char *to)
{
 char dir[PTH],leaf[13],*p;unsigned i,a;strcpy(dir,to);p=strrchr(dir,'\\');
 if(p==dir+2)p[1]=0;else *p=0;
 for(i=0;i<100;i++){sprintf(leaf,"XR%05u.NEW",i);join(out,dir,leaf);if(!attr(out,&a))return;}
 stop("No free native staging temporary name.",dir);
}
static void stage(unsigned i,int check_only)
{
 char to[PTH],output[PTH];unsigned a;struct sink sink;
 if(!check_only&&checked_existing[i])return;
 strcpy(to,"C:\\");strcat(to,files[i].path);
 memset(&sink,0,sizeof(sink));sink.limit=files[i].size;
 if(check_only){
  if(attr(to,&a)){
   if(a&(_A_SUBDIR|_A_VOLID))stop("Output is not a regular file.",to);
   sink.file=fopen(to,"rb");if(!sink.file)stop("Cannot compare existing managed output.",to);sink.compare=1;
   payload(i,&sink);if(compared(&sink,to))checked_existing[i]=1;else replace_existing[i]=1;
  }
  return;
 }
 parents(to);if(replace_existing[i])stage_name(output,to);else strcpy(output,to);
 createout(output);sink.write=1;payload(i,&sink);closeout(output);
 sink.used=0;sink.write=0;sink.compare=1;sink.different=0;sink.file=fopen(output,"rb");if(!sink.file)stop("Cannot verify prepared output.",output);
 payload(i,&sink);if(!compared(&sink,output))stop("Prepared output readback failed.",output);
 if(replace_existing[i]){
  if(remove(to))stop("Cannot replace the named managed output.",to);
  if(rename(output,to))stop("Cannot commit the verified managed output.",to);
 }
 stream_output[0]=0;printf("Prepared %s\n",to);
}
static U32 expected_media(char *leaf)
{
 unsigned i,v;char name[13];
 if(!stricmp(leaf,"SETUP.INF"))return 49046UL;
 if(!stricmp(leaf,"WIN.CNF"))return 3456UL;
 for(i=0;i<NFILES;i++)if(files[i].kind==1)for(v=0;v<3;v++){
  strcpy(name,files[i].source);if(v)name[strlen(name)-1]=v==1?'_':'$';if(!stricmp(leaf,name))return files[i].size;
 }
 return 0;
}
static int cached(char *root,char *name,U32 size)
{
 char path[PTH],leaf[13];unsigned v;
 for(v=0;v<3;v++){strcpy(leaf,name);if(v)leaf[strlen(leaf)-1]=v==1?'_':'$';join(path,root,leaf);if(candidate(path,size))return 1;}return 0;
}
static int media_complete(char *root)
{
 unsigned i;
 if((!cached(root,"SETUP.INF",49046UL)&&!cached(root,"SETUP.INF",49095UL))||!cached(root,"WIN.CNF",3456UL))return 0;
 for(i=0;i<NFILES;i++)if(files[i].kind==1&&!cached(root,files[i].source,files[i].size))return 0;
 return 1;
}
static void collect_media(char *source,char *cache)
{
 struct find_t entry,existing;char pattern[PTH],from[PTH],to[PTH],answer[16],tag[32];unsigned a,i,count,n;FILE *f;U32 total,want;
 /* This cache contains only the user's Windows input, never public output. */
 for(i=0;i<100;i++){
  if(!i)strcpy(cache,"C:\\W30SRC");else sprintf(cache,"C:\\W30SRC%02u",i);
  join(to,cache,"NATIVE.TAG");
  if(!attr(cache,&a)){
   if(mkdir(cache))stop("Cannot create Windows media cache.",cache);
   f=fopen(to,"wb");if(!f||fwrite("XR1 own Windows media\r\n",1,23,f)!=23||fclose(f))stop("Cannot identify Windows media cache.",to);break;
  }
  if(!(a&_A_SUBDIR))continue;
  f=fopen(to,"rb");if(f){n=fread(tag,1,sizeof(tag),f);fclose(f);if(n==23&&!memcmp(tag,"XR1 own Windows media\r\n",23))break;}
 }
 if(i==100)stop("No free Windows media-cache name.","");
 strcpy(cache_root,cache);
 if(media_complete(cache)){puts("Using the complete Windows media cache.");return;}
 for(;;){
  count=0;join(pattern,source,"*.*");
  if(!_dos_findfirst(pattern,_A_NORMAL|_A_RDONLY|_A_HIDDEN|_A_SYSTEM|_A_ARCH,&entry))do{
   if(entry.attrib&(_A_SUBDIR|_A_VOLID)||(want=expected_media(entry.name))==0)continue;
   if(entry.size>1024UL*1024UL)stop("Windows media file exceeds its bound.",entry.name);
   join(from,source,entry.name);join(to,cache,entry.name);
   if(attr(to,&a)){
    if(a&(_A_SUBDIR|_A_VOLID))stop("Cached input is not a regular file.",to);
    if(_dos_findfirst(to,_A_NORMAL|_A_RDONLY|_A_HIDDEN|_A_SYSTEM|_A_ARCH,&existing))stop("Cannot inspect cached input.",to);
    if(existing.size==entry.size&&(candidate(to,want)||(!stricmp(entry.name,"SETUP.INF")&&candidate(to,49095UL))))continue;
    if(remove(to))stop("Cannot replace incomplete cached input.",to);
   }
   f=fopen(from,"rb");if(!f)stop("Cannot read Windows disk.",from);createout(to);total=0;
   while((n=fread(io,1,sizeof(io),f))!=0){total+=n;if(total>entry.size){fclose(f);stop("Windows media changed during copy.",from);}putbytes(io,n,to);}
   if(ferror(f)||fclose(f)||total!=entry.size)stop("Windows media read failed.",from);closeout(to);verifyfile(to,from,NULL,entry.size);stream_output[0]=0;count++;
  }while(!_dos_findnext(&entry));
  printf("Copied %u Windows media files to %s.\n",count,cache);
  if(media_complete(cache)){puts("Complete Windows 3.0 disk set gathered automatically.");return;}
  puts("Insert the next original Windows 3.0 Setup disk, then press Enter. Q cancels.");
  if(!fgets(answer,sizeof(answer),stdin)||toupper(answer[0])=='Q')stop("Windows media gathering cancelled; rerun with the original disks to continue.",cache);
 }
}
int main(int argc,char **argv)
{
 char self[PTH],exe[PTH],path[PTH],*p;unsigned a,i,count=0;int fresh,prepare=0,status,ready_setup=0;struct sink setup_sink;FILE *f;unsigned char h[6];long image;
 union REGS regs;
 setbuf(stdout,NULL);signal(SIGINT,onbreak);puts("PREPXR - DOS-native XR1 fresh/update preparation");
 if(argc>1&&!stricmp(argv[argc-1],"/PREP")){prepare=1;argc--;}
 if(argc!=3||(stricmp(argv[1],"FRESH")&&stricmp(argv[1],"UPDATE"))){
  puts("Usage: PREPXR UPDATE C:\\WINDOWS\n       PREPXR FRESH C:\\WIN30SRC\nRun on the DOS computer itself; no Python or host conversion is required.");return 1;}
 fresh=!stricmp(argv[1],"FRESH");not_windows();
 regs.h.ah=0x30;intdos(&regs,&regs);if(regs.h.al<3||(regs.h.al==3&&regs.h.ah<30))stop("DOS 3.3 or later is required, as for the existing XR1 installer.","");
 if(!canonical(self,argv[0],PTH)||(p=strrchr(self,'\\'))==NULL)stop("Cannot locate this packet.",argv[0]);
 strcpy(exe,self);if(p==self+2)p[1]=0;else *p=0;absolute(runtime,self);join(path,runtime,"PAYLOAD");
 f=fopen(exe,"rb");if(!f||fread(h,1,6,f)!=6||h[0]!='M'||h[1]!='Z')stop("Cannot locate this native helper.",exe);
 image=(long)zw(h+4)*512L;if(zw(h+2))image-=512L-zw(h+2);
 if(!fseek(f,image,SEEK_SET)&&fread(h,1,4,f)==4&&!memcmp(h,"PK\003\004",4)){
  strcpy(archive,exe);zip_mode=1;zip_start=image;
 }
 fclose(f);
 if(!zip_mode){
  if(attr(path,&a)){directory(path);strcpy(runtime,path);}
  else{join(archive,runtime,"WINXT.ZIP");if(!attr(archive,&a))stop("Use complete WINXT.EXE, or keep PREPXR beside its payload or WINXT.ZIP.",exe);zip_mode=1;zip_start=0;}
 }
 absolute(roots[0],argv[2]);
 if(!stricmp(roots[0],"C:\\WINXT")||!strnicmp(roots[0],"C:\\WINXT\\",9)||(fresh&&(!stricmp(roots[0],"C:\\W30")||!strnicmp(roots[0],"C:\\W30\\",7))))stop("Windows input must be separate from the installer output folders.",roots[0]);
 if(fresh&&!media_complete(roots[0])){collect_media(roots[0],path);strcpy(roots[0],path);}root_count=1;join(path,roots[0],"SYSTEM");if(attr(path,&a)){directory(path);strcpy(roots[root_count++],path);}
 setup_bytes=malloc(49095U);setup_result=malloc(49840U);cnf_bytes=malloc(3456U);
 if(!setup_bytes||!setup_result||!cnf_bytes)stop("Not enough conventional memory for preparation.","");
 if(!locate_input("SETUP.INF",49046UL,path)&&!locate_input("SETUP.INF",49095UL,path)&&locate_input("SETUP.INF",49840UL,path)){
  memset(&setup_sink,0,sizeof(setup_sink));setup_sink.memory=setup_result;setup_sink.limit=49840UL;
  read_stream(path,49840UL,&setup_sink);
  if((crc_add(0xffffffffUL,setup_result,49840U)^0xffffffffUL)!=SETUP_OUTPUT_CRC)stop("Installed XR1 Setup metadata differs.",path);
  setup_used=49840U;ready_setup=1;
 }else critical("SETUP.INF",49046U,SETUP_INPUT_SHA,setup_bytes,original);
 critical("WIN.CNF",3456U,CNF_SHA,cnf_bytes,loader);
 if(!ready_setup)setup_generate();
 puts("Checking the supplied runtime and required Windows files before output.");
 for(i=0;i<NPINS;i++)public_source(i);
 for(i=0;i<NFILES;i++)if(fresh||strncmp(files[i].path,"W30\\",4)){
  if(files[i].kind==1)find_input(files[i].source,files[i].size,path);
  stage(i,1);count++;
 }
 if(count!=(fresh?369:82))stop("Compiled preparation inventory differs.","");
 checkcancel();
 /* SETUPXT.BAT is withheld until every private source and readback succeeds. */
 for(i=0;i<NFILES;i++)if(strcmp(files[i].path,"SETUPXT.BAT")&&(fresh||strncmp(files[i].path,"W30\\",4)))stage(i,0);
 for(i=0;i<NFILES;i++)if(!strcmp(files[i].path,"SETUPXT.BAT"))stage(i,0);
 free(setup_bytes);free(setup_result);free(cnf_bytes);
 /* Return the far-heap DOS blocks before child programs reserve video RAM. */
 _fheapshrink();_nheapshrink();
 printf("Complete native XR1 %s preparation: %u verified files.\nNext: C:\\SETUPXT\n",fresh?"fresh":"update",count);
 if(!prepare){
  char *shell=getenv("COMSPEC");if(!shell||!*shell)stop("DOS command interpreter is unavailable.","");
  join(path,DEST,"RESERVE.COM");
  status=spawnl(P_WAIT,path,path,NULL);
  if(status!=0&&status!=0x300)stop("Video reservation failed. The guarded installer was not started.",path);
  puts("Starting the existing guarded Windows XT installer.");
  execl(shell,"COMMAND.COM","/C","C:\\SETUPXT.BAT",NULL);
  stop("Cannot start SETUPXT through the DOS command interpreter.",shell);
 }
 return 0;
}
