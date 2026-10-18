from pathlib import Path
import argparse,hashlib,json
parser=argparse.ArgumentParser();parser.add_argument("--check",action="store_true");args=parser.parse_args()
p=Path(__file__).resolve().parent
s=(p/'page.html').read_text(encoding='utf-8')
for token,name,tag in [('<link rel="stylesheet" href="style.css">','style.css','style'),('<script src="model.js"></script>','model.js','script'),('<script src="app.js"></script>','app.js','script')]:
 if s.count(token)!=1:raise ValueError('Expected exactly one build token: '+token)
 s=s.replace(token,'<'+tag+'>'+(p/name).read_text(encoding='utf-8')+'</'+tag+'>')
if args.check:
 if (p/'index.html').read_bytes()!=s.encode('utf-8'):raise ValueError('Generated index.html is stale')
else:
 (p/'index.html').write_bytes(s.encode('utf-8'))
print(json.dumps({'output':'index.html','sha256':hashlib.sha256((p/'index.html').read_bytes()).hexdigest()}))
