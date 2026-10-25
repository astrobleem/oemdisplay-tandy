#!/usr/bin/env python3
"""Replay the bounded PC1512 native evidence and exact current-source bindings.

This is a host replay, never a fresh native run or a physical-hardware claim.
The original installer receipt stays unchanged; a driver update has its own
qualified payload, native carrier extraction, three driver runs and frames.
"""
from pathlib import Path
import configparser,hashlib,importlib.machinery,json,sys,tempfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
QUAL=ROOT/'tools/P15PACK/QUALIFY.JSN'
EVIDENCE=ROOT/'docs/pc1512/OUTPUT'
CMP=importlib.machinery.SourceFileLoader('p15_verify_cmp',str(HERE/'P15CMP.PY')).load_module()

SOURCE_INPUTS={'src/pc1512/BUILD15.PY','src/pc1512/P15PATCH.PY','src/pc1512/P15OUT.PY',
    'src/pc1512/P15BENCH.PY','src/pc1512/P15CMP.PY','src/pc1512/P15VERIFY.PY',
    'src/pc1512/P15CTEST.PY','src/pc1512/P15OTEST.PY','src/pc1512/P15OUT.FIX',
    'src/rrect/RRPATCH.PY','src/rrect/RRBENCH.C','src/rrect/RRAPP.PY','src/rrect/RRCMP.PY','src/rrect/RRBENCH.DEF','src/rrect/RRBENCH.RSP','src/rrect/BUILD.BAT',
    'tools/P15PACK/PACK.PY','tools/APPSET/APPSET.C','tools/APPSET/PACK.PY','tools/DRVSET/NATIVE.PY'}
SOURCE_INPUTS|={'tools/YAMPACK/SUPPORT.JSN','tools/XR1PACK/PREPARE.PY','tools/XR1PACK/OWATCOM.TXT'}
SOURCE_INPUTS|={'src/tandysw/'+name for name in (
    'build.py','BUILD88.PY','PORT8086.PY','PORTDIB.PY','MODEPROF.PY','MODECOL.PY','MODEEXT.PY','MONOCOL.PY',
    'REPCOPY88.PY','BYTECOL.PY','CURKEEP.PY','OUTROWS.PY','WIDESCAN.PY','AUDIT88.PY','RLEABITEST.PY',
    'V1.ASM','TCURSOR.ASM','TSOFT.DEF','TSOFT.LNK','BLDCOR.BAT','BLDCUR.BAT','BLDRES.BAT','PACKRES.PY',
    'MODECOL.ASM','MONOCOL.ASM','RLE88.ASM','SDIB88.ASM')}
SOURCE_INPUTS.add('tools/BUILDDEPS/LOCK.JSON')

