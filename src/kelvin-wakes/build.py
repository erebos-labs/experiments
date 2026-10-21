from pathlib import Path
import json
root=Path(__file__).resolve().parent
data=json.loads((root/'data.json').read_text())
html=(root/'template.html').read_text().replace('__DATA__','window.WAKE_DATA='+json.dumps(data,separators=(',',':'))+';').replace('__APP__',(root/'app.js').read_text())
assert '__DATA__' not in html and '__APP__' not in html
(root/'index.html').write_text(html)
print('Built Kelvin wake measurement explorer')
