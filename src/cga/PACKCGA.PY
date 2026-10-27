#!/usr/bin/env python3
"""Prepare/finalize a private expanded CGA packet; no native execution.

Consumers receive SETUP.EXE, README.TXT and CGA/. They never run this tool,
gather support files or edit a manifest. New driver/helper bytes remain a
development packet until separate native acceptance/publication approval.
"""
import argparse
import hashlib
import importlib.machinery
import json
import re
import shutil
import struct
import zipfile
import zlib
from pathlib import Path
import CGAFONT
import CG6FONT
import CGASET
from STAGECGA import MODES, read, write

HERE=Path(__file__).resolve().parent
ASSETS={
 'XTCSYS.FON':('XTCSYS.FON','c45b5d313109fe0b5fa6e665344accd5fa9de4a5ef35c0f416fe8ca1d83c1326'),
 'XTCFIX.FON':('XTCFIX.FON','3c02c48996d3f8bc9d5a1825bfee966ca4da97ed3e8331472dc78cbe2a63a971'),
 'XTCOEM.FON':('XTCOEM.FON','8fc600059c0246a1b43c1af47bef17a34df844b3ae21369ce53b9ecc8ccc3055'),
 'CGAGRAB.GR2':('CGA.GR2','1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067'),
 'XTSTATIC.LGO':('XTSTATIC.LGO','995d71e3626de64c8fe21bc1f037e0dece0853d4f0d09082bf607b2d237b37ef'),
 'WXTSPL01.RLE':('WXTSPL01.RLE','eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c'),
 'LOGOLIC.TXT':('LOGOLIC.TXT','b7b5b82f34c6a21e5f680e983af2dc628b9bd913363a7ffc6087cd1486201c80'),
}
T80_PINS={'T80COUR.FON':'fe1d522d802dcd442d3904d35222fa864a3a52f214fe1f0f1fa60e120ece3ea6'}
COPY=set(T80_PINS)|set(v[1] for v in MODES.values())|set(CGAFONT.FACES)|{'CG6HELV.FON','XTCSYS.FON','XTCFIX.FON','XTCOEM.FON','CGAGRAB.GR2','CGACTL.EXE','PANCTL.EXE','PANKEY.DLL','PANCFG.EXE','XTPAN.EXE'}
HELPERS={'CGACTL.EXE','PANCTL.EXE','PANCFG.EXE','XTPAN.EXE'}
ALL_FILES=COPY|{'XTSTATIC.LGO','WXTSPL01.RLE','LOGOLIC.TXT','OEMSETUP.INF','FONTLIC.TXT','NOTICE.TXT'}


def ROOT_CGA_BASE(repo):
    with zipfile.ZipFile(repo/'tools/UPAN/BASE/CGA.ZIP') as z:
        return {n[4:]:z.read(n) for n in z.namelist() if n.startswith('CGA/')}


def identity(data):
    return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),crc32='%08x'%zlib.crc32(data))


def dos_exe(data,driver=False):
    if len(data)<64 or data[:2]!=b'MZ':raise ValueError('Expected a complete native MZ executable')
    off=struct.unpack_from('<I',data,60)[0]
    sig=data[off:off+4] if off<len(data) else b''
    if sig[:2] in (b'PE',b'LE',b'LX'):raise ValueError('Modern/protected-mode binary refused')
    if driver and sig[:2]!=b'NE':raise ValueError('Win16 driver must have an NE header')
    if not driver and sig[:2]==b'NE':raise ValueError('SETUP must be a native DOS executable')


def read_drivers(builds):
    result={}
    for mode,folder in builds.items():
        record=json.loads((folder/'CGABUILD.JSN').read_bytes())
        name=MODES[mode][1]
        data=(folder/name).read_bytes()
        if (record.get('build'),record.get('mode'),record.get('driver'),record.get('hardware'))!=('PASS',mode,name,'ibm-cga'):
            raise ValueError('Wrong/incomplete CGA driver receipt: '+mode)
        if record.get('sha256')!=hashlib.sha256(data).hexdigest() or record.get('bytes')!=len(data):
            raise ValueError('Changed CGA build: '+name)
        dos_exe(data,driver=True)
        result[name]=data
    if set(result)!={v[1] for v in MODES.values()}:raise ValueError('All four CGA drivers are required')
    return result


