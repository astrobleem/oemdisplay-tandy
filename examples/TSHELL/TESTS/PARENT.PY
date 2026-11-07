from pathlib import Path
import subprocess,json,os
import argparse
p=argparse.ArgumentParser();p.add_argument('--cc',type=Path,default=Path('gcc'));p.add_argument('--out',type=Path,required=True);a=p.parse_args()
R=Path(__file__).resolve().parent.parent;O=a.out.resolve();O.mkdir(parents=True,exist_ok=True)
s=(R/'TSHELL.C').read_text()
func=s[s.index('static int browseparentfirst'):s.index('static void browseextent')]
# Compile the exact activation branch, with only its surrounding dialog removed.
activation=s.split('/* Copy only the index. DlgDirSelect sees the original native DOS row. */',1)[1].split('\n }\n return FALSE;',1)[0]
code=r'''
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#define LPSTR char*
#define HWND int
#define LPARAM intptr_t
#define TRUE 1
#define LB_ERR (-1)
#define FILELIST 102
#define NATIVELIST 105
#define SHORTBOX 106
#define LB_GETCOUNT 1
#define LB_GETTEXTLEN 2
#define LB_GETTEXT 3
#define LB_DELETESTRING 4
#define LB_INSERTSTRING 5
#define LB_RESETCONTENT 6
#define LB_ADDSTRING 7
#define LB_GETCURSEL 8
#define LB_SETCURSEL 9
#define IDOK 1
#define lstrcmp strcmp
#define lstrlen strlen
#define lstrcpy strcpy
#define lstrcat strcat
#define browsetext SetDlgItemText
static int browseBusy,failed,failDelete,failInsert,ended;
static char chosen[144],shortbox[144],cwd[144]="C:\\NESTED",activated[144];
typedef struct {int n,selected;char row[12][144];} LIST;
static LIST native,visible;
static int GetDlgItem(int w,int id){return id;}
static intptr_t SendMessage(int id,int msg,int index,intptr_t ptr){LIST *l=id==105?&native:&visible;char *s=(char*)ptr;int n;
 switch(msg){case LB_GETCOUNT:return l->n;case LB_GETTEXTLEN:return strlen(l->row[index]);case LB_GETTEXT:strcpy(s,l->row[index]);return strlen(s);
 case LB_DELETESTRING:if(failDelete)return -1;memmove(l->row[index],l->row[index+1],sizeof(l->row[0])*(l->n-index-1));return --l->n;
 case LB_INSERTSTRING:if(failInsert)return -1;memmove(l->row[index+1],l->row[index],sizeof(l->row[0])*(l->n-index));strcpy(l->row[index],s);l->n++;return index;
 case LB_RESETCONTENT:l->n=0;return 0;case LB_ADDSTRING:n=l->n++;strcpy(l->row[n],s);return n;
 case LB_GETCURSEL:return l->selected;case LB_SETCURSEL:l->selected=index;return index;}return -1;
}
static intptr_t SendDlgItemMessage(int w,int id,int msg,int n,intptr_t p){return SendMessage(id,msg,n,p);}
static int SetDlgItemText(int w,int id,char*s){strcpy(shortbox,s);return 1;}
static int DlgDirSelect(int w,char *item,int id){char *s=native.row[native.selected];int n=strlen(s);if(s[0]=='['){memcpy(item,s+1,n-2);item[n-2]=0;return 1;}strcpy(item,s);return 0;}
static int listfiles(int w,char*s){strcpy(activated,s);return 1;}
static int SetFocus(int w){return 1;}static char *getcwd(char*s,int n){strcpy(s,cwd);return s;}static int EndDialog(int w,int n){ended=n;return 1;}
'''+func+r'''
static int activate(int w){int i,n;char item[144],cwd[144];i=visible.selected;
'''+activation+r'''
 return 1;}
static void ck(char*s,int ok){printf("CHECK %s=%d\n",s,ok!=0);if(!ok)failed++;}
static void seed(char **rows,int n){int i;memset(&native,0,sizeof(native));memset(&visible,0,sizeof(visible));for(i=0;i<n;i++)strcpy(native.row[i],rows[i]);native.n=n;chosen[0]=activated[0]=0;ended=0;}
int main(void){char *rows[]={"Z.EXE","[folder]","A.EXE","[..]","[-c-]"};char *root[]={"A.EXE","[folder]","[-c-]"};
 seed(rows,5);ck("parent_first",browseparentfirst(1)&&!strcmp(native.row[0],"[..]"));
 ck("other_rows_keep_sort_order",!strcmp(native.row[1],"Z.EXE")&&!strcmp(native.row[2],"[folder]")&&!strcmp(native.row[3],"A.EXE")&&!strcmp(native.row[4],"[-c-]"));
 ck("alias_copy",browsealiases(1)&&visible.n==native.n);visible.selected=0;browseselect(1);activate(1);ck("parent_activation",!strcmp(activated,"..")&&!strcmp(shortbox,"[..]"));
 strcpy(visible.row[2],"[Friendly Folder Name]");visible.selected=2;browseselect(1);activate(1);ck("friendly_folder_maps_to_short_path",!strcmp(activated,"folder")&&!strcmp(shortbox,"[folder]"));
 strcpy(visible.row[3],"Friendly Program Name.exe");visible.selected=3;browseselect(1);activate(1);ck("friendly_file_maps_to_short_path",!strcmp(chosen,"C:\\NESTED\\A.EXE")&&ended==IDOK);
 ck("parent_reorder_idempotent",browseparentfirst(1)&&!strcmp(native.row[0],"[..]"));
 seed(root,3);ck("root_unchanged",browseparentfirst(1)&&native.n==3&&!strcmp(native.row[0],"A.EXE"));
 seed(rows,5);failDelete=1;ck("delete_failure_refused",!browseparentfirst(1));failDelete=0;failInsert=1;ck("insert_failure_refused",!browseparentfirst(1));
 printf("FINAL failures=%d\n",failed);return failed?1:0;
}
'''
(O/'HOSTPAR.C').write_bytes(code.replace('\n','\r\n').encode('ascii'))
gcc=a.cc;env=dict(os.environ,PATH=str(gcc.parent)+os.pathsep+os.environ['PATH'])
subprocess.run([str(gcc),'-std=c89','-Wall','-Wno-unused-function','-x','c',str(O/'HOSTPAR.C'),'-o',str(O/'HOSTPAR.EXE')],env=env,check=True)
r=subprocess.run([str(O/'HOSTPAR.EXE')],capture_output=True,text=True,env=env);print(r.stdout);(O/'HOSTPAR.LOG').write_text(r.stdout+r.stderr);r.check_returncode()
