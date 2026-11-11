"""Run real unittest discovery and retain per-case results plus console evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest

class Recorded(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.cases=[];self._started={};self._states={}
    def startTest(self,test):
        super().startTest(test);self._started[test.id()]=time.perf_counter();self._states[test.id()]={"status":"passed"}
    def addFailure(self,test,err):
        super().addFailure(test,err);self._states[test.id()]={"status":"failed","detail":self._exc_info_to_string(err,test)}
    def addError(self,test,err):
        super().addError(test,err);self._states[test.id()]={"status":"error","detail":self._exc_info_to_string(err,test)}
    def addSkip(self,test,reason):
        super().addSkip(test,reason);self._states[test.id()]={"status":"skipped","detail":reason}
    def addSubTest(self,test,subtest,err):
        super().addSubTest(test,subtest,err)
        if err:self._states[test.id()]={"status":"failed","detail":str(subtest)+"\n"+self._exc_info_to_string(err,test)}
    def stopTest(self,test):
        self.cases.append({"id":test.id(),"seconds":time.perf_counter()-self._started[test.id()],**self._states[test.id()]})
        super().stopTest(test)

def main():
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    suite=unittest.defaultTestLoader.discover(str(root/"tests"))
    start=time.perf_counter()
    with args.output.with_suffix(".log").open("w",encoding="utf-8") as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Recorded).run(suite)
    lib=Path(os.environ.get("MESH_CORE_LIBRARY",root/"python/mesh_testbed/mesh_core.dll"))
    data={"timestamp":datetime.now(timezone.utc).isoformat(),"platform":platform.platform(),"python":sys.version,
          "seconds":time.perf_counter()-start,"tests":result.testsRun,"successful":result.wasSuccessful(),
          "failures":len(result.failures),"errors":len(result.errors),"skipped":len(result.skipped),
          "library":str(lib),"library_sha256":hashlib.sha256(lib.read_bytes()).hexdigest() if lib.is_file() else None,
          "cases":result.cases}
    args.output.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    print({k:data[k] for k in ("tests","successful","failures","errors","skipped","seconds")})
    raise SystemExit(not result.wasSuccessful())

if __name__=="__main__":main()
