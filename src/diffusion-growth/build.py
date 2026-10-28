from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent
s=(p/'template.html').read_text(encoding='utf-8')
data={'samples':json.loads((p/'data/samples.json').read_text(encoding='utf-8')),'ensemble':{'summary':json.loads((p/'data/ensemble.json').read_text(encoding='utf-8'))['summary']}}
for token,text in [('/*CSS*/',(p/'style.css').read_text(encoding='utf-8')),('/*MODEL*/',(p/'model.js').read_text(encoding='utf-8')),('/*UI*/',(p/'ui.js').read_text(encoding='utf-8')),('/*DATA*/',json.dumps(data,separators=(',',':')))]:
 if s.count(token)!=1:raise ValueError('Expected exactly one build token: '+token)
 s=s.replace(token,text)
(p/'index.html').write_text(s,encoding='utf-8')
print(json.dumps({'output':'index.html','sha256':hashlib.sha256((p/'index.html').read_bytes()).hexdigest()}))
