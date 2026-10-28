"""Accept only the reviewed fresh CGA packet and completed native installation.

The existing compact/PAN gates still verify their own immutable packet. This
gate never qualifies a new launcher from those older installed-driver tests.
"""
from pathlib import Path
import argparse,configparser,hashlib,importlib.machinery,io,json,re,sys,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def require(ok,message):
    if not ok:raise ValueError(message)
def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def exact(row):
    name=row['path']
    require(isinstance(name,str) and name and '\\' not in name and ':' not in name and not name.startswith('/'),
            'Unsafe fresh evidence path')
    p=Path(name);require(not p.anchor and '..' not in p.parts,'Unsafe fresh evidence path')
    target=(ROOT/p).resolve(strict=True)
    require(target.is_relative_to(ROOT.resolve(strict=True)),'Fresh evidence escapes repository')
    require(not any((ROOT/Path(*p.parts[:i])).is_symlink() for i in range(1,len(p.parts)+1)),
            'Linked fresh evidence refused')
    b=target.read_bytes();require(identity(b)==row['identity'],'Changed fresh evidence: '+p.as_posix());return b
def members(b):
    with zipfile.ZipFile(io.BytesIO(b))as z:
        names=z.namelist();require(len(names)==len(set(names)) and z.testzip() is None,'Invalid fresh archive')
        require(all(not n.startswith('/') and '..' not in n.split('/') for n in names),'Unsafe fresh member')
        return {n:z.read(n)for n in names}

