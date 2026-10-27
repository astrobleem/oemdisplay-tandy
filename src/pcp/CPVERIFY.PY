#!/usr/bin/env python3
"""Replay fixed ColorPlus native runs and exact current package bindings.

No compiler, emulator or network is used. Original installer/panning evidence
is retained; the fixed-driver update has separate build/frame and ZIP-composition proof.
"""
from pathlib import Path
import configparser,hashlib,importlib.machinery,json,tempfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
L=importlib.machinery.SourceFileLoader('cpp_historical_sources',str(ROOT/'tools/LEGACY/SOURCE.PY')).load_module()
QUAL=ROOT/'tools/CPPACK/QUALIFY.JSN'
EVIDENCE=ROOT/'docs/pcp/OUTPUT'
CMP=importlib.machinery.SourceFileLoader('cpp_verify_cmp',str(HERE/'CPCMP.PY')).load_module()
SOURCE_INPUTS={'src/pcp/'+n for n in ('BUILDPCP.PY','PCPPATCH.PY','CPPOUT.PY','CPPOUT.FIX',
    'CPPOTEST.PY','CPBENCH.PY','CPCMP.PY','CPCTEST.PY','CPVERIFY.PY')}
SOURCE_INPUTS|={'src/rrect/'+n for n in ('RRPATCH.PY','RRBENCH.C','RRAPP.PY','RRCMP.PY','RRBENCH.DEF','RRBENCH.RSP','BUILD.BAT')}
SOURCE_INPUTS|={'src/tandysw/'+n for n in ('build.py','BUILD88.PY','PORT8086.PY','PORTDIB.PY','MODEPROF.PY',
    'MODECOL.PY','MODEEXT.PY','MONOCOL.PY','REPCOPY88.PY','BYTECOL.PY','CURKEEP.PY','OUTROWS.PY','WIDESCAN.PY',
    'AUDIT88.PY','RLEABITEST.PY','V1.ASM','TCURSOR.ASM','TSOFT.DEF','TSOFT.LNK','BLDCOR.BAT','BLDCUR.BAT',
    'BLDRES.BAT','PACKRES.PY','MODECOL.ASM','MONOCOL.ASM','RLE88.ASM','SDIB88.ASM')}
SOURCE_INPUTS|={'tools/BUILDDEPS/LOCK.JSON','tools/APPSET/APPSET.C','tools/APPSET/PACK.PY',
    'tools/DRVSET/VERIFY.PY','tools/DRVSET/NATIVE.PY','tools/CPPACK/PACKAGE.PY',
    'tools/PANUI/PACKAGE.PY','tools/PANUI/BASE.JSN','tools/SPPACK/PACKAGE.PY','tools/SPPACK/PUBLIC.JSN',
    'src/panui/VERIFY.PY','tools/CURRENT/BUNDLE.PY','tools/CURRENT/GUIDES/CPPAN.TXT',
    'tools/XR1PACK/PREPARE.PY','tools/XR1PACK/OWATCOM.TXT'}

def identity(data):return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

# These unchanged host-only producer files are LF in Git and CRLF in a
# Windows autocrlf checkout. Native build/probe/evidence bytes stay exact.
SOURCE_TEXT_LF={'tools/PANUI/BASE.JSN','tools/PANUI/PACKAGE.PY'}
def source_identity(name,data):
    pin=json.loads(QUAL.read_bytes())['sources'][name]
    data=L.source(name,data,pin,name in SOURCE_TEXT_LF)
    return identity(data.replace(b'\r\n',b'\n') if name in SOURCE_TEXT_LF else data)

def recorded_files(folder,run,frames):
    expected={n:identity((folder/n).read_bytes()) for n in set(frames)|{'RRBENCH.LOG'}}
    if run.get('files')!=expected:raise ValueError('Native run file manifest differs from exported frames/log')

def package():
    return importlib.machinery.SourceFileLoader('cpp_current_overlay',str(ROOT/'tools/CPPACK/PACKAGE.PY')).load_module()

