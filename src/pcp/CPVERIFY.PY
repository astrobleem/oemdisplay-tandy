#!/usr/bin/env python3
"""Replay fixed ColorPlus native runs and exact current package bindings.

No compiler, emulator or network is used. Original installer/panning evidence
is retained; the fixed-driver update has separate build, frame and carrier proof.
"""
from pathlib import Path
import configparser,hashlib,importlib.machinery,json,tempfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
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
    'tools/DRVSET/PACK.PY','tools/DRVSET/VERIFY.PY','tools/DRVSET/NATIVE.PY',
    'tools/SPPACK/PACKAGE.PY','src/softpan/PACKCP.PY','tools/XR1PACK/PREPARE.PY','tools/XR1PACK/OWATCOM.TXT'}

def identity(data):return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def packet():
    p=importlib.machinery.SourceFileLoader('cpp_verify_payload',str(ROOT/'tools/SPPACK/PACKAGE.PY')).load_module()
    files=p.payload('CPPAN',json.loads((ROOT/'tools/SPPACK/PUBLIC.JSN').read_bytes()))
    files['INSTALL.TXT']=(ROOT/'tools/DRVSET/CPPAN.TXT').read_bytes()
    files['OWATCOM.TXT']=(ROOT/'tools/XR1PACK/OWATCOM.TXT').read_bytes()
    return files

def verify():
    q=json.loads(QUAL.read_bytes())
    if q.get('schema')!=1 or q.get('complete') is not True or q.get('physical_hardware_qualified') is not False:
        raise ValueError('ColorPlus fixed-driver qualification is incomplete')
    if not SOURCE_INPUTS<=set(q['sources']):raise ValueError('Missing ColorPlus source bindings')
    for n,pin in q['sources'].items():
        if identity((ROOT/n).read_bytes())!=pin:raise ValueError('Qualified ColorPlus source differs: '+n)
    for n,pin in q['evidence'].items():
        if identity((EVIDENCE/n).read_bytes())!=pin:raise ValueError('ColorPlus evidence differs: '+n)
    required={'BUILD-B.JSN','BUILD-C.JSN','STAGE.JSN','SCOPE.JSN','SUMMARY.JSN','CARRIER.JSN','PROBE.JSN','PROBEGEN.JSN','PROFILE.CFG'}
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
    if runs['CANDIDATE']['fixture']['driver']!=q['driver'] or identity((ROOT/'tools/SPPACK/PAYLOAD/CPPAN/PCP3216.DRV').read_bytes())!=q['driver']:raise ValueError('Current fixed driver differs from executed candidate')
    actual={n:identity(b) for n,b in packet().items()}
    if q['runtime']!=actual or actual['PCP3216.DRV']!=q['driver']:raise ValueError('Current ColorPlus runtime closure differs')
    if set(actual)!=set(old['runtime']['ColorPlus']) or any(actual[n]!=old['runtime']['ColorPlus'][n] for n in actual if n!='PCP3216.DRV'):raise ValueError('Fixed update changed panning/installer/support inputs')
    if set(q['outputs'])!={'CPPSET.EXE','CPPAN.ZIP','INSTALL.TXT'} or any(identity((ROOT/'downloads/experimental/CPPAN'/n).read_bytes())!=pin for n,pin in q['outputs'].items()):raise ValueError('Current ColorPlus downloads differ from carrier proof')
    catalog=json.loads((ROOT/'tools/CURRENT/PRODUCTS.JSN').read_bytes())['local']['CPPAN.ZIP']
    if catalog!={'source':'downloads/experimental/CPPAN/CPPAN.ZIP','identity':q['outputs']['CPPAN.ZIP']}:raise ValueError('Current ColorPlus catalog binding differs')
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
    carrier=json.loads((EVIDENCE/'CARRIER.JSN').read_bytes())
    if any(carrier.get(k) is not True for k in ('complete','owned_child_stopped','lease_released')) or carrier.get('outputs')!=q['outputs'] or carrier.get('runtime')!=q['runtime'] or carrier.get('checks')!={n:True for n in ('target_refusal_before_writes','exact_native_extraction','case_retry_preserved_user_file','normal_transaction_exit')} or carrier.get('process',{}).get('return')!=0 or carrier['process'].get('lease_acquired') is not True:raise ValueError('New ColorPlus native carrier proof differs')
    return q,{'shipped':shipped,'candidate':candidate,'native_runs':runs}

def status(outputs,files):
    native=importlib.machinery.SourceFileLoader('cpp_original_installer',str(ROOT/'tools/DRVSET/NATIVE.PY')).load_module()
    state,receipt=native.status('ColorPlus',outputs,files)
    if state.startswith('PASS:') or not QUAL.is_file():return state,receipt
    q=json.loads(QUAL.read_bytes())
    if q.get('outputs')!=outputs or q.get('runtime')!={n:identity(b) for n,b in files.items()}:return state,receipt
    verify()
    return 'PASS: fixed ColorPlus Output/frame/return-state qualification and exact new carrier; original panning/installer/support preserved',{'path':'tools/CPPACK/QUALIFY.JSN',**identity(QUAL.read_bytes())}

if __name__=='__main__':
    q,r=verify();print(json.dumps({'status':'PASS: host replay of qualified native ColorPlus runs','driver':q['driver'],'frames_per_comparison':len(r['candidate']['frames']),'physical_hardware_qualified':False},indent=2))
