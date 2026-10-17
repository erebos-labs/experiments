"""Bind public numerical claims and no-referrer metadata to the generated page."""
from pathlib import Path
from html.parser import HTMLParser
import json, os, shutil, subprocess, sys, tempfile

root = Path(__file__).resolve().parents[1]

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None
        self.referrer = []
        self.in_head = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'head': self.in_head = True
        if tag == 'meta' and self.in_head and attrs.get('name') == 'referrer':
            self.referrer.append(attrs.get('content'))
        if tag == 'tr': self.row = []
        if tag == 'td': self.cell = ''

    def handle_data(self, data):
        if self.cell is not None: self.cell += data

    def handle_endtag(self, tag):
        if tag == 'head': self.in_head = False
        if tag == 'td': self.row.append(self.cell.strip()); self.cell = None
        if tag == 'tr' and self.row: self.rows.append(self.row); self.row = None

def validate(text, calculated):
    page = Page(); page.feed(text)
    assert page.referrer == ['no-referrer'], 'Missing or conflicting document referrer policy'
    assert len(page.rows) == 3
    expected = {int(row['frequency_Hz']): row for row in calculated if row['azimuth_deg'] == 30}
    for frequency, point, sphere in page.rows:
        row = expected[int(frequency.replace(',', '').removesuffix(' Hz'))]
        assert point == f"{row['point_receiver_delay_us']:.1f} μs"
        assert sphere == f"{row['sphere_phase_delay_us']:.1f} μs"

data = json.loads((root/'results/sphere-study.json').read_text(encoding='utf-8'))['key_rows']
text = (root/'index.html').read_text(encoding='utf-8')
validate(text, data)
for corrupted in [text.replace('409.0 μs', '410.0 μs'), text.replace('content="no-referrer"', 'content="origin"')]:
    try: validate(corrupted, data)
    except AssertionError: pass
    else: raise AssertionError('Negative control failed')

# Exercise explicit encoding and LF output even when input files have CRLF.
# This uses a bounded owned temporary directory, not another operating system.
with tempfile.TemporaryDirectory(dir=root/'results') as folder:
    copy = Path(folder); (copy/'src').mkdir(); (copy/'scripts').mkdir()
    for name in ['page.html', 'style.css', 'model.js', 'ui.js']:
        source = (root/'src'/name).read_text(encoding='utf-8')
        (copy/'src'/name).write_bytes(source.replace('\n', '\r\n').encode('utf-8'))
    shutil.copyfile(root/'scripts/build.py', copy/'scripts/build.py')
    result = subprocess.run([sys.executable, '-B', 'scripts/build.py'], cwd=copy, capture_output=True,
                            timeout=10, env=dict(os.environ, LC_ALL='C', PYTHONUTF8='0'))
    assert result.returncode == 0, result.stderr
    assert (copy/'index.html').read_bytes() == (root/'index.html').read_bytes()
    assert b'\r' not in (copy/'index.html').read_bytes()

report = {'status': 'PASS', 'sphere_rows': 3, 'negative_controls': 2,
          'ascii_locale_crlf_build_identical': True,
          'limits': 'Host subprocess and markup checks, not Windows/browser/referrer-network measurement.'}
(root/'results/page-tests.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))