def shared_build(folder,names):
    record=json.loads((folder/'BUILD.JSN').read_bytes())
    if record.get('status')!='BUILT_NOT_RUNTIME_QUALIFIED':raise ValueError('Missing unified native helper build')
    files={}
    for name in names:
        data=(folder/name).read_bytes()
        if {k:identity(data)[k] for k in ('bytes','sha256')}!=record['binaries'][name]:
            raise ValueError('Changed unified helper: '+name)
        files[name]=data
    source_map={'CGACTL.C':HERE/'CGACTL.C','PANCTL.C':HERE/'PANCTL.C','PANCFG.C':HERE.parent/'softpan/PANCFG.C'}
    source_map.update({p.name:p for p in (HERE.parent/'panui').iterdir() if p.suffix in ('.C','.H','.ASM','.DEF')})
    for name,pin in record['sources'].items():
        if name in source_map:
            data=source_map[name].read_bytes()
            if {k:identity(data)[k] for k in ('bytes','sha256')}!=pin:raise ValueError('Changed compiled helper source: '+name)
    return files


def read_helper(folder):
    if (folder/'BUILD.JSN').exists():return shared_build(folder,('CGACTL.EXE',))['CGACTL.EXE']
    record=json.loads((folder/'HELPER.JSN').read_bytes())
    data=(folder/'CGACTL.EXE').read_bytes()
    if record.get('build')!='PASS' or record.get('kind')!='CGA_WINDOW_ACCESS_CANDIDATE':
        raise ValueError('Missing native CGACTL build receipt')
    if record.get('sha256')!=hashlib.sha256(data).hexdigest() or record.get('bytes')!=len(data):
        raise ValueError('Changed CGACTL executable')
    if record.get('source_sha256')!=hashlib.sha256((HERE/'CGACTL.C').read_bytes()).hexdigest():
        raise ValueError('CGACTL build/source mismatch')
    shared=record.get('shared_source_sha256',{})
    if set(shared)!={'WDCORE.C','WDCORE.H','WDWIN.C','WDWIN.H','WTPLACE.C','WTPLACE.H'} or record.get('placement_owner')!='shared WDWIN only':
        raise ValueError('Shared WDESK placement ownership/source receipt required')
    if any(not re.fullmatch('[0-9a-f]{64}',sha) for sha in shared.values()):
        raise ValueError('Invalid shared placement source pin')
    dos_exe(data,driver=True)
    return data


def read_owner(folder):
    """The CGAPAN viewport owner and its exact input module."""
    if (folder/'BUILD.JSN').exists():
        files=shared_build(folder,('PANCTL.EXE','PANKEY.DLL'))
        return files['PANCTL.EXE'],files['PANKEY.DLL']
    record=json.loads((folder/'HELPER.JSN').read_bytes())
    data=(folder/'PANCTL.EXE').read_bytes()
    if record.get('build')!='PASS' or record.get('kind')!='CGA_PAN_OWNER_CANDIDATE':
        raise ValueError('Missing native PANCTL build receipt')
    if record.get('sha256')!=hashlib.sha256(data).hexdigest() or record.get('bytes')!=len(data):
        raise ValueError('Changed PANCTL executable')
    if record.get('source_sha256')!=hashlib.sha256((HERE/'PANCTL.C').read_bytes()).hexdigest():
        raise ValueError('PANCTL build/source mismatch')
    dos_exe(data,driver=True)
    key=(folder/'PANKEY.DLL').read_bytes()
    row=record.get('key_dll',{})
    if row.get('sha256')!=hashlib.sha256(key).hexdigest() or row.get('bytes')!=len(key):
        raise ValueError('Changed PANKEY.DLL')
    for name in ('PANKEY.C','PANKEY.DEF','PKENTRY.ASM'):
        if record.get('sources',{}).get(name)!=hashlib.sha256((HERE/name).read_bytes()).hexdigest():
            raise ValueError('PANKEY build/source mismatch: '+name)
    for name in ('PANSET.C','PANSET.H','PANDLG.H','PANDLGC.C'):
        if record.get('sources',{}).get(name)!=hashlib.sha256((HERE.parent/'panui'/name).read_bytes()).hexdigest():
            raise ValueError('PANCTL shared settings source mismatch: '+name)
    dos_exe(key,driver=True)
    return data,key


