"""Independent stdlib parser: does not import the JS writer or its VLQ code."""
import json,struct,sys,pathlib,hashlib

def parse(path):
 b=path.read_bytes();assert b[:4]==b'MThd';hlen,=struct.unpack('>I',b[4:8]);assert hlen==6
 fmt,tracks,ppq=struct.unpack('>HHH',b[8:14]);assert (fmt,tracks,ppq)==(0,1,480)
 assert b[14:18]==b'MTrk';length,=struct.unpack('>I',b[18:22]);assert len(b)==22+length
 p=22;tick=0;active={};onsets=[];durations=[];tempo=[];eot=False;running=None
 def vlq():
  nonlocal p
  value=0
  for i in range(4):
   assert p<len(b);x=b[p];p+=1;value=(value<<7)|(x&127)
   if x<128:return value
  raise AssertionError('VLQ exceeds four bytes')
 while p<len(b):
  tick+=vlq();status=b[p]
  if status>=128:p+=1
  else:assert running is not None;status=running
  if status==255:
   running=None;kind=b[p];p+=1;n=vlq();data=b[p:p+n];assert len(data)==n;p+=n
   if kind==81:assert n==3;tempo.append((tick,int.from_bytes(data,'big')))
   if kind==88:assert data==bytes([4,2,24,8])
   if kind==47:assert n==0 and p==len(b);eot=True
  elif status<240:
   running=status;kind=status&240;ch=status&15;n=1 if kind in (192,208) else 2;data=b[p:p+n];p+=n;assert len(data)==n and all(x<128 for x in data)
   assert kind in (128,144);note,vel=data;key=(ch,note)
   if kind==144 and vel:
    assert key not in active,('ambiguous overlapping pitch',key,tick);active[key]=tick;onsets.append((tick,ch,note,vel))
   else:
    assert key in active;start=active.pop(key);assert tick>start;durations.append(tick-start)
  else:raise AssertionError('Unexpected system message')
 assert eot and not active and tick==32*ppq and tempo==[(0,461538)]
 expected=json.loads(path.with_name(path.stem+'-events.json').read_text())
 # Positive beat positions avoid Python half-even tie differences; non-ties checked.
 intended=sorted((int(e['beat']*ppq+.5),e['channel'],e['note'],e['velocity']) for e in expected)
 assert sorted(onsets)==intended
 return {'file':path.name,'bytes':len(b),'notes':len(onsets),'tempo_us_per_quarter':tempo[0][1],'effective_bpm':60000000/tempo[0][1],'ppq':ppq,'end_tick':tick,'min_note_ticks':min(durations),'max_note_ticks':max(durations),'dangling_notes':len(active),'sha256':hashlib.sha256(b).hexdigest()}

root=pathlib.Path(sys.argv[1]);results=[parse(p) for p in sorted(root.glob('*.mid'))];assert len(results)==6
print(json.dumps(results,indent=2));(root/'midi-parser-results.json').write_text(json.dumps(results,indent=2)+'\n')
