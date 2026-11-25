"""Check source paths, known private font blobs and common credential patterns.

This is a bounded release check, not a licence or complete secret audit.
"""
from pathlib import Path
import hashlib
import json
import subprocess

from font_assets import ROOT
from private_files import private_path, secret_content


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def secret_blobs(ids):
    """Batch reads keep index/history scanning fast and never print blob data."""
    ids = sorted(set(ids))
    if not ids:
        return set()
    metadata = subprocess.check_output(['git', 'cat-file', '--batch-check'],
                                       input=('\n'.join(ids) + '\n').encode(), cwd=ROOT)
    # Gitlinks may refer to objects held only in another repository.
    blobs = []
    for line in metadata.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[1] == b'blob':
            blobs.append(fields[0].decode())
    ids = blobs
    if not ids:
        return set()
    output = subprocess.check_output(['git', 'cat-file', '--batch'],
                                     input=('\n'.join(ids) + '\n').encode(), cwd=ROOT)
    found = set()
    offset = 0
    for _ in ids:
        end = output.index(b'\n', offset)
        oid, kind, size = output[offset:end].split()
        offset = end + 1
        size = int(size)
        if secret_content(output[offset:offset + size]):
            found.add(oid.decode())
        offset += size + 1
    return found


candidates = set(git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')) - {''}
findings = []
font_suffixes = {'.ttf', '.otf', '.woff', '.woff2', '.eot'}


def forbidden(name):
    path = Path(name)
    return (name.startswith(('.local/', 'dist/', 'node_modules/', 'app/assets/private-fonts/',
                                    'explorations/', 'docs/research/', 'docs/articles/'))
            or private_path(name) or path.suffix.lower() in {'.wgt', '.dll', '.pdb', '.exe'}
            or any(part.lower() in {'bin', 'obj'} for part in path.parts)
            or (path.name.startswith('PP') and path.suffix.lower() in font_suffixes))


public_fonts = {'app/assets/manrope.woff2': 'e310b55a7fd9677f5e3555e6c6c4d064fa1f1d24393f0ddbe217cea12a8c432f'}
sources = json.loads((ROOT / 'app/assets/fonts/SOURCES.json').read_text())
for record in sources:
    if Path(record['file']).suffix.lower() in font_suffixes:
        public_fonts['app/assets/fonts/' + record['file']] = record['sha256']

for name in sorted(candidates):
    if forbidden(name):
        findings.append('Private/generated source path: ' + name)
    path = ROOT / name
    if path.is_symlink():
        findings.append('Symlink in public source: ' + name)
        continue
    if not path.is_file():
        continue
    if path.suffix.lower() in font_suffixes:
        if name not in public_fonts or hashlib.sha256(path.read_bytes()).hexdigest() != public_fonts[name]:
            findings.append('Unrecognised or changed public font: ' + name)
    # Print filenames only, so a failing check does not leak a matched credential.
    if secret_content(path.read_bytes()):
        findings.append('Credential pattern: ' + name)

index = []
for entry in git('ls-files', '--stage', '-z').decode().split('\0'):
    if not entry:
        continue
    metadata, name = entry.split('\t', 1)
    mode, oid, stage = metadata.split()
    index.append((name, oid))
    if mode == '120000' or forbidden(name):
        findings.append('Private/generated or symlink path in Git index: ' + name)

history = set()
# rev-list --objects records only one path per object. A later rename could hide
# a private filename, so inspect each distinct committed tree with NUL records.
for tree in sorted(set(git('log', '--all', '--format=%T').decode().splitlines())):
    for entry in git('ls-tree', '-r', '-z', tree).decode().split('\0'):
        if not entry:
            continue
        metadata, name = entry.split('\t', 1)
        mode, kind, oid = metadata.split()
        if forbidden(name):
            findings.append('Private/generated path in reachable Git history: ' + name)
        if mode == '120000':
            findings.append('Symlink in reachable Git history: ' + name)
        if kind == 'blob':
            history.add((name, oid))

object_ids = {oid for _, oid in history}
unsafe_blobs = secret_blobs(object_ids | {oid for _, oid in index})
for name, oid in index:
    if oid in unsafe_blobs:
        findings.append('Credential pattern in Git index: ' + name)
for name, oid in history:
    if oid in unsafe_blobs:
        findings.append('Credential pattern in reachable Git history: ' + name)
private_root = ROOT / '.local/research/font-candidates'
private_fonts = [p for p in private_root.rglob('*') if p.is_file() and p.name.startswith('PP') and p.suffix.lower() in font_suffixes]
for path in private_fonts:
    if git('hash-object', str(path)).decode().strip() in object_ids:
        findings.append('Known proprietary font bytes in Git history: ' + path.name)

for name in ['app/assets/fonts/geist/OFL.txt', 'app/assets/fonts/newsreader/OFL.txt', 'app/assets/fonts/orbitron/OFL.txt', 'app/assets/fonts/roboto/OFL.txt', 'app/assets/manrope-OFL.txt']:
    if not (ROOT / name).is_file():
        findings.append('Missing public font licence: ' + name)

# Every file recorded in SOURCES.json (fonts and licence texts) must have exactly the recorded
# upstream size and SHA-256 in the working copy: these are the bytes a public export ships.
# The Manrope licence has no recorded upstream source and is only required to exist (above).
for record in sources:
    name = 'app/assets/fonts/' + record['file']
    path = ROOT / name
    if not path.is_file():
        findings.append('Missing file recorded in SOURCES.json: ' + name)
        continue
    data = path.read_bytes()
    # Font binaries can contain CR LF bytes by chance; the hint applies to licence texts only.
    hint = ' (CRLF line endings; see .gitattributes)' if b'\r\n' in data and Path(name).suffix.lower() not in font_suffixes else ''
    if len(data) != record['bytes']:
        findings.append('Size differs from SOURCES.json, ' + str(len(data)) + ' instead of ' + str(record['bytes']) + ' bytes' + hint + ': ' + name)
    elif hashlib.sha256(data).hexdigest() != record['sha256']:
        findings.append('SHA-256 differs from SOURCES.json' + hint + ': ' + name)

# .gitattributes must keep Git from converting fonts, images and licence texts, and must give
# text files LF line endings on every platform (Windows checkouts otherwise gain CRLF).
licences = {'app/assets/manrope-OFL.txt'} | {'app/assets/fonts/' + r['file'] for r in sources if Path(r['file']).name == 'OFL.txt'}
binary_suffixes = font_suffixes | {'.jpg', '.jpeg', '.png', '.webp'}
text_suffixes = {'.js', '.mjs', '.css', '.html', '.json', '.md', '.py', '.sh', '.svg', '.xml', '.yml', '.cs', '.in', '.csproj', '.txt'}
present = sorted(name for name in candidates if (ROOT / name).is_file() and not (ROOT / name).is_symlink())
attributes = {}
if present:
    fields = subprocess.check_output(['git', 'check-attr', '-z', '--stdin', 'text', 'eol', 'binary'],
                                     input=('\0'.join(present) + '\0').encode(), cwd=ROOT).decode().split('\0')
    for i in range(0, len(fields) - 2, 3):
        attributes.setdefault(fields[i], {})[fields[i + 1]] = fields[i + 2]
if not (ROOT / '.gitattributes').is_file():
    findings.append('Missing .gitattributes: line endings and binary files are not protected')
unmarked_binary, unmarked_text, crlf_text = [], [], []
for name in present:
    attr, suffix = attributes.get(name, {}), Path(name).suffix.lower()
    if name in licences:
        if attr.get('text') != 'unset':
            findings.append('Licence text is not protected from line-ending conversion (-text): ' + name)
    elif suffix in binary_suffixes:
        if attr.get('binary') != 'set' or attr.get('text') != 'unset':
            unmarked_binary.append(name)
    elif suffix in text_suffixes or name.startswith('.githooks/') or name in {'.gitignore', '.gitattributes', 'LICENSE'}:
        if attr.get('text') not in {'set', 'auto'} or attr.get('eol') != 'lf':
            unmarked_text.append(name)
        elif b'\r\n' in (ROOT / name).read_bytes():
            crlf_text.append(name)


def grouped(message, names):
    """One finding per category, so a missing rule set cannot hide other findings."""
    if names:
        findings.append(message + ' (' + str(len(names)) + '): ' + ', '.join(names[:5]) + (', …' if len(names) > 5 else ''))


grouped('Binary files not marked binary in .gitattributes', unmarked_binary)
grouped('Text files without eol=lf in .gitattributes', unmarked_text)
grouped('Text files with CRLF line endings in the working copy', crlf_text)

if findings:
    raise SystemExit('\n'.join(sorted(set(findings))[:20]) + '\nTotal findings: ' + str(len(set(findings))))
print('Public-source checks passed for ' + str(len(candidates)) + ' candidate files and reachable Git paths.')
print('Compared ' + str(len(private_fonts)) + ' local proprietary font files with reachable Git objects.')
if not private_fonts:
    print('No private fonts on this machine; known-font byte comparison was skipped.')
print('Also review third-party notices, full history, GitHub logs and release assets before publication.')
