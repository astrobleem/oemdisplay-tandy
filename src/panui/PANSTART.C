#include <string.h>
#include <ctype.h>
#include "PANSTART.H"
static int Same(const char *p,unsigned n,const char *name)
{
 unsigned i;
 if(strlen(name)!=n)return 0;
 for(i=0;i<n;i++)if(toupper((unsigned char)p[i])!=name[i])return 0;
 return 1;
}
static int Owned(const char *p,unsigned n)
{
 unsigned i,k=0;
 if(n>1&&p[0]=='"'&&p[n-1]=='"'){p++;n-=2;}
 for(i=0;i<n;i++)if(p[i]=='\\'||p[i]=='/')k=i+1;
 p+=k;n-=k;
 return Same(p,n,"XTPAN.EXE")||Same(p,n,"XYCTL.EXE")||Same(p,n,"PANCTL.EXE")||
  Same(p,n,"CGACTL.EXE")||Same(p,n,"PANCFG.EXE");
}
int PanStartupEdit(const char *old,const char *add,char *out,unsigned cap)
{
 unsigned i=0,k=0,start,sep,n;int quoted;
 if(!old||!out||!cap)return 0;
 while(old[i]){
  sep=i;while(old[i]==' '||old[i]=='\t'||old[i]==',')i++;
  if(!old[i])break;
  start=i;quoted=0;
  do{if(old[i]=='"')quoted=!quoted;i++;}
  while(old[i]&&(quoted||(old[i]!=' '&&old[i]!='\t'&&old[i]!=',')));
  if(quoted)return 0;
  n=i-start;
  if(!Owned(old+start,n)){
   if(k){unsigned d=start-sep;if(k+d>=cap)return 0;memcpy(out+k,old+sep,d);k+=d;}
   if(k+n>=cap)return 0;
   memcpy(out+k,old+start,n);k+=n;
  }
 }
 if(add&&*add){
  n=(unsigned)strlen(add);if(k+n+(k?1:0)>=cap)return 0;
  if(k)out[k++]=' ';
  memcpy(out+k,add,n);k+=n;
 }
 out[k]=0;return 1;
}
