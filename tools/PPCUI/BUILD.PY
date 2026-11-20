"""Build the optional PPC512 tester; no OS files or checksum records emitted."""
from pathlib import Path
import importlib.machinery as M
import zipfile
ROOT=Path(__file__).resolve().parents[2]
F=M.SourceFileLoader('ppc_ui_font',str(Path(__file__).with_name('FONT.PY'))).load_module()
def build(out):
    driver=(ROOT/'downloads/PPCUI/CGALIVE.DRV').read_bytes()
    members={}
    with zipfile.ZipFile(ROOT/'downloads/FRESH/CGA.ZIP') as z:
        old=z.read('CGA/CGA100.DRV')
        changes=[(a,b) for a,b in zip(old,driver) if a!=b]
        assert len(old)==len(driver) and changes==[(1,9)], 'Expected exact existing B redraw operand change'
        support={n:z.read('CGA/'+n) for n in ['CG1FIX.FON','CG1OEM.FON','XTSTATIC.LGO','WXTSPL01.RLE','FONTLIC.TXT','LOGOLIC.TXT']}
    for folder,drv,font,data,label in [
        ('B','CGALIVE.DRV','CG1SYS.FON',(ROOT/'tools/SYSFONT/BIN/CG1SYS.FON').read_bytes(),'PPC512 B - five-row revised System'),
        ('BIG','PPC6.DRV','PPCSYS6.FON',F.build(),'PPC512 B - larger six-row System')]:
        base='PPCUI/'+folder+'/'
        members[base+drv]=driver;members[base+font]=data
        for n in ['CG1FIX.FON','CG1OEM.FON','XTSTATIC.LGO','WXTSPL01.RLE']:members[base+n]=support[n]
        inf='''; Optional 160x100 only. 3:CGA.GR2 comes from licensed Windows media.
[data]
Version="3.0"
[disks]
a = .,"PPC512 OPTIONAL UI",OEMSETUP.INF
[display]
ppcui = a:%s,"%s","100,48,40",3:CGA.GR2,a:XTSTATIC.LGO,,,,a:WXTSPL01.RLE
[sysfonts]
a:%s,"PPC512 System","100,48,40"
[fixedfonts]
a:CG1FIX.FON,"CGA100 Fixed","100,48,40"
[oemfonts]
a:CG1OEM.FON,"CGA100 Terminal","100,48,40",1
'''%(drv,label,font)
        members[base+'OEMSETUP.INF']=inf.replace('\n','\r\n').encode('ascii')
    for n in ['FONTLIC.TXT','LOGOLIC.TXT']:members['PPCUI/'+n]=support[n]
    for n in ['README.TXT','NOTICE.TXT']:members['PPCUI/'+n]=Path(__file__).with_name(n).read_bytes()
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(members.items()):
            info=zipfile.ZipInfo(n,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    return members
if __name__=='__main__':
    target=ROOT/'downloads/PPCUI/PPCUI.ZIP';build(target);print(target)