def validate(q,data=None):
    require(q.get('status') in ('NATIVE_COMPLETE_PENDING_REVIEW','REVIEWED_FRESH_CGA_COMPLETE_INSTALL'),'Fresh completion acceptance pending')
    require(q.get('physical_hardware') is False,'Physical qualification remains separate')
    required={'src/cga/FRESH.C','src/cga/FRESH.INF','src/cga/FRESH.TXT','src/cga/FRESHLIC.TXT',
              'src/cga/FRESHPK.PY','src/cga/FRESHT.PY','tools/CGAFRESH/VERIFY.PY',
              'tools/CGAFRESH/TESTGATE.PY','tools/CURRENT/BUNDLE.PY','tools/CURRENT/CHECK.PY',
              'tools/CURRENT/PRODUCTS.JSN','docs/CGA.MD','docs/CGA-FRESH.MD'}
    require(required<=set(q.get('sources',{})),'Fresh source binding incomplete')
    for n,pin in q['sources'].items():exact(dict(path=n,identity=pin))
    raw=exact(q['packet']);require(data is None or raw==data,'Different accepted fresh packet')
    files=members(raw);require({n:identity(b)for n,b in files.items()}==q['members'],'Fresh member inventory differs')
    sys.path.insert(0,str(ROOT/'src/cga'))
    p=importlib.machinery.SourceFileLoader('qualified_fresh_producer',str(ROOT/'src/cga/FRESHPK.PY')).load_module()
    original,fresh=p.inputs(ROOT);expected=dict(original)
    expected['CGAOLD.TXT']=expected.pop('README.TXT');expected['README.TXT']=p.crlf((ROOT/'src/cga/FRESH.TXT').read_bytes())
    expected.update({'FRESH.EXE':files.get('FRESH.EXE',b''),'FRESH.TXT':expected['README.TXT'],
                     'FRESHLIC.TXT':p.crlf((ROOT/'src/cga/FRESHLIC.TXT').read_bytes()),
                     'OWATCOM.TXT':(ROOT/'tools/XR1PACK/OWATCOM.TXT').read_bytes()})
    expected.update({'FRESH640/'+n:b for n,b in fresh.items()})
    require(files==expected,'Fresh packet changed accepted CGA runtime/support or adds unexpected members')
    p.dos_exe(files['FRESH.EXE'])
    require(all(re.fullmatch(r'[A-Z0-9_]{1,8}\.[A-Z0-9]{1,3}',part) if '.' in part else
                re.fullmatch(r'[A-Z0-9_]{1,8}',part) for n in files for part in n.split('/')),'Fresh DOS names invalid')
    build=json.loads(exact(q['build']));src=p.sources(ROOT)
    require(build.get('sources')=={n:identity(b)for n,b in src.items()} and
            build.get('binary')==identity(files['FRESH.EXE']),'Fresh native build/source binding differs')
    host=json.loads(exact(q['host']))
    require(host.get('standalone_source_rebuild_identical') and host.get('launcher')==identity(files['FRESH.EXE']) and
            host.get('consumer_packet')==q['packet']['identity'] and host.get('source_packet')==q['source_packet']['identity'] and
            all(host.get(n) for n in ('closed_fresh_inventory','changed_base_refused','changed_launcher_refused',
            'fresh_instructions_are_root_readme','PE_refused','NE_refused','LE_refused','LX_refused')),
            'Fresh host corruption/source-rebuild checks incomplete')
    source=members(exact(q['source_packet']))
    expected_source={'src/cga/'+n:(ROOT/'src/cga'/n).read_bytes() for n in
                     ('FRESH.C','FRESH.INF','FRESH.TXT','FRESHLIC.TXT','FRESHPK.PY','FRESHT.PY')}
    expected_source.update({n:(ROOT/n).read_bytes() for n in
                          (p.BASE,'tools/DOSINST/CRCFAST.H','tools/XR1PACK/OWATCOM.TXT')})
    require(source==expected_source,'Fresh source archive closed inventory/content differs')
    entry=json.loads(exact(q['native_entry']));full=json.loads(exact(q['native_completion']))
    require(entry.get('status')=='PASS_FRESH_ORIGINAL_MEDIA_GRAPHICAL_SETUP_ENTRY' and
            entry.get('windows_absent_at_start') and entry.get('post_install_driver_replacement') is False,
            'Original-media fresh entry evidence missing')
    require(entry.get('launcher')==identity(files['FRESH.EXE'])['sha256'],'Fresh native-tested launcher differs')
    require(full.get('status')=='PASS_ORIGINAL_SETUP_COMPLETION_AND_FIRST_START' and
            full.get('continued_from_entry')==q['native_entry']['identity'] and
            full.get('complete_os_installation') and full.get('first_ordinary_win_r_start') and
            full.get('normal_dos_return') and full.get('original_media_unchanged') and
            full.get('driver_replaced_after_setup') is False,'Fresh completion/first-start proof missing')
    require(full.get('installed')==entry['installed'] and full.get('boot_settings')==entry['generated_setup_boot']|{'shell':'PROGMAN.EXE'},
            'Completed fresh display/support selection differs')
    require(full.get('owned_stopped') and full.get('lease_released') and full.get('inventory_after')==0 and
            full.get('byte_lock_available_after') and not full.get('queued_runner'),'Fresh emulator cleanup incomplete')
    proof_names={'COMPLETE.PNG','FIRSTWIN.PNG','DOSBACK.PNG','FULLRUN.JSN','FULLPREP.JSN',
                 'COMPLETE.CNF','RUNFULL.PY','PREPFULL.PY','SETUPRET.TXT','FIRSTRUN.TXT'}
    require(set(full.get('evidence',{}))==proof_names,'Fresh completion evidence inventory differs')
    proof={n:exact(dict(path=(Path(q['native_completion']['path']).parent/n).as_posix(),identity=pin))
           for n,pin in full['evidence'].items()}
    run=json.loads(proof['FULLRUN.JSN'])
    require(run.get('complete') and run.get('owned_stopped') and run.get('lease_released') and
            run.get('inventory_after')=='0' and run.get('owned_pid')==full['owned_pid'] and 'error' not in run,
            'Raw native completion/cleanup receipt differs')
    require(all(proof[n].decode('ascii').replace('\r','').strip()=='RETURNED'
                for n in ('SETUPRET.TXT','FIRSTRUN.TXT')),'Native DOS return markers differ')
    require(set(q.get('captures',{}))=={'complete','first_start','dos_return'},'Fresh completion captures missing')
    for row in q['captures'].values():exact(row)
    config=configparser.ConfigParser(interpolation=None,strict=True);config.read_string(exact(q['config']).decode('utf-8-sig'))
    expected_config={
      'General':dict(confirm_exit='0',confirm_reset='0',confirm_save='0',host_cpu='Unknown'),
      'Machine':dict(cpu_family='8088',cpu_multi='1',cpu_speed='4772728',cpu_use_dynarec='0',
                     machine='ibmxt86',mem_size='640',time_sync='disabled'),
      'Video':dict(gfxcard='cga'),
      'IBM CGA #1':dict(display_type='0',composite_type='1',rgb_type='0',snow_enabled='1',double_type='1'),
      'Input devices':dict(keyboard_type='keyboard_pc_xt',mouse_type='msserial'),
      'Storage controllers':dict(hdc_1='xtide'),
      'Hard disks':dict(hdd_01_ide_channel='0:0',hdd_01_parameters='34, 5, 969, 0, ide',hdd_01_speed='ramdisk'),
      'PC/XT XTIDE #1':dict(bios='xt'),
      'Floppy and CD-ROM drives':dict(fdd_02_type='none')}
    require(not config.defaults() and set(config.sections())==set(expected_config),'Fresh machine sections/default overrides differ')
    for section,want in expected_config.items():
        actual=dict(config.items(section,raw=True))
        if section=='Hard disks':require(bool(actual.pop('hdd_01_fn','')),'Fresh image path missing')
        require(actual==want,'Fresh machine options differ: '+section)
    return raw

def reviewed(q,data=None):
    require(q.get('status')=='REVIEWED_FRESH_CGA_COMPLETE_INSTALL','Independent fresh review acceptance pending')
    review=json.loads(exact(q['review']))
    require(review.get('outcome')=='NO_ACTIONABLE_FINDINGS' and review.get('findings')==[] and
            review.get('reviewed_commit')==q['reviewed_commit'] and review.get('sources')==q['sources'],
            'Independent final-source review missing or differs')
    return validate(q,data)

def verify(data=None):
    q=json.loads((HERE/'ACCEPT.JSN').read_bytes());return reviewed(q,data)

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--packet',type=Path);v=a.parse_args()
    try:print(json.dumps(identity(verify(v.packet.read_bytes() if v.packet else None)),indent=2))
    except (ValueError,OSError,KeyError)as e:a.exit(1,'Refused: '+str(e)+'\n')
