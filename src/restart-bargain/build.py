"""Build the self-contained finite search page from local sources."""
from pathlib import Path
p=Path(__file__).resolve().parent
html=(p/'page.template.html').read_text()
if html.count('/* CORE_JS */')!=1:raise ValueError('Expected one core token')
(p/'index.html').write_text(html.replace('/* CORE_JS */',(p/'core.js').read_text()))