def packet():
    p=package();return p.members(p.outputs()['CPPAN.ZIP'])

def verify():
    q=json.loads(QUAL.read_bytes())
    if q.get('schema')!=1 or q.get('complete') is not True or q.get('physical_hardware_qualified') is not False:
        raise ValueError('ColorPlus fixed-driver qualification is incomplete')
    if not SOURCE_INPUTS<=set(q['sources']):raise ValueError('Missing ColorPlus source bindings')
    if q.get('source_text_lf')!=sorted(SOURCE_TEXT_LF):raise ValueError('Host-only source text normalization differs')
    for n,pin in q['sources'].items():
        if source_identity(n,(ROOT/n).read_bytes())!=pin:raise ValueError('Qualified ColorPlus source differs: '+n)
    for n,pin in q['evidence'].items():
        if identity((EVIDENCE/n).read_bytes())!=pin:raise ValueError('ColorPlus evidence differs: '+n)
    required={'BUILD-B.JSN','BUILD-C.JSN','STAGE.JSN','SCOPE.JSN','SUMMARY.JSN','PROBE.JSN','PROBEGEN.JSN','PROFILE.CFG'}
    app=json.loads((EVIDENCE/'PROBE.JSN').read_bytes());emitted=json.loads((EVIDENCE/'PROBEGEN.JSN').read_bytes())
    if app.get('exe')!='RRBENCH.EXE' or app.get('warnings')!=[]:raise ValueError('ColorPlus native probe build differs')
    probe={'bytes':app['exe_bytes'],'sha256':app['exe_sha256']}
    generator=importlib.machinery.SourceFileLoader('cpp_verify_bench',str(HERE/'CPBENCH.PY')).load_module()
    with tempfile.TemporaryDirectory() as temp:
        generated=Path(temp)/'source';generator.emit(generated)
        if app['sources_sha256']!={n:identity((generated/n).read_bytes())['sha256'] for n in ('RRBENCH.C','RRBENCH.DEF','RRBENCH.RSP','BUILD.BAT')} or emitted!=json.loads((generated/'CPEMIT.JSN').read_bytes()):
            raise ValueError('Executed ColorPlus probe sources do not reproduce')
    config=(EVIDENCE/'PROFILE.CFG').read_bytes();profile=configparser.ConfigParser();profile.read_string(config.decode('utf-8-sig'))
    for k,v in {'machine':'ibmxt86','cpu_family':'8088','cpu_speed':'4772728','cpu_multi':'1','mem_size':'640','cpu_use_dynarec':'0','time_sync':'disabled'}.items():
        if profile['Machine'].get(k)!=v:raise ValueError('Unmatched ColorPlus timing profile: '+k)
    if profile['Video'].get('gfxcard')!='plantronics' or q['config']!=identity(config):raise ValueError('ColorPlus effective video/configuration differs')
    runs={}
    for label in ('SHIPPED','BASELINE','CANDIDATE'):
        folder=EVIDENCE/label;head,stages,frames,bad=CMP.validate(folder)
        if bad:raise ValueError(label+': '+repr(bad))
        required|={label+'/'+n for n in frames}|{label+'/RRBENCH.LOG',label+'/RUN.JSN',label+'/FINAL.JSN',label+'/PROMPT.PNG'}
        run=json.loads((folder/'RUN.JSN').read_bytes());runs[label]=run
        recorded_files(folder,run,frames)
        if any(run.get(k) is not True for k in ('complete','lease_acquired','owned_stopped','lease_released')) or run.get('post_win_marker')!='RETURNED\r\n':raise ValueError(label+': native run did not complete and return')
        if run.get('bios_mode')!=6 or run.get('conventional_kb')!=640:raise ValueError(label+': DOS return differs from shipped control')
        if run['emulator']!=q['emulator'] or run['config']!=q['config'] or run['timing_profile']!=dict(profile['Machine']):raise ValueError(label+': unmatched native environment')
        final=json.loads((folder/'FINAL.JSN').read_bytes())
        if final.get('bad')!=[] or final.get('frames')!=48 or final['fat'].get('copies_equal') is not True or len(set(final['fat']['sha256']))!=1 or final['driver_readback']!=run['fixture']['driver'] or final['probe_readback']!=probe:raise ValueError(label+': stopped-image readback differs')
        if (folder/'PROMPT.PNG').read_bytes()!=(EVIDENCE/'SHIPPED/PROMPT.PNG').read_bytes():raise ValueError(label+': terminal frame differs')
    required|={'SHIPPED/ASSESS.JSN','SHIPPED/POSTCHECK.JSN'}
    assessment=json.loads((EVIDENCE/'SHIPPED/ASSESS.JSN').read_bytes())
    if assessment.get('complete') is not True or assessment.get('visual_dos_prompt') is not True or assessment['result']!=identity((EVIDENCE/'SHIPPED/RUN.JSN').read_bytes()) or assessment['return_image']!=identity((EVIDENCE/'SHIPPED/PROMPT.PNG').read_bytes()) or assessment['postcheck']!=identity((EVIDENCE/'SHIPPED/POSTCHECK.JSN').read_bytes()):raise ValueError('Shipped ColorPlus control assessment differs')
    original=(ROOT/'tools/DRVSET/NATIVE.JSN').read_bytes();old=json.loads(original)
    if q['original_installer_receipt']!=identity(original) or runs['SHIPPED']['fixture']['driver']!=old['runtime']['ColorPlus']['PCP3216.DRV']:raise ValueError('Original ColorPlus installer/shipped-driver anchor differs')
    if set(q['evidence'])!=required:raise ValueError('ColorPlus evidence closure differs')
    if any(r['fixture']['probe']!=probe or r['fixture']['source_image']!=runs['SHIPPED']['fixture']['source_image'] for r in runs.values()):raise ValueError('ColorPlus comparison inputs differ')
    if runs['CANDIDATE']['fixture']['driver']!=q['driver'] or identity((ROOT/'tools/CPPACK/PAYLOAD/PCP3216.DRV').read_bytes())!=q['driver']:raise ValueError('Current fixed driver differs from executed candidate')
    actual={n:identity(b) for n,b in packet().items()}
    if q['runtime']!=actual or actual['PCP3216.DRV']!=q['driver']:raise ValueError('Current ColorPlus runtime closure differs')
    p=package();base=p.P.outputs()['CPPAN.ZIP'];before=p.members(base)
    if identity(base)!=q['panning_reference']['packet'] or q['panning_reference']['settings']!=identity((ROOT/'docs/QUAL/WDESK/NATIVE.JSN').read_bytes()):raise ValueError('Qualified current panning reference differs')
    if identity(before['PCP3216.DRV'])!=runs['SHIPPED']['fixture']['driver'] or set(actual)!=set(before) or any(actual[n]!=identity(before[n]) for n in actual if n!='PCP3216.DRV'):raise ValueError('Fixed update changed current panning/installer/support inputs')
    if identity((ROOT/'downloads/experimental/CPPAN/CPPSET.EXE').read_bytes())!=old['outputs']['ColorPlus']['CPPSET.EXE']:raise ValueError('Original ColorPlus carrier evidence changed')
    if set(q['outputs'])!={'CPPAN.ZIP','INSTALL.TXT'} or any(identity((ROOT/'downloads/experimental/CPPAN'/n).read_bytes())!=pin for n,pin in q['outputs'].items()):raise ValueError('Current ColorPlus downloads differ from qualified ZIP composition')
    catalog=json.loads((ROOT/'tools/CURRENT/PRODUCTS.JSN').read_bytes())['local']['CPPAN.ZIP']
    if catalog!={'source':'downloads/experimental/CPPAN/CPPAN.ZIP','identity':q['outputs']['CPPAN.ZIP']}:
        current_source=catalog['source']
        current_producer='tools/PAN/PUBLISH.PY' if current_source=='downloads/PAN/CPPAN.ZIP' else 'tools/UPAN/PUBLISH.PY'
        unified=importlib.machinery.SourceFileLoader('cpp_unified_catalog',str(ROOT/current_producer)).load_module()
        accepted,products=unified.products()
        data=products['CPPAN.ZIP']
        if current_source not in ('downloads/UNIPAN/CPPAN.ZIP','downloads/PAN/CPPAN.ZIP') or catalog!={'source':current_source,'identity':identity(data)} or (ROOT/catalog['source']).read_bytes()!=data:
            raise ValueError('Current ColorPlus catalog binding differs')
        if identity(unified.C.members(data)['PCP3216.DRV'])!=q['driver']:
            raise ValueError('Unified ColorPlus driver differs from native qualification')
    builds={}
    for label,n in [('BASELINE','BUILD-B.JSN'),('CANDIDATE','BUILD-C.JSN')]:
        b=json.loads((EVIDENCE/n).read_bytes());builds[label]=b;a=b['build88']
        if b['driver']!=runs[label]['fixture']['driver'] or any(b.get(k) is not True for k in ('build_complete','owned_stopped','lease_released')) or b.get('exit_code')!=0:raise ValueError(label+': compiled/executed identity differs')
        if a['build']!='PASS' or a['instruction_audit']['unsupported'] or a['rep_prefix_audit']['multi_prefix_rep'] or a['link_audit']['result']!='PASS' or a['ui_profile']['profile']!='stock':raise ValueError(label+': native build audit/profile differs')
    for key,n in [('adapter','src/pcp/BUILDPCP.PY'),('pcppatch','src/pcp/PCPPATCH.PY'),('cppout','src/pcp/CPPOUT.PY'),('rrpatch','src/rrect/RRPATCH.PY'),('build88','src/tandysw/BUILD88.PY')]:
        if builds['CANDIDATE']['inputs'][key]!=q['sources'][n]:raise ValueError('Current source differs from native build: '+n)
    stage=json.loads((EVIDENCE/'STAGE.JSN').read_bytes());scope=json.loads((EVIDENCE/'SCOPE.JSN').read_bytes())
    if stage.get('only_TOutput') is not True or stage['changed_staged_files']!=['renderer/EGA/TSOFT.ASM'] or scope['only_changed_staged_source']!=['EGA/TSOFT.ASM'] or scope['code_delta']!=240 or scope['data_delta']!=0 or not scope['same_resources']:raise ValueError('ColorPlus change exceeds bounded Output path')
    for label,key in [('BASELINE','baseline'),('CANDIDATE','candidate')]:
        b=builds[label];r=b['build_report'];wanted=r.get('output_gate_staged_sha256',r['plantronics_edits_staged_sha256'])['TSOFT.ASM']
        if stage[key]['sha256']!=wanted or r['plantronics_edits_staged_sha256']['TCURSOR.ASM']!=stage['tcursor']['sha256']:raise ValueError(label+': staged native hashes differ')
    shipped=CMP.compare(EVIDENCE/'SHIPPED',EVIDENCE/'BASELINE');candidate=CMP.compare(EVIDENCE/'BASELINE',EVIDENCE/'CANDIDATE')
    if not shipped['pass'] or not candidate['pass']:raise ValueError('ColorPlus native frame/results differ')
    full=next(t for t in candidate['timings'] if t['stage']=='scan_full')
    if full['candidate_ms']>full['baseline_ms']+55:raise ValueError('ColorPlus full-width scan regression exceeds one BIOS tick')
    return q,{'shipped':shipped,'candidate':candidate,'native_runs':runs}

if __name__=='__main__':
    q,r=verify();print(json.dumps({'status':'PASS: host replay of qualified native ColorPlus runs','driver':q['driver'],'frames_per_comparison':len(r['candidate']['frames']),'physical_hardware_qualified':False},indent=2))
