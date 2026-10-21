"""Build or check the standalone page with the standard library."""
from pathlib import Path
import sys
base=Path(__file__).resolve().parent
template=(base/'exhibit-template.html').read_text();script=(base/'exhibit.js').read_text()
assert template.count('__SCRIPT__')==1 and '</script' not in script.lower()
page=template.replace('__SCRIPT__',script)
if '--check' in sys.argv:
    assert (base/'index.html').read_text()==page
    print('PASS source/page equality')
else:
    (base/'index.html').write_text(page)
    print('Built index.html')
