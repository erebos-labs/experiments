"""Reproduce scientific fixture bytes; run with -B. Never writes during import."""

if not __debug__:
    raise RuntimeError('Validation requires Python without -O or PYTHONOPTIMIZE')

from pathlib import Path
import argparse,hashlib,json,random
from ice import domain_tables,domain_sample,asm_formula
from loop_fixture import canonical_rows
ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--loop-output',type=Path);a=parser.parse_args()
    if a.loop_output:
        rows=[json.loads(line)for line in a.loop_output.read_text().splitlines()]
        rows=canonical_rows(rows,allow_timing=True)
        payload=''.join(json.dumps({k:v for k,v in row.items()if k!='seconds'},sort_keys=True,separators=(',',':'))+'\n'for row in rows)
        target=ROOT/'data/loops.jsonl'
    else:
        n=14;seed=1967;_,backward=domain_tables(n);assert backward[0][(1<<n)-1]==asm_formula(n)
        rng=random.Random(seed);samples=[]
        for _ in range(6):
            h,v=domain_sample(n,backward,rng);samples.append({'horizontal':h,'vertical':v})
        value={'n':n,'seed':seed,'generator':'generate_fixtures.py; exact integer-weight row sampling','generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'samples':samples}
        payload=json.dumps(value,indent=2)+'\n';target=ROOT/'data/domain-samples.json'
    if a.check:
        assert target.read_bytes()==payload.encode('utf-8'),'Canonical fixture differs'
    else:
        target.write_bytes(payload.encode('utf-8'))
    print(json.dumps({'fixture':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(payload.encode()).hexdigest(),'status':'PASS'}))
if __name__=='__main__':main()