def identity(data):return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def verify():
    q=json.loads(QUAL.read_bytes())
    if q.get('schema')!=1 or q.get('complete') is not True or q.get('physical_hardware_qualified') is not False:
        raise ValueError('PC1512 native qualification is incomplete')
    for name,pin in q['sources'].items():
        if identity((ROOT/name).read_bytes())!=pin:raise ValueError('Qualified PC1512 source differs: '+name)
    if not SOURCE_INPUTS<=set(q['sources']):raise ValueError('Missing PC1512 source bindings')
    for name,pin in q['evidence'].items():
        if identity((EVIDENCE/name).read_bytes())!=pin:raise ValueError('PC1512 native evidence differs: '+name)
    required={'BUILD-B.JSN','BUILD-C.JSN','SCOPE.JSN','SHIPSIZE.JSN','CARRIER.JSN','PROBE.JSN','PROBEGEN.JSN','PROFILE.CFG'}
    app=json.loads((EVIDENCE/'PROBE.JSN').read_bytes())
    emitted=json.loads((EVIDENCE/'PROBEGEN.JSN').read_bytes())
    probe={'bytes':app['exe_bytes'],'sha256':app['exe_sha256']}
    if app.get('exe')!='RRBENCH.EXE' or app.get('warnings')!=[]:raise ValueError('Native probe build differs')
    generator=importlib.machinery.SourceFileLoader('p15_verify_bench',str(HERE/'P15BENCH.PY')).load_module()
    with tempfile.TemporaryDirectory() as temp:
        generated=Path(temp)/'source';generator.emit(generated)
        if (app['sources_sha256']!={n:identity((generated/n).read_bytes())['sha256'] for n in ('RRBENCH.C','RRBENCH.DEF','RRBENCH.RSP','BUILD.BAT')} or
            emitted!=json.loads((generated/'P15EMIT.JSN').read_bytes())):raise ValueError('Executed probe sources do not reproduce')
    profile=configparser.ConfigParser();config=(EVIDENCE/'PROFILE.CFG').read_bytes();profile.read_string(config.decode('utf-8-sig'))
    for key,value in {'machine':'pc1512','cpu_family':'8086','cpu_speed':'8000000','mem_size':'640','cpu_use_dynarec':'0','time_sync':'disabled'}.items():
        if profile['Machine'].get(key)!=value:raise ValueError('Unmatched PC1512 timing profile: '+key)
    if profile['Video'].get('gfxcard')!='internal':raise ValueError('PC1512 internal video is required')
    if q['config']!=identity(config):raise ValueError('Effective native config differs')
    runs={}
    for label in ('SHIPPED','BASELINE','CANDIDATE'):
        folder=EVIDENCE/label
        head,stages,frames,bad=CMP.validate(folder)
        if bad:raise ValueError(label+': '+repr(bad))
        required|={label+'/'+name for name in frames}|{label+'/RRBENCH.LOG',label+'/RUN.JSN'}
        run=json.loads((folder/'RUN.JSN').read_bytes());runs[label]=run
        for field in ('lease_acquired','owned_stopped','lease_released'):
            if run.get(field) is not True:raise ValueError(label+': '+field)
        if run['bios_mode']!=6 or run['conventional_kb']!=640:raise ValueError(label+': return state differs from shipped control')
        if label!='SHIPPED' and (run.get('complete') is not True or run.get('post_win_marker')!='RETURNED\r\n'):
            raise ValueError(label+': native run did not complete and return to DOS')
    required|={'SHIPPED/ASSESS.JSN','SHIPPED/PROMPT.PNG'}
    assessment=json.loads((EVIDENCE/'SHIPPED/ASSESS.JSN').read_bytes())
    if (assessment.get('complete') is not True or assessment.get('mode3_restored') is not False or
        assessment.get('post_win_marker')!='RETURNED\r\n' or assessment['raw_result']!=identity((EVIDENCE/'SHIPPED/RUN.JSN').read_bytes())):
        raise ValueError('Shipped native control assessment differs')
    shipped_run=runs['SHIPPED']
    if (shipped_run.get('complete') is not False or shipped_run.get('error')!="AssertionError('DOS return state')" or
        assessment['driver']!=shipped_run['fixture']['driver'] or assessment['probe']!=shipped_run['fixture']['probe'] or
        assessment['prompt_image']!=identity((EVIDENCE/'SHIPPED/PROMPT.PNG').read_bytes())):
        raise ValueError('Original shipped-control calibration receipt differs')
    original=ROOT/'tools/DRVSET/NATIVE.JSN'
    if (q['original_installer_receipt']!=identity(original.read_bytes()) or
        shipped_run['fixture']['driver']!=json.loads(original.read_bytes())['runtime']['PC1512']['PC1512.DRV']):
        raise ValueError('Shipped driver/installer anchor differs')
    for label,run in runs.items():
        environment=assessment if label=='SHIPPED' else run
        if environment['emulator']!=q['emulator'] or environment['config']!=q['config'] or environment['timing_profile']!=dict(profile['Machine']):
            raise ValueError(label+': emulator/configuration differs')
    if set(q['evidence'])!=required:raise ValueError('PC1512 evidence closure differs')
    driver_runs=[r['fixture']['driver'] for r in runs.values()]
    probe_runs=[r['fixture']['probe'] for r in runs.values()]
    fixture_runs=[r['fixture']['source_image'] for r in runs.values()]
    if not all(x==probe for x in probe_runs) or not all(x==fixture_runs[0] for x in fixture_runs):
        raise ValueError('PC1512 comparison inputs differ')
    if driver_runs[-1]!=q['driver'] or identity((ROOT/'tools/P15PACK/PAYLOAD/PC1512.DRV').read_bytes())!=q['driver']:
        raise ValueError('Current PC1512 driver is not the qualified candidate')
    if q['runtime'].get('PC1512.DRV')!=q['driver']:raise ValueError('Native carrier driver differs from executed candidate')
    pack=importlib.machinery.SourceFileLoader('p15_verify_packet',str(ROOT/'tools/P15PACK/PACK.PY')).load_module()
    if q['runtime']!={n:identity(b) for n,b in pack.payload(None).items()}:raise ValueError('Current packet/runtime closure differs')
    if set(q['outputs'])!={'P15SET.EXE','PC1512.ZIP','INSTALL.TXT'} or any(identity((ROOT/'downloads/experimental/PC1512'/name).read_bytes())!=pin for name,pin in q['outputs'].items()):
        raise ValueError('Current PC1512 downloads differ from native carrier proof')
    catalog=json.loads((ROOT/'tools/CURRENT/PRODUCTS.JSN').read_bytes())['local']['PC1512.ZIP']
    if catalog!={'source':'downloads/experimental/PC1512/PC1512.ZIP','identity':q['outputs']['PC1512.ZIP']}:
        raise ValueError('Current PC1512 catalog binding differs from qualified packet')
    builds={}
    for label,filename in [('BASELINE','BUILD-B.JSN'),('CANDIDATE','BUILD-C.JSN')]:
        build=json.loads((EVIDENCE/filename).read_bytes());audit=build['build88']
        builds[label]=build
        if {'bytes':build['bytes'],'sha256':build['sha256']}!=runs[label]['fixture']['driver']:
            raise ValueError(label+': compiled and executed driver differ')
        if (audit['build']!='PASS' or audit['instruction_audit']['unsupported'] or
            audit['rep_prefix_audit']['multi_prefix_rep'] or audit['link_audit']['result']!='PASS'):
            raise ValueError(label+': native build audit failed')
    adapters=('src/pc1512/BUILD15.PY','src/pc1512/P15PATCH.PY','src/pc1512/P15OUT.PY','src/rrect/RRPATCH.PY')
    if builds['CANDIDATE'].get('adapter_source_sha256')!={n:q['sources'][n]['sha256'] for n in adapters}:
        raise ValueError('Current adapter source differs from the actual native build inputs')
    scope=json.loads((EVIDENCE/'SCOPE.JSN').read_bytes())
    if scope['only_changed_staged_source']!=['EGA/TSOFT.ASM'] or scope['only_TOutput'] is not True:
        raise ValueError('PC1512 staged change exceeds TOutput')
    for label,key in [('BASELINE','baseline'),('CANDIDATE','candidate')]:
        if scope[key]!={k:builds[label][k] for k in ('bytes','sha256','staged_patched_sha256')}:
            raise ValueError(label+': stage scope and native build differ')
    shipped=CMP.compare(EVIDENCE/'SHIPPED',EVIDENCE/'BASELINE')
    candidate=CMP.compare(EVIDENCE/'BASELINE',EVIDENCE/'CANDIDATE')
    if not shipped['pass'] or not candidate['pass']:raise ValueError('PC1512 native frames/results differ')
    full=next(r for r in candidate['timings'] if r['stage']=='scan_full')
    if full['candidate_ms']>full['baseline_ms']+110:raise ValueError('PC1512 full-width scan regression exceeds two BIOS ticks')
    carrier=json.loads((EVIDENCE/'CARRIER.JSN').read_bytes())
    if (carrier.get('complete') is not True or carrier.get('owned_child_stopped') is not True or
        carrier.get('lease_released') is not True or carrier.get('outputs')!=q['outputs'] or
        carrier.get('runtime')!=q['runtime'] or
        carrier.get('checks')!={n:True for n in ('target_refusal_before_writes','exact_native_extraction','case_retry_preserved_user_file','normal_transaction_exit')} or
        carrier.get('process',{}).get('return')!=0 or carrier['process'].get('lease_acquired') is not True):raise ValueError('New native carrier/payload proof differs')
    return q,{'shipped':shipped,'candidate':candidate,'native_runs':runs}

if __name__=='__main__':
    q,r=verify()
    print(json.dumps({'status':'PASS: host replay of qualified native PC1512 runs',
        'driver':q['driver'],'frames_per_comparison':len(r['candidate']['frames']),
        'physical_hardware_qualified':False},indent=2))
