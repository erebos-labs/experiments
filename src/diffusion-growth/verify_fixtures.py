"""Verify declared fixture identity and optionally replay the tested toolchain."""

if not __debug__:
    raise RuntimeError('Validation requires Python without -O or PYTHONOPTIMIZE')

from pathlib import Path
import argparse,hashlib,json,subprocess
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--replay',action='store_true');a=p.parse_args()
m=json.loads((R/'PROVENANCE.json').read_text())
for name,expected in m['fixture_sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==expected,name
if a.replay:
 subprocess.run(['node','ensemble.js'],cwd=R,check=True,timeout=120)
 expected=json.loads((R/'data/ensemble.json').read_text());actual=json.loads((R/'output/ensemble.json').read_text())
 for field in ['seeds','target','summary','paired','rows']:assert actual[field]==expected[field],field
 assert json.loads((R/'output/samples.json').read_text())==json.loads((R/'data/samples.json').read_text())
 assert len(json.loads((R/'output/probes.json').read_text()))==6
print('PASS declared fixture hashes'+(' and tested-toolchain numerical replay' if a.replay else ''))