def payload(repo,support,drivers,fontout,helper,owner,key,config,window):
    result=dict(drivers)
    result['CGACTL.EXE']=helper
    result['PANCTL.EXE']=owner
    result['PANKEY.DLL']=key
    result['PANCFG.EXE']=config
    result['XTPAN.EXE']=window
    CGAFONT.build(fontout)
    for name in CGAFONT.FACES:result[name]=(fontout/name).read_bytes()
    # Retain TEXT80 Courier exactly. CGA's proportional Helv preserves the
    # same original 8-row ink with dialog-appropriate advances.
    t80=importlib.machinery.SourceFileLoader('cga_t80font',str(repo/'src/text80/T80FONT.PY')).load_module()
    origin=(support/'distributions/WINXT/XTTSYS.FON').read_bytes()
    if hashlib.sha256(origin).hexdigest()!=t80.XTTSYS_SHA:raise ValueError('Wrong XT Pixels T80 strike')
    fnt,rid=t80.strike(origin)
    for name,(face,family,module,variable,weight) in t80.FACES.items():
        if name not in T80_PINS:continue
        data=CGAFONT.B.fon(t80.renamed(fnt,face,family,variable,weight),module,rid,
                          'TEXT80 %s 8x8 (XT Pixels strike), 96x48'%face)
        if hashlib.sha256(data).hexdigest()!=T80_PINS[name]:raise ValueError('Changed accepted T80 font derivation: '+name)
        result[name]=data;(fontout/name).write_bytes(data)
    data,metrics=CG6FONT.build(repo,support)
    result['CG6HELV.FON']=data;(fontout/'CG6HELV.FON').write_bytes(data)
    write(fontout/'CG6FONT.JSN',json.dumps(metrics,indent=2)+'\n')
    for target,(source,sha) in ASSETS.items():
        data=(support/'distributions/WINXT'/source).read_bytes()
        if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('Wrong accepted support input: '+source)
        result[target]=data
    result['OEMSETUP.INF']=(HERE/'OEMSETUP.INF').read_bytes()
    result['FONTLIC.TXT']=(repo/'tools/XTFONTS/LICENSE').read_bytes()
    result['NOTICE.TXT']=(HERE/'NOTICE.TXT').read_bytes()
    return result


