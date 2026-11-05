"""Exercise the exact inline two-driver scope step without release writes."""
import hashlib,importlib.machinery,json,os,tempfile,textwrap
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[2]
workflow=(ROOT/'.github/workflows/colorplus.yml').read_text()
start=workflow.index('          import importlib.machinery,json,os\n')
end=workflow.index('          PYCODE',start)
source=textwrap.dedent(workflow[start:end]).replace("'tools/CPPACK/CPPUB.PY'",repr(str(ROOT/'tools/CPPACK/CPPUB.PY')))
code=compile(source,'colorplus.yml:scope','exec')
M=importlib.machinery.SourceFileLoader('scope_packets',str(ROOT/'tools/CPPACK/CPPUB.PY')).load_module()
def yamaha(driver=b'qualified Yamaha',support=b'current support'):
    files={'YAM160.DRV':driver,'CGA.GR2':support}
    record={'schema':1,'profile':'b800','driver':'YAM160.DRV','native_test':'not asserted by host packaging',
            'files':{n:M.P.identity(b) for n,b in sorted(files.items())}}
    files['MANIFEST.JSN']=M.P.text(json.dumps(record))
    files['SHA256.SUM']=M.P.text(''.join(M.P.identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items())))
    return M.P.archive(files)
data={'CPPAN.ZIP':M.P.archive({'PCP3216.DRV':b'qualified fixed','PANCFG.EXE':b'current helper','INSTALL.TXT':b'current derived guide'}),
      'YAMAHA.ZIP':yamaha()}
identities={n:M.P.identity(b) for n,b in data.items()}
def fixture(previous=None,missing=(),duplicate=(),catalog=None,stale_sums=False,damage=None):
    bodies=dict(data);bodies.update(previous or {})
    record=json.dumps({'assets':catalog or identities}).encode()
    sums=(''.join(pin['sha256']+'  '+n+'\n' for n,pin in sorted(identities.items()))+
          ('0'*64 if stale_sums else hashlib.sha256(record).hexdigest())+'  CURRENT.JSN\n').encode()
    bodies.update({'CURRENT.JSN':record,'CURRENT.SHA':sums})
    rows=[]
    for name,body in bodies.items():
        if name in missing:continue
        row={'name':name,'size':len(body),'digest':'sha256:'+hashlib.sha256(body).hexdigest(),'browser_download_url':'https://example.invalid/'+name}
        if name==damage:row['size']+=1
        rows.append(row)
        if name in duplicate:rows.append(dict(row))
    return rows,bodies
oldcp=M.P.archive({'PCP3216.DRV':b'old fixed','PANCFG.EXE':b'current helper','INSTALL.TXT':b'old guide'})
cases=[
    ('same',fixture(),False),
    ('fixed-colorplus',fixture({'CPPAN.ZIP':oldcp}),True),
    ('colorplus-guide-only',fixture({'CPPAN.ZIP':M.P.archive({'PCP3216.DRV':b'qualified fixed','PANCFG.EXE':b'current helper','INSTALL.TXT':b'old guide'})}),True),
    ('fixed-yamaha',fixture({'YAMAHA.ZIP':yamaha(b'old Yamaha')}),True),
    ('both-fixed',fixture({'CPPAN.ZIP':oldcp,'YAMAHA.ZIP':yamaha(b'old Yamaha')}),True),
    ('noncanonical-cp',fixture({'CPPAN.ZIP':oldcp+b'trailing bytes'}),'error'),
    ('noncanonical-yamaha',fixture({'YAMAHA.ZIP':yamaha(b'old Yamaha')+b'trailing bytes'}),'error'),
    ('shared-cp-helper',fixture({'CPPAN.ZIP':M.P.archive({'PCP3216.DRV':b'old fixed','PANCFG.EXE':b'newer helper','INSTALL.TXT':b'old guide'})}),'unsafe'),
    ('shared-yamaha-helper',fixture({'YAMAHA.ZIP':yamaha(b'old Yamaha',b'newer helper')}),'unsafe'),
    ('member-closure',fixture({'CPPAN.ZIP':M.P.archive({'PCP3216.DRV':b'qualified fixed'})}),'unsafe'),
    ('colorplus-catalog-old',fixture(catalog=dict(identities,**{'CPPAN.ZIP':dict(identities['CPPAN.ZIP'],bytes=1)})),True),
    ('yamaha-catalog-old',fixture(catalog=dict(identities,**{'YAMAHA.ZIP':dict(identities['YAMAHA.ZIP'],bytes=1)})),True),
    ('sums-incomplete',fixture(stale_sums=True),True)]
for name in M.ORDER:
    cases.append(('missing-'+name,fixture(missing=(name,)),True))
    cases.append(('duplicate-'+name,fixture(duplicate=(name,)),'error'))
    cases.append(('metadata-'+name,fixture(damage=name),'error'))
results=[]
with tempfile.TemporaryDirectory(prefix='driver-scope-') as temp:
    tmp=Path(temp);(tmp/'current').mkdir()
    for name,body in data.items():(tmp/'current'/name).write_bytes(body)
    oldcwd=Path.cwd()
    try:
        os.chdir(tmp)
        for name,(rows,bodies),expected in cases:
            output=tmp/(name+'.out');payload=json.dumps({'assets':rows}).encode()
            def respond(request,timeout):
                assert timeout==60
                body=payload if request.full_url.startswith('https://api.github.com/') else bodies[request.full_url.rsplit('/',1)[1]]
                response=mock.Mock();response.read.return_value=body;return response
            with mock.patch.dict(os.environ,{'GITHUB_OUTPUT':str(output)}),mock.patch('urllib.request.urlopen',side_effect=respond):
                try:exec(code,{})
                except ValueError:
                    assert expected in ('error','unsafe'),name
                    if expected=='error':assert not output.exists(),name
                    else:assert output.read_text()=='changed=true\ndriver_only=false\n',name
                else:
                    assert expected not in ('error','unsafe'),name
                    assert output.read_text()=='changed='+str(expected).lower()+'\ndriver_only=true\n',name
            results.append(name)
    finally:os.chdir(oldcwd)
assert "if: steps.scope.outputs.changed == 'true' && steps.scope.outputs.driver_only == 'true'" in workflow
assert "needs.publication-check.outputs.drivers_changed == 'true' && needs.publication-check.outputs.driver_only == 'true'" in workflow
assert "github.event_name == 'push' && github.ref == 'refs/heads/main'" in workflow
assert "group: current-colorplus-publication" in workflow
assert "gate.verify(profile,data)" in workflow
print(json.dumps({'status':'PASS','exact_inline_cases':results,'fixed_driver_scope':['CPPAN.ZIP','YAMAHA.ZIP'],'network_or_release_writes':False}))
