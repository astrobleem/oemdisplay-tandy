"""Exercise the exact inline scope step without network or release writes."""
import hashlib,importlib.machinery,json,os,tempfile,textwrap
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[2]
workflow=(ROOT/'.github/workflows/colorplus.yml').read_text()
start=workflow.index('          import hashlib,importlib.machinery,json,os,urllib.request\n')
end=workflow.index('          PYCODE',start)
source=textwrap.dedent(workflow[start:end]).replace("'tools/CPPACK/CPPUB.PY'",repr(str(ROOT/'tools/CPPACK/CPPUB.PY')))
code=compile(source,'colorplus.yml:scope','exec')
M=importlib.machinery.SourceFileLoader('scope_packets',str(ROOT/'tools/CPPACK/CPPUB.PY')).load_module()
data=M.P.archive({'PCP3216.DRV':b'qualified fixed','PANCFG.EXE':b'current helper'})
identity={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
row={'name':'CPPAN.ZIP','size':len(data),'digest':'sha256:'+identity['sha256'],'browser_download_url':'https://example.invalid/CPPAN.ZIP'}
def fixture(pc_rows, catalog_identity=identity, missing=(), stale_sums=False, previous=data):
    record=json.dumps({'assets':{'CPPAN.ZIP':catalog_identity}}).encode()
    sums=(identity['sha256']+'  CPPAN.ZIP\n'+('0'*64 if stale_sums else hashlib.sha256(record).hexdigest())+'  CURRENT.JSN\n').encode()
    bodies={'CURRENT.JSN':record,'CURRENT.SHA':sums}
    rows=pc_rows+[{'name':name,'size':len(body),'digest':'sha256:'+hashlib.sha256(body).hexdigest(),'browser_download_url':'https://example.invalid/'+name} for name,body in bodies.items() if name not in missing]
    bodies['CPPAN.ZIP']=previous
    return rows,bodies
cases=[('same',fixture([row]),False),('different',fixture([dict(row,size=len(data)+1)]),'error'),
       ('missing-pc',fixture([]),True),('duplicate-pc',fixture([row,row]),'error'),
       ('pc-uploaded-catalog-old',fixture([row],dict(identity,bytes=1)),True),
       ('catalog-missing',fixture([row],missing=('CURRENT.JSN',)),True),
       ('sums-missing',fixture([row],missing=('CURRENT.SHA',)),True),
       ('sums-incomplete',fixture([row],stale_sums=True),True)]
def prior(files):
    previous=M.P.archive(files);pin=M.P.identity(previous)
    return fixture([dict(row,size=pin['bytes'],digest='sha256:'+pin['sha256'])],previous=previous)
cases.extend([('fixed-driver',prior({'PCP3216.DRV':b'old fixed','PANCFG.EXE':b'current helper'}),True),
              ('shared-helper',prior({'PCP3216.DRV':b'qualified fixed','PANCFG.EXE':b'old helper'}),True),
              ('member-closure',prior({'PCP3216.DRV':b'qualified fixed'}),True)])
results=[]
with tempfile.TemporaryDirectory(prefix='colorplus-scope-') as temp:
    tmp=Path(temp);(tmp/'current').mkdir();(tmp/'current/CPPAN.ZIP').write_bytes(data)
    try:
        os.chdir(tmp)
        for name,(rows,bodies),expected in cases:
            output=tmp/(name+'.out')
            payload=json.dumps({'assets':rows}).encode()
            def respond(request,timeout):
                assert timeout==60
                body=payload if request.full_url.startswith('https://api.github.com/') else bodies[request.full_url.rsplit('/',1)[1]]
                response=mock.Mock();response.read.return_value=body;return response
            with mock.patch.dict(os.environ,{'GITHUB_OUTPUT':str(output)}),mock.patch('urllib.request.urlopen',side_effect=respond):
                try:exec(code,{})
                except ValueError:
                    assert expected=='error',name
                    assert not output.exists(),name
                else:
                    driver_only=name not in ('shared-helper','member-closure')
                    assert output.read_text()=='changed='+str(expected).lower()+'\ndriver_only='+str(driver_only).lower()+'\n',name
            results.append(name)
    finally:os.chdir(ROOT)
assert "if: steps.scope.outputs.changed == 'true' && steps.scope.outputs.driver_only == 'true'" in workflow
assert "needs.publication-check.outputs.colorplus_changed == 'true' && needs.publication-check.outputs.driver_only == 'true'" in workflow
print(json.dumps({'status':'PASS','exact_inline_cases':results,'ColorPlus_publisher_guards':'unchanged','network_or_release_writes':False}))
