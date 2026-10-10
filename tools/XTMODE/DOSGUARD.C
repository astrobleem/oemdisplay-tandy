/* Original MIT test-only DOS app launched by WINGUARD under real Windows.
 * MSC6 /AS /G0; never a runtime payload. Writes only C:\DOS*.LOG/OK.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
static unsigned query(unsigned ax)
{ union REGS r;memset(&r,0,sizeof(r));r.x.ax=ax;int86(0x2f,&r,&r);return r.x.ax; }
int main(int argc,char **argv)
{
 static const char *commands[]={"CHECK","INSTALL","SET","RECOVER","UNDO","GUARD","VERIFY","FORGET","ACCEPT","MENU"};
 FILE *log,*f;char output[1024];const char *args[6];unsigned a,b,i,n;int fd,rc,refused,stdoutfd,stderrfd;
 log=fopen("C:\\DOSGUARD.LOG","wb");if(!log)return 2;
 a=query(0x1600);b=query(0x4680);
 fprintf(log,"DOS context argc=%d tag=%s AX1600=%04x AX4680=%04x\r\n",argc,argc==2?argv[1]:"MISSING",a,b);fflush(log);
 if(argc!=2||strcmp(argv[1],"WINDOWS")){fclose(log);return 3;}
 stdoutfd=dup(1);stderrfd=dup(2);if(stdoutfd<0||stderrfd<0){fclose(log);return 4;}
 for(i=0;i<10;++i){
  fd=open("C:\\DOSOUT.LOG",O_WRONLY|O_CREAT|O_TRUNC|O_BINARY,S_IREAD|S_IWRITE);
  if(fd<0||dup2(fd,1)<0||dup2(fd,2)<0){fclose(log);return 4;}if(fd>2)close(fd);
  args[0]="C:\\WINXT\\XTMODE.EXE";args[1]=commands[i];args[2]="C:\\WINDOWS\\SYSTEM.INI";args[3]=NULL;args[4]=NULL;args[5]=NULL;
  if(i==1)args[3]="C:\\WINXT";if(i==2)args[3]="32016";
  rc=spawnv(P_WAIT,args[0],args);dup2(stdoutfd,1);dup2(stderrfd,2);
  f=fopen("C:\\DOSOUT.LOG","rb");if(!f){fclose(log);return 5;}n=(unsigned)fread(output,1,sizeof(output)-1,f);output[n]=0;fclose(f);
  refused=rc==1&&strstr(output,"Exit Windows completely")!=NULL;
  fprintf(log,"COMMAND=%s EXIT=%d ACTIVE_WINDOWS_REFUSAL=%d\r\n",commands[i],rc,refused);
  fwrite(output,1,n,log);fflush(log);
  /* CHECK is read-only: abort here if it did not prove the actual guard. */
  if(!refused){fprintf(log,"STOP: guard not proved; no further command attempted\r\n");fclose(log);return 6;}
 }
 close(stdoutfd);close(stderrfd);fprintf(log,"DONE=1\r\n");if(fclose(log))return 7;
 f=fopen("C:\\DOSDONE.OK","wb");if(!f)return 8;fputs("TEN REFUSED\r\n",f);return fclose(f)?9:0;
}