def emit(repo,out,files,source_commit,fixture=False):
    """Shared serializer, also used on explicitly marked synthetic fixtures."""
    if out.exists():raise ValueError('Choose a fresh prepared directory')
    if not re.fullmatch('[0-9a-f]{40}',source_commit):raise ValueError('Use the full source commit')
    if set(files)!=ALL_FILES:raise ValueError('Incomplete or unexpected CGA packet inventory')
    out.mkdir(parents=True)
    root=out/'packet';folder=root/'CGA';folder.mkdir(parents=True)
    for name,data in sorted(files.items()):
        if not re.fullmatch(r'[A-Z0-9_]{1,8}\.[A-Z0-9]{1,3}',name):raise ValueError('Non-DOS payload name: '+name)
        (folder/name).write_bytes(data)
    pin={name:dict(identity(data),installed=name if name in COPY else '',
                   destination='WINDOWS' if name in HELPERS else 'SYSTEM' if name in COPY else '')
         for name,data in sorted(files.items())}
    token=hashlib.sha256(json.dumps(pin,sort_keys=True).encode()).hexdigest()
    # Current and immediately preceding accepted packets share one checked
    # upgrade/undo implementation, with each sealed inventory kept exact.
    baseline=ROOT_CGA_BASE(repo)
    oldpin={name:dict(identity(data),installed=name if name in COPY else '',
                    destination='WINDOWS' if name in HELPERS else 'SYSTEM' if name in COPY else '')
            for name,data in sorted(baseline.items())}
    oldtoken=hashlib.sha256(json.dumps(oldpin,sort_keys=True).encode()).hexdigest()
    header='#define CGA_MAX_COUNT '+str(max(len(pin),len(oldpin)))+'\n'
    if not set(oldpin)<set(pin) or set(pin)-set(oldpin)!={'PANCFG.EXE','XTPAN.EXE'}:
        raise ValueError('Review the prior-packet upgrade inventory')
    header+='static CGAFILE cga_new_files[]={\n'
    for name,row in pin.items():
        header+=' {"%s","%s",%dUL,0x%sUL},\n'%(name,row['installed'],row['bytes'],row['crc32'])
    header+='};\nstatic CGAFILE cga_old_files['+str(len(oldpin))+'];\n'
    header+='static CGAFILE *cga_files=cga_new_files;\n'
    header+='static unsigned cga_count='+str(len(pin))+';\nstatic int cga_legacy;\n'
    header+='static const char *cga_packet_id="'+token+'";\n'
    header+='#define CGA_COUNT cga_count\n#define CGA_PACKET_ID cga_packet_id\n'
    header+='static void cga_select(int old){unsigned i,j=0;\nif(old){\n'
    header+='for(i=0;i<'+str(len(pin))+';i++)if(i!='+str(list(pin).index('PANCFG.EXE'))+' && i!='+str(list(pin).index('XTPAN.EXE'))+')cga_old_files[j++]=cga_new_files[i];\n'
    for i,(name,row) in enumerate(oldpin.items()):
        if row['installed']!=pin[name]['installed']:raise ValueError('Prior destination changed')
        if row['bytes']!=pin[name]['bytes'] or row['crc32']!=pin[name]['crc32']:
            header+='cga_old_files[%d].size=%dUL;cga_old_files[%d].crc=0x%sUL;\n'%(i,row['bytes'],i,row['crc32'])
    header+='}\ncga_legacy=old;cga_files=old?cga_old_files:cga_new_files;'
    header+='cga_count=old?'+str(len(oldpin))+':'+str(len(pin))+';'
    header+='cga_packet_id=old?"'+oldtoken+'":"'+token+'";}\n'
    sources=CGASET.stage(repo,out/'native-src',header)
    readme=(HERE/'README.TXT').read_bytes()
    (root/'README.TXT').write_bytes(readme)
    rec=dict(kind='CGA_DEVELOPMENT_PACKET',source_commit=source_commit,fixture=fixture,
             native_build='NOT_RUN',windows='NOT_TESTED',hardware='UNQUALIFIED',
             payload=pin,packet_id=token,installer_sources=sources,readme=identity(readme),
             helper_autoload_modes=['100','320','640','PAN'],
             helper_by_mode={'100':'CGACTL.EXE','320':'CGACTL.EXE','640':'CGACTL.EXE','PAN':'PANCTL.EXE'},
             helper_normal_modes='Set disabled text black, then exit; no resident placement owner')
    write(out/'PREPARED.JSN',json.dumps(rec,indent=2)+'\n')
    return rec


