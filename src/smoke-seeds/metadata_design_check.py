"""Check a published, minimal GEO-derived design table; no expression data."""
from pathlib import Path
from collections import Counter,defaultdict
import csv
HERE=Path(__file__).resolve().parent
with (HERE/'data/geo-sample-design.csv').open(newline='') as f:rows=list(csv.DictReader(f))
assert len(rows)==len({r['accession'] for r in rows})==28
groups=defaultdict(Counter)
for r in rows:
    groups[(r['time'],r['treated'])][r['treated_channel']]+=1
    assert [r['Cy3_treatment'],r['Cy5_treatment']].count('control')==1
assert len(groups)==7 and all(c=={'1':2,'2':2} for c in groups.values())
assert next(r for r in rows if r['accession']=='GSM852502')['treated_channel']=='1'
assert next(r for r in rows if r['accession']=='GSM852504')['treated_channel']=='2'
print('PASS 28 records, seven comparisons, balanced dye orientations. Metadata only.')
