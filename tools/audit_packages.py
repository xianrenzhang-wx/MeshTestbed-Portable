"""Audit package formats/exports and execute the Windows zip in a clean folder.
Requires optional pefile, pyelftools and macholib in the auditing environment.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
import pefile
from elftools.elf.elffile import ELFFile
from macholib.MachO import MachO

root=Path(__file__).resolve().parents[1]
out=root/'reports/release-2.1.0'
out.mkdir(parents=True,exist_ok=True)
expected=set(re.findall(r'\b(mc_\w+)\(', (root/'include/mesh_core.h').read_text()))
results=[]
for label,name in [('windows-x86_64','mesh_core.dll'),('linux-x86_64','libmesh_core.so'),('macos-arm64','libmesh_core.dylib'),('macos-x86_64','libmesh_core.dylib')]:
    path=root/'dist'/label/'mesh_testbed'/name
    binary=path.read_bytes();exports=set();deps=[]
    if label.startswith('windows'):
        pe=pefile.PE(str(path));exports={s.name.decode() for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
        deps=[s.dll.decode() for s in pe.DIRECTORY_ENTRY_IMPORT];arch=hex(pe.FILE_HEADER.Machine)
    elif label.startswith('linux'):
        with path.open('rb') as stream:
            elf=ELFFile(stream);arch=elf.header.e_machine
            exports={s.name for s in elf.get_section_by_name('.dynsym').iter_symbols() if s.entry.st_shndx!='SHN_UNDEF'}
            deps=[t.needed for t in elf.get_section_by_name('.dynamic').iter_tags() if t.entry.d_tag=='DT_NEEDED']
    else:
        mach=MachO(str(path));arch=mach.headers[0].header.cputype
        for header in mach.headers:
            for load,cmd,data in header.commands:
                if load.cmd in (0xc,0x18,0x80000018):deps.append(data.rstrip(b'\0').decode())
                if load.cmd==2:
                    strings=binary[cmd.stroff:cmd.stroff+cmd.strsize]
                    for i in range(cmd.nsyms):
                        strx,typ,sect,desc,value=struct.unpack_from('<IBBHQ',binary,cmd.symoff+16*i)
                        if typ&1 and typ&0xe==0xe and strx:
                            exports.add(strings[strx:].split(b'\0',1)[0].decode().lstrip('_'))
    missing=sorted(expected-exports)
    assert not missing,(label,missing)
    archive=root/'dist'/f'mesh-testbed-v2.1.0-{label}.zip'
    results.append(dict(target=label,architecture=arch,dependencies=deps,missing_exports=missing,
                        expected_exports=len(expected),binary_sha256=hashlib.sha256(binary).hexdigest(),
                        zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),zip_bytes=archive.stat().st_size))
env=dict(os.environ)
for key in ('PYTHONPATH','MESH_CORE_LIBRARY'):env.pop(key,None)
runs=[]
with tempfile.TemporaryDirectory(prefix='mesh-audit-') as tmp:
    with zipfile.ZipFile(root/'dist/mesh-testbed-v2.1.0-windows-x86_64.zip') as z:z.extractall(tmp)
    folder=Path(tmp)/'windows-x86_64'
    for args in (['analysis_demo.py'],['demo.py'],['manufacturing_demo.py','--layers','3','--output','analysis.json'],['-m','unittest','discover','-s','tests','-v']):
        p=subprocess.run([sys.executable,'-S',*args],cwd=folder,env=env,capture_output=True,text=True,timeout=60)
        runs.append(dict(command=['python','-S',*args],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
        assert p.returncode==0,p.stderr
    data=json.loads((folder/'analysis.json').read_text())
    assert abs(data['mass_properties']['mass']-1)<1e-12
    assert all(abs(s['area']-1)<1e-12 for s in data['sections'])
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
          for sub in ('src','include','python','tests') for p in (root/sub).rglob('*')
          if p.is_file() and p.suffix in ('.cpp','.h','.py')}
report=dict(platform=platform.platform(),packages=results,windows_extracted_runs=runs,source_sha256=manifest)
(out/'packages.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('Four binary formats/export tables checked; Windows extracted zip and examples passed.')