def verify(out):
    rec=json.loads((out/'PREPARED.JSN').read_bytes())
    root=out/'packet';files={p.name:p for p in (root/'CGA').iterdir() if p.is_file()}
    paths=list(root.rglob('*'))
    if any(p.is_symlink() for p in paths):raise ValueError('Linked packet content refused')
    expected={'README.TXT'}|{'CGA/'+name for name in ALL_FILES}
    if {p.relative_to(root).as_posix() for p in paths if p.is_file()}!=expected:
        raise ValueError('Expanded packet inventory changed')
    if {p.relative_to(root).as_posix() for p in paths if p.is_dir()}!={'CGA'}:
        raise ValueError('Unexpected packet directory')
    if set(files)!=set(rec['payload']):raise ValueError('Payload inventory changed')
    for name,path in files.items():
        if identity(path.read_bytes())!={k:rec['payload'][name][k] for k in ('bytes','sha256','crc32')}:
            raise ValueError('Payload changed: '+name)
    if {p.name for p in (out/'native-src').iterdir()}!=set(rec['installer_sources']):
        raise ValueError('Native source inventory changed')
    for name,sha in rec['installer_sources'].items():
        if (out/'native-src'/name).is_symlink():raise ValueError('Linked native source refused')
        if hashlib.sha256((out/'native-src'/name).read_bytes()).hexdigest()!=sha:
            raise ValueError('Installer source changed: '+name)
    if identity((root/'README.TXT').read_bytes())!=rec['readme']:raise ValueError('README changed')
    return rec


def finish(prepared,build,out):
    rec=verify(prepared)
    if rec['fixture']:raise ValueError('Synthetic test fixture cannot become a consumer packet')
    receipt=json.loads((build/'SETBUILD.JSN').read_bytes())
    if receipt.get('sources')!=rec['installer_sources'] or receipt.get('build')!='PASS':
        raise ValueError('Installer build/source receipt mismatch')
    data=(build/'SETUP.EXE').read_bytes();dos_exe(data)
    if receipt.get('binary')!=identity(data):raise ValueError('Installer binary changed')
    if out.exists():raise ValueError('Choose a fresh finished output')
    out.mkdir(parents=True);root=out/'expanded'
    shutil.copytree(prepared/'packet',root)
    (root/'SETUP.EXE').write_bytes(data)
    with zipfile.ZipFile(out/'CGADEV.ZIP','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                name=path.relative_to(root).as_posix()
                item=zipfile.ZipInfo(name,date_time=(2026,10,25,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(item,path.read_bytes())
    rec.update(native_build='PASS',installer_binary=identity(data),windows='NOT_TESTED',hardware='UNQUALIFIED')
    write(out/'CGADEV.JSN',json.dumps(rec,indent=2)+'\n')
    return rec


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--repo',type=Path,required=True);p.add_argument('--support',type=Path,required=True)
    p.add_argument('--build-100',type=Path,required=True);p.add_argument('--build-320',type=Path,required=True);p.add_argument('--build-640',type=Path,required=True)
    p.add_argument('--build-pan',type=Path,required=True)
    p.add_argument('--helper-build',type=Path,required=True)
    p.add_argument('--owner-build',type=Path,required=True)
    p.add_argument('--config-build',type=Path,required=True)
    p.add_argument('--source-commit',required=True);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('finish');p.add_argument('--prepared',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.command=='prepare':
        if args.out.exists():raise ValueError('Choose a fresh prepared directory')
        drivers=read_drivers({'160x100x16':args.build_100,'320x200x4':args.build_320,'640x200x2':args.build_640,
                              '160x100x16pan':args.build_pan})
        # Generated font work is private developer output, outside the packet.
        fonts=args.out.parent/(args.out.name+'-fonts')
        if fonts.exists():raise ValueError('Fresh font output required: '+str(fonts))
        owner,key=read_owner(args.owner_build)
        files=payload(args.repo,args.support,drivers,fonts,read_helper(args.helper_build),owner,key,shared_build(args.config_build,('PANCFG.EXE',))['PANCFG.EXE'],shared_build(args.config_build,('XTPAN.EXE',))['XTPAN.EXE'])
        emit(args.repo,args.out,files,args.source_commit)
        print('CGA expanded packet/source prepared; native helper build and Windows qualification remain queued')
    else:
        finish(args.prepared,args.build,args.out)
        print('CGADEV.ZIP assembled from native build receipts; Windows/hardware still NOT_TESTED')


if __name__=='__main__':main()
