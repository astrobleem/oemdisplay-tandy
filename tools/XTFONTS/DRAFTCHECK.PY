import hashlib, json, os
from pathlib import Path
out = Path('dist')
names = {'WINXT720.IMG','WINXT720.ZIP','WXTTOOLS.ZIP','README.TXT','BUILD.JSON',
    'PKGSUMS.TXT','XT-PIXELS-R10-SOURCE.zip','XT-PIXELS-R10-FONTS.zip',
    'XT-PIXELS-R10-PREVIEWS.zip','FONT-LICENSE.TXT','START-HERE.TXT',
    'QUALIFY.JSON','RELEASE.JSON','SHA256SUMS'}
assert {p.name for p in out.iterdir()} == names
assert all(p.is_file() and not p.is_symlink() for p in out.iterdir())
q = json.loads((out/'QUALIFY.JSON').read_bytes())
r = json.loads((out/'RELEASE.JSON').read_bytes())
snapshot = json.loads((out/'BUILD.JSON').read_bytes())
assert q['publication_allowed'] is True and q['native_package_qualified'] is True
assert r['publication_allowed'] is True and r['native_binary_identity_preserved'] is True
assert r['Windows_support_included'] is False
assert q['publication_commit'] == r['publication_commit'] == os.environ['SOURCE_SHA']
assert q['release_tag'] == r['release_tag'] == os.environ['RELEASE_TAG']
assert snapshot['publication_allowed'] is False and snapshot['native_package_qualified'] is False
assert snapshot['windows_support_included'] is False and snapshot['kind'] == 'original-font-test-candidate'
assert snapshot['image_bytes'] == (out/'WINXT720.IMG').stat().st_size == 737280
assert hashlib.sha256((out/'WINXT720.IMG').read_bytes()).hexdigest() == q['disk_sha256']
assert q['native_default_transaction']['sha_blocks'] == [0,0]
assert q['native_default_transaction']['compared_bytes'] == [0]
assert all(q['native_verify_transaction']['sha_blocks'])
for n,h in q['package_sha256'].items():
    assert n in {'WINXT720.IMG','WINXT720.ZIP','WXTTOOLS.ZIP','BUILD.JSON','README.TXT','SHA256SUMS'}
    name = 'PKGSUMS.TXT' if n == 'SHA256SUMS' else n
    assert hashlib.sha256((out/name).read_bytes()).hexdigest() == h
assert set(r['assets_sha256']) == names - {'RELEASE.JSON','SHA256SUMS'}
for n,h in r['assets_sha256'].items():
    assert hashlib.sha256((out/n).read_bytes()).hexdigest() == h
expected = ''.join(hashlib.sha256((out/n).read_bytes()).hexdigest()+'  '+n+'\n'
    for n in sorted(names-{'SHA256SUMS'}))
assert (out/'SHA256SUMS').read_text() == expected
