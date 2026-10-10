"""Mandatory host preflight for the frozen final-gates kit. Never launches a guest."""
from pathlib import Path
import argparse,csv,hashlib,json,re,struct
GR2='1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067'
CNF='371bd1935f84505d61873f1e08a17b858d667a5149d71995d4285c6f17782bdb'
STATIC='995d71e3626de64c8fe21bc1f037e0dece0853d4f0d09082bf607b2d237b37ef'
MODES={'TR53216':'133,96,72','TR56404':'200,96,48','TR51616':'200,96,48','TR53204':'200,96,48','TR56402':'200,96,48','TXTMODE':'0200,96,48'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def readjson(p):return json.loads(p.read_bytes())
def exact(p,h):
    need(p.is_file() and not p.is_symlink(),'Missing/linked input '+str(p))
    need(sha(p)==h,'Changed input '+str(p))
def inside(root,relative):
    p=(root/relative).resolve();need(p.is_relative_to(root),'Path escapes kit '+relative);return p
def catalog(p,expected_sha):
    exact(p,expected_sha);section='';rows={}
    for line in p.read_text('ascii').splitlines():
        line=line.strip()
        if line.startswith('['):section=line.lower();continue
        if section=='[display]' and '=' in line:
            name,value=line.split('=',1);name=name.strip().upper()
            need(name not in rows,'Duplicate display '+str(p));rows[name]=next(csv.reader([value],skipinitialspace=True,strict=True))
    need(set(rows)==set(MODES),'Wrong six candidate profiles '+str(p))
    for name,metric in MODES.items():
        row=rows[name];need(len(row)==9,'Wrong catalog resource count '+name)
        need(row[0].strip().upper()=='A:'+name+'.DRV' and row[2].strip()==metric,'Wrong driver/metrics '+name)
        need([row[i].strip().upper() for i in (3,4,8)]==['A:CGA.GR2','A:XTSTATIC.LGO','A:WXTSPL01.RLE'],'Stale logo/grabber/art '+name)
    need('CGALOGO.LGO' not in p.read_text('ascii').upper(),'Legacy source logo '+str(p))
def binding(root,which):
    meta=readjson(root/'KIT.JSON');p=root/'PREP/BUILD';b=readjson(p/(which+'.BIND.JSN'))
    need(b['source_pins']==meta['compile_source'],'Stale compiled-source binding '+which)
    for name,h in b['source_pins'].items():exact(p/name,h)
    exact(p/(which+'.EXE'),b['binary_sha256']);exact(p/(which+'.LOG'),b['log_sha256'])
    need(b['flags']==meta['compiler_flags'][which],'Wrong compiler flags '+which)
    return b
def check(root,group=None,job=None):
    root=Path(root).resolve();meta=readjson(root/'KIT.JSON')
    need(meta['native_runs_authorized'] is False and meta['publication_allowed'] is False,'Kit is not the frozen unqualified plan')
    for name,h in meta['frozen_source'].items():exact(inside(root,name),h)
    candidate=root/'CANDIDATE';catsha=meta['catalog_sha256'];catalog(candidate/'OEMSETUP.INF',catsha)
    exact(candidate/'TINST.EXE','cc0036bbb82c89cef6dfbe025c10f7d61732d1271f9805031070d4b515517df1')
    exact(candidate/'XTMODE.EXE','34ff85d216a7c0233066aedc27c2199c2772e278438e627ce548d07909de4160')
    for name,h in meta['external_toolchain_pins'].items():exact(Path(meta['compiler_path'])/name,h)
    exact(Path(meta['dosbox_path']),meta['dosbox_sha256'])
    for name,h in meta['compile_source'].items():exact(root/'PREP/BUILD'/name,h)
    need((candidate/'XTSTATIC.LGO').stat().st_size==361 and sha(candidate/'XTSTATIC.LGO')==STATIC,'Original static module pin')
    manifest={n:h for h,n in (line.split() for line in (candidate/'MANIFEST.SHA').read_text('ascii').splitlines())}
    need(set(manifest)==set(meta['runtime_pins']),'Candidate manifest allowlist')
    need({n:h for n,h in manifest.items() if n.endswith('.FON')}==meta['qualified_font_pins'],'Font bytes differ from qualified originals')
    need(set(n for n in manifest if n.startswith(('CGA','EGA'))) == {'CGA.GR2'},'Legacy public dependencies')
    for name,h in manifest.items():
        need(h==meta['runtime_pins'][name],'Stale manifest '+name)
        if name!='CGA.GR2':exact(candidate/name,h)
    need(manifest['CGA.GR2']==GR2,'Wrong owned grabber pin')
    for case in meta['fixtures']:
        fixture=inside(root,case['guest']);source=inside(root,case['source'])
        catalog(source/'OEMSETUP.INF',case['catalog_sha256'])
        for name,h in case['source_files'].items():exact(source/name,h)
        need(not(source/'CGALOGO.LGO').exists(),'Legacy source logo retained '+case['name'])
        exact(fixture/'WINDOWS/SYSTEM/WIN.CNF',CNF)
        need((fixture/'WINDOWS/SYSTEM/WIN.CNF').stat().st_size==3456,'Wrong WIN.CNF size')
        for rel,h in case['owned_grabbers'].items():exact(fixture/rel,h)
        for name,h in case['test_helpers'].items():exact(fixture/name,h)
        if case['kind']=='setup':
            for name,h in meta['runtime_pins'].items():
                if name!='CGA.GR2':exact(source/name,case['catalog_sha256'] if name=='OEMSETUP.INF' else h)
            exact(source/'CGA.GR2',GR2);catalog(source/'OEMBASE.INF',catsha)
            need(not any((source/n).exists() for n in ('WINXT.WVO','TSTART.WVO')),'Stale generated launcher rollback snapshots')
            bat=(source/'WINXT.BAT').read_text('ascii')
            for command in ('XTMODE.EXE RECOVER C:\\WINDOWS\\SYSTEM.INI','XTMODE.EXE GUARD C:\\WINDOWS\\SYSTEM.INI','XTMODE.EXE ACCEPT C:\\WINDOWS\\SYSTEM.INI'):
                need(command in bat,'Missing guarded candidate launcher '+command)
        elif group=='prep' and job is None:need(not(fixture/'WINXT').exists(),'Preparation output is not fresh '+case['name'])
    for name,jobdata in meta['jobs'].items():
        cfg=inside(root,jobdata['config']);exact(cfg,meta['frozen_source'][jobdata['config']])
        text=cfg.read_text('ascii');actual=re.findall(r'^MOUNT ([A-Z]) "([^"]+)"$',text,re.M)
        expected=[(drive,str(inside(root,path))) if drive!='T' else (drive,meta['compiler_path']) for drive,path in jobdata['mounts']]
        need(actual==expected,'Wrong/missing mount path '+name)
        need('IMGMOUNT' not in text and not any('E:\\budmaker' in s for _,s in actual),'Unexpected external writable mount '+name)
        need(jobdata['seconds']<=meta['max_job_seconds'],'Unbounded job '+name)
    if group:
        need(group in ('setup','prep'),'Unknown lease group')
        for case in meta['fixtures']:
            if case['kind']!=group:continue
            if job and case['name']!=job:continue
            if (root/'RESULTS'/(case['name']+'.JSON')).exists():continue
            fixture=inside(root,case['guest'])
            for rel,h in case['preimage'].items():exact(fixture/rel,h)
    if job:
        if job=='PFAST':binding(root,'PREPXT')
        elif job=='PZERO':binding(root,'ZEROPREP')
        elif job=='PVERIFY':binding(root,'PREPXT')
    return {'host_preflight_pass':True,'fixtures':len(meta['fixtures']),'frozen_inputs':len(meta['frozen_source']),'catalog_sha256':catsha,'native_evidence':False}
def finish(root,job):
    root=Path(root).resolve();meta=readjson(root/'KIT.JSON');out=root/'RESULTS';out.mkdir(exist_ok=True)
    if job in ('PRODBLD','ZEROBLD'):
        which='PREPXT' if job=='PRODBLD' else 'ZEROPREP';p=root/'PREP/BUILD'
        need((p/(which+'.OK')).read_text('ascii').strip()=='PASS','Native compile completion missing')
        log=(p/(which+'.LOG')).read_text('latin1');need(not re.search('warning|error',log,re.I),'Compiler warning/error')
        need((p/(which+'.EXE')).read_bytes()[:2]==b'MZ','Native DOS EXE header')
        record={'native_compile_pass':True,'source_pins':meta['compile_source'],'flags':meta['compiler_flags'][which],'binary_sha256':sha(p/(which+'.EXE')),'log_sha256':sha(p/(which+'.LOG'))}
        (p/(which+'.BIND.JSN')).write_text(json.dumps(record,indent=2)+'\n');binding(root,which)
    else:
        case=next(c for c in meta['fixtures'] if c['name']==job);g=inside(root,case['guest'])
        need((g/'DONE.OK').exists() and not(g/'FAIL.TXT').exists(),'Native completion missing '+job)
        memory=(g/'AFTER.LOG').read_text('ascii');need(re.search(r'^0270 5003 0000',memory,re.M),'DOS memory/mode mismatch')
        if case['kind']=='prep':
            for name,h in meta['runtime_pins'].items():exact(g/'WINXT'/name,h)
            exact(g/'WINXT/MANIFEST.SHA',sha(root/'CANDIDATE/MANIFEST.SHA'))
            for rel,h in case['preimage'].items():exact(g/rel,h)
            log=(g/'PREP.LOG').read_text('ascii');need('Preparation succeeded; Setup was not started.' in log,'Native preparation incomplete')
            if job=='PZERO':
                counters=[int(n) for n in re.findall(r'SHA blocks=(\d+)',log)]
                need(len(counters)==2 and counters==[0,0] and 'output readback=0 bytes' in log,'Default diagnostic SHA/readback was nonzero')
            elif job=='PVERIFY':need('Deep verification ON.' in log and 'self-test passed' in log,'VERIFY not exercised')
            record={'native_pass':True,'runtime_and_owned_bytes_exact':True,'Windows_and_boot_preimages_exact':True,'default_counters':counters if job=='PZERO' else 'not instrumented in production','log_sha256':sha(g/'PREP.LOG')}
        else:
            data=(g/'SELECTED.INI').read_text('ascii');section='';selected={}
            for line in data.splitlines():
                if line.startswith('['):section=line.strip().lower()
                elif '=' in line:
                    k,v=line.split('=',1);selected[(section,k.strip().lower())]=v.strip().upper()
            for key,value in case['selected_boot'].items():need(selected.get(('[boot]',key))==value,'Wrong native selection '+key)
            com=(g/'SELECTED.COM').read_bytes();need(len(com)==7879 and com[:3456]==(g/'WINDOWS/SYSTEM/WIN.CNF').read_bytes(),'Wrong candidate common loader')
            need(com[3456:3817]==(root/'CANDIDATE/XTSTATIC.LGO').read_bytes() and com[3817:]==(root/'CANDIDATE/WXTSPL01.RLE').read_bytes(),'Wrong static resource/art')
            exact(g/'SELECTED.WAV',case['wave_preimage_sha256'])
            trace=(g/'KEYTRACE.BIN').read_bytes()
            row,phase,age,actions,armed,busy=struct.unpack('<BBHHBB',trace[:8])
            transitions=[struct.unpack('<BBHHH',trace[n:n+8]) for n in range(8,len(trace),8) if any(trace[n:n+8])]
            # Six required phase changes; extra media-path prompts are optional.
            need(row==case['row'] and phase==6 and actions>=6,'Incomplete native controller phases')
            phases=[t[0] for i,t in enumerate(transitions) if i==0 or t[0]!=transitions[i-1][0]]
            need(phases==list(range(1,7)) and all(t[1]==row for t in transitions),'Incomplete native controller transition trace')
            for name in case['selected_boot'].values():
                if name in meta['runtime_pins']:
                    path=g/'WINDOWS'/name
                    if not path.is_file():path=g/'WINDOWS/SYSTEM'/name
                    exact(path,meta['runtime_pins'][name])
            record={'native_Setup_pass':True,'row':row,'phase':phase,'actions':actions,'common_bytes':len(com),'wave_unchanged':True,'selected_boot':case['selected_boot'],'text_GUI_quality_claim':False}
        record['DOS_KB']=624;record['DOS_mode']=3
    (out/(job+'.JSON')).write_text(json.dumps(record,indent=2)+'\n');return record
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('kit',type=Path);p.add_argument('--group',choices=('setup','prep'));a=p.parse_args();print(json.dumps(check(a.kit,a.group),indent=2))
