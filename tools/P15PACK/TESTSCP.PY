"""Exercise the exact inline scope step without network or release writes."""
import hashlib,json,os,tempfile,textwrap
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[2]
workflow=(ROOT/'.github/workflows/pc1512.yml').read_text()
start=workflow.index('          import hashlib,json,os,urllib.request\n')
end=workflow.index('          PYCODE',start)
code=compile(textwrap.dedent(workflow[start:end]),'pc1512.yml:scope','exec')
data=b'qualified-PC1512-packet'
identity={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
row={'name':'PC1512.ZIP','size':len(data),'digest':'sha256:'+identity['sha256']}
def fixture(pc_rows, catalog_identity=identity, missing=(), stale_sums=False):
    record=json.dumps({'assets':{'PC1512.ZIP':catalog_identity}}).encode()
    sums=(identity['sha256']+'  PC1512.ZIP\n'+('0'*64 if stale_sums else hashlib.sha256(record).hexdigest())+'  CURRENT.JSN\n').encode()
    bodies={'CURRENT.JSN':record,'CURRENT.SHA':sums}
    rows=pc_rows+[{'name':name,'size':len(body),'digest':'sha256:'+hashlib.sha256(body).hexdigest(),'browser_download_url':'https://example.invalid/'+name} for name,body in bodies.items() if name not in missing]
    return rows,bodies
cases=[('same',fixture([row]),False),('different',fixture([dict(row,size=len(data)+1)]),True),
       ('missing-pc',fixture([]),True),('duplicate-pc',fixture([row,row]),'error'),
       ('pc-uploaded-catalog-old',fixture([row],dict(identity,bytes=1)),True),
       ('catalog-missing',fixture([row],missing=('CURRENT.JSN',)),True),
       ('sums-missing',fixture([row],missing=('CURRENT.SHA',)),True),
       ('sums-incomplete',fixture([row],stale_sums=True),True)]
results=[]
with tempfile.TemporaryDirectory(prefix='pc1512-scope-') as temp:
    tmp=Path(temp);(tmp/'current').mkdir();(tmp/'current/PC1512.ZIP').write_bytes(data)
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
                    assert output.read_text()=='changed='+str(expected).lower()+'\n',name
            results.append(name)
    finally:os.chdir(ROOT)
assert "if: steps.scope.outputs.changed == 'true'" in workflow
assert "needs.publication-check.outputs.pc1512_changed == 'true'" in workflow
print(json.dumps({'status':'PASS','exact_inline_cases':results,'PC1512_publisher_guards':'unchanged','network_or_release_writes':False}))
