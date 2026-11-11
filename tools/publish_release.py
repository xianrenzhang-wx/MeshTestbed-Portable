"""Package exact tested CI binaries and publish an English GitHub release.

Runs on a GitHub-hosted Linux runner. Authentication is supplied by GH_TOKEN;
tokens are never written to manifests or printed. No native library is rebuilt.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import pefile
from macholib.MachO import MachO

ROOT = Path(__file__).resolve().parents[1]
REPO = 'xianrenzhang-wx/MeshTestbed-Portable'
RUN = 42992820689
TESTED = '0525fb168bd513c37c41b200b8d6dceca98231d1'
TAG = 'v2.1.0'
TARGETS = {
    'windows-x86_64': ('mesh_core.dll', ['win_amd64']),
    'linux-x86_64': ('libmesh_core.so', ['manylinux_2_28_x86_64', 'manylinux_2_27_x86_64', 'manylinux_2_17_x86_64']),
    'macos-arm64': ('libmesh_core.dylib', ['macosx_15_0_arm64']),
    'macos-x86_64': ('libmesh_core.dylib', ['macosx_15_0_x86_64']),
}

def command(*args, capture=False):
    result = subprocess.run(args, cwd=ROOT, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout if capture else None

def gh_json(endpoint):
    return json.loads(command('gh','api',endpoint,capture=True))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def zip_folder(folder, output):
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                archive.write(path, (Path(folder.name)/path.relative_to(folder)).as_posix())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None

def inspect(path, target):
    if target.startswith('windows'):
        binary=pefile.PE(str(path))
        return {'architecture':hex(binary.FILE_HEADER.Machine),
                'system_libraries':[x.dll.decode() for x in binary.DIRECTORY_ENTRY_IMPORT]}
    if target.startswith('linux'):
        dynamic=command('readelf','-d',str(path),capture=True)
        versions=command('readelf','--version-info',str(path),capture=True)
        return {'architecture':'x86_64', 'system_libraries':re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic),
                'symbol_versions':sorted(set(re.findall(r'\b(?:GLIBC|GLIBCXX|CXXABI)_[\d.]+',versions)))}
    binary=MachO(str(path));deps=[]
    for header in binary.headers:
        for load, cmd, data in header.commands:
            if load.cmd in (0xc,0x18,0x80000018):deps.append(data.rstrip(b'\0').decode())
    return {'architecture':binary.headers[0].header.cputype,'system_libraries':deps}

def main():
    run=gh_json(f'repos/{REPO}/actions/runs/{RUN}')
    assert run['head_sha']==TESTED and run['conclusion']=='success'
    # Documentation/release changes are permitted; computational source must match the tested commit.
    command('git','diff','--exit-code',TESTED,'HEAD','--','src','include','python','CMakeLists.txt')
    stage=ROOT/'release-stage';assets=ROOT/'release-assets'
    stage.mkdir();assets.mkdir()
    evidence=stage/'test-evidence';evidence.mkdir()
    records=[]
    docs=['README.md','USAGE.md','API.md','GEOMETRY.md','DEPENDENCIES.md','CI_REPORT.md','VALIDATION.md','CHANGELOG.md','MeshTestbed Portable.md']
    for target,(library,platforms) in TARGETS.items():
        folder=stage/target
        command('gh','run','download',str(RUN),'--repo',REPO,'--name',f'mesh-testbed-{target}','--dir',str(folder))
        tests=evidence/target
        command('gh','run','download',str(RUN),'--repo',REPO,'--name',f'test-results-{target}','--dir',str(tests))
        result=json.loads((tests/'ci-results/suite.json').read_text())
        assert result['tests']==82 and result['successful'] and not any(result[k] for k in ['failures','errors','skipped'])
        native=folder/'mesh_testbed'/library
        assert sha(native)==result['library_sha256'],target
        record={'target':target,'tested_commit':TESTED,'run_id':RUN,'native_sha256':sha(native),
                'tests':82, **inspect(native,target)}
        for name in docs:
            shutil.copy2(ROOT/name,folder/name)
        reportdir=folder/'reports/release-2.1.0';reportdir.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'reports/release-2.1.0/TEST_REPORT.md',reportdir/'TEST_REPORT.md')
        shutil.copytree(tests/'ci-results',folder/'test-results')
        requirements='numpy==2.3.5\npolyscope==2.6.1\n'
        (folder/'requirements-display.txt').write_text(requirements)
        wheels=folder/'wheels';wheels.mkdir()
        args=[sys.executable,'-m','pip','download','--only-binary=:all:','--python-version','3.11','--implementation','cp','--abi','cp311','--dest',str(wheels)]
        for platform in platforms:args+=['--platform',platform]
        command(*args,'-r',str(folder/'requirements-display.txt'))
        record['optional_wheels']=[{'name':p.name,'sha256':sha(p)} for p in sorted(wheels.glob('*.whl'))]
        assert record['optional_wheels']
        (folder/'BINARY_DEPENDENCIES.json').write_text(json.dumps(record,indent=2))
        (folder/'START_HERE.md').write_text('# Start here\n\nRead USAGE.md. Run python demo.py or python analysis_demo.py.\nCore computation needs Python but no third-party Python packages.\nOptional display wheels are for CPython 3.11 on this platform only.\nSee DEPENDENCIES.md for system runtimes and graphics requirements.\n')
        # Remove example outputs and bytecode from the artifact; preserve the tested binary exactly.
        for path in folder.rglob('*.pyc'):path.unlink()
        output=folder/'analysis.json'
        if output.exists():output.unlink()
        for path in folder.rglob('*.md'):
            assert not re.search('[\u4e00-\u9fff]',path.read_text(encoding='utf-8-sig')),path
        files=sorted(p for p in folder.rglob('*') if p.is_file())
        (folder/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(folder).as_posix()}\n' for p in files))
        zip_folder(folder,assets/f'MeshTestbed-Portable-2.1.0-{target}.zip')
        records.append(record)
    # Combine the four identical platform folders into one convenient archive.
    with zipfile.ZipFile(assets/'MeshTestbed-Portable-2.1.0-All-Platforms.zip','w',zipfile.ZIP_DEFLATED) as combined:
        for target in TARGETS:
            with zipfile.ZipFile(assets/f'MeshTestbed-Portable-2.1.0-{target}.zip') as package:
                for name in package.namelist():combined.writestr(name,package.read(name))
        combined.writestr('START_HERE.md','# MeshTestbed Portable 2.1.0\n\nChoose the directory matching your OS and Python architecture, then read USAGE.md.\n')
    zip_folder(evidence,assets/'MeshTestbed-Portable-2.1.0-Test-Evidence.zip')
    (assets/'RELEASE_MANIFEST.json').write_text(json.dumps({'version':'2.1.0','tested_commit':TESTED,'run_id':RUN,'packages':records},indent=2))
    sums=''.join(f'{sha(p)}  {p.name}\n' for p in sorted(assets.iterdir()) if p.is_file())
    (assets/'SHA256SUMS.txt').write_text(sums)
    notes=ROOT/'release-notes.md'
    notes.write_text('''# MeshTestbed Portable 2.1.0

Python interfaces backed by a portable C++ geometry library.

## Downloads

Choose the ZIP for Windows x86_64, Linux x86_64, macOS Apple Silicon or macOS Intel.
The All-Platforms ZIP contains all four. Each ZIP includes the tested dynamic library,
Python modules, three examples, English documentation, test fixtures/results, C header,
dependency metadata, license notices and optional CPython 3.11 display wheels.

Core computation requires Python and system runtimes; neither Python nor OS/graphics
drivers are bundled. Optional display dependencies can be installed offline on CPython
3.11 using the included wheels. See USAGE.md and DEPENDENCIES.md after extraction.

## Validation and provenance

All four native targets passed 82 tests with zero failures/errors/skips in
[Actions run 42992820689](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/actions/runs/42992820689).
Native binaries are copied unchanged from that run and verified against recorded SHA256s.
English documentation and optional wheels were added afterwards. No native library was rebuilt.
See RELEASE_MANIFEST.json and the Test-Evidence ZIP. SHA256SUMS.txt covers all release assets.

Tested environments: Windows Server 2025, Ubuntu 22.04, macOS 15 ARM64 and Intel,
with CPython 3.11. Broader minimum-OS compatibility and interactive graphics are not
certified by this workflow. These are native CI artifacts, not the earlier Zig builds.

## Features

Mesh loading and topology; geometric/mass properties; affine transforms; nearest
points and signed distances; containment/collision; sections/slices; tetrahedron
classification and barycentric coordinates; local mesh properties; cubic/bicubic Bézier sampling.
''')
    # Publishing is explicitly requested. Keep a draft until every asset uploads successfully.
    command('gh','release','create',TAG,'--repo',REPO,'--target',os.environ['GITHUB_SHA'],
            '--title','MeshTestbed Portable 2.1.0','--notes-file',str(notes),'--draft')
    command('gh','release','upload',TAG,'--repo',REPO,*[str(p) for p in sorted(assets.iterdir())])
    command('gh','release','edit',TAG,'--repo',REPO,'--draft=false','--latest')
    print('Published tested native artifacts with English documentation.')

if __name__=='__main__':main()
