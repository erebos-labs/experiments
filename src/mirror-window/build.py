"""Build the self-contained optics page from local model/UI sources."""
from pathlib import Path
p=Path(__file__).resolve().parent
html=(p/'page.template.html').read_text()
for token,name in [('/*CORE*/','core.js'),('/*UI*/','ui.js')]:
    assert html.count(token)==1,token
    html=html.replace(token,(p/name).read_text())
(p/'index.html').write_text(html)
