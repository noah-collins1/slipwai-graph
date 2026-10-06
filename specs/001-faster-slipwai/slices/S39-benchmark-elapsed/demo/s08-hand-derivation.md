# S08-scoped-mutation derived by hand (iteration 24, demo 1)

## git moments (quickstart step 2, run in the scratch clone at 13b7301)
added to story-split:  d3a0926 1790994849 2026-10-02T21:34:09-05:00
S04 register row:      b31c864 1791137585 2026-10-04T13:13:05-05:00   -> ready (the later)
S08 register row:      c88fe2f 1791271018 2026-10-06T02:16:58-05:00   -> accepted
merge (first parent):  3138416 1791256484 2026-10-05T22:14:44-05:00
S06 register row:      1d6cc17 1791256426 2026-10-05T22:13:46-05:00

## brackets, cruise log and causes (derive.py, independent of measures.py)
```python
# Hand derivation of S08's elapsed, stage time and waiting by cause, independent of measures.py.
# Inputs: git moments derived with `git log` (printed above), the S08 record's brackets, specs/cruise-log.jsonl.
import json, datetime as dt
def t(s): return int(dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
def iso(n): return dt.datetime.fromtimestamp(n, dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
D='/tmp/s39/demo/'
ready=1791137585      # b31c864, S04's register row (later than d3a0926, S08 added to story-split)
accepted=1791271018   # c88fe2f, S08's register row
merged=1791256484     # 3138416, first-parent merge of slice/S08-scoped-mutation
s06=1791256426        # 1d6cc17, S06's register row
rec=json.load(open(D+'specs/001-faster-slipwai/slices/S08-scoped-mutation/benchmark.json'))
br=[]
for e in rec['stages']:
    a=t(e['started']); b=t(e['ended']) if e.get('ended') else None
    print(f"{e['stage']:10} {e['started']} {e.get('ended')} seconds={e.get('seconds')} outcome={(e.get('signals') or {}).get('outcome')}")
    br.append((e['stage'],a,b,e.get('seconds')))
stage=sum(s for *_,s in br); print('entries',len(br),'stage time (sum seconds)',stage)
def union(iv):
    iv=sorted(tuple(x) for x in iv); out=[]
    for a,b in iv:
        if out and a<=out[-1][1]: out[-1][1]=max(out[-1][1],b)
        else: out.append([a,b])
    return out
def length(iv): return sum(b-a for a,b in iv)
def clip(iv,lo,hi): return [(max(a,lo),min(b,hi)) for a,b in iv if min(b,hi)>max(a,lo)]
def minus(iv,cut):
    res=[]
    for a,b in iv:
        segs=[(a,b)]
        for c,d in cut:
            nxt=[]
            for x,y in segs:
                if d<=x or c>=y: nxt.append((x,y)); continue
                if x<c: nxt.append((x,c))
                if d<y: nxt.append((d,y))
            segs=nxt
        res+=segs
    return res
W=union(clip([(a,b) for _,a,b,_ in br],ready,accepted)); worked=length(W)
print('worked (union in [ready,accepted])',worked, 'overlap among brackets:', stage-length(union([(a,b) for _,a,b,_ in br])))
# integration: merge -> accepted, less S08 brackets
integ=minus([(merged,accepted)],W); print('integration',length(integ), 'brackets inside:',[(s,iso(a),iso(b)) for s,a,b,_ in br if a>=merged])
# dependency: last accepted demo end -> S06's row, less S08 brackets
demo_acc=[b for s,a,b,_ in br if s=='demo'][-1]
dep=minus([(demo_acc,s06)],W); print('demo accepted',iso(demo_acc),'dependency',length(dep), 'window',s06-demo_acc)
claimed=union(W+integ+dep)
# parks
rows=[json.loads(l) for l in open(D+'specs/cruise-log.jsonl')]
parks=[]
for i,r in enumerate(rows):
    if r['last_line'].endswith('stopped: human') or r['last_line'].startswith('cruise: parked:'):
        nxt=t(rows[i+1]['started']) if i+1<len(rows) else accepted
        parks.append((t(r['ended']),nxt))
P=minus(clip(parks,ready,accepted),claimed); person=length(P)
print('parks', [(iso(a),iso(b),b-a) for a,b in clip(parks,ready,accepted)], 'person (cause unrecorded)',person)
claimed=union(claimed+P)
start=max(ready,t(rows[0]['started']))
worker=length(minus([(start,accepted)],claimed))
print('worker',worker)
elapsed=accepted-ready
unattr=elapsed-worked-length(integ)-length(dep)-worker
print('elapsed',elapsed,'unattributed (incl. person)',unattr,'sum check',worked+length(integ)+length(dep)+0+worker+unattr==elapsed)
```
```
gaps       2026-10-05T16:41:44Z 2026-10-05T16:59:32Z seconds=1068 outcome=None
plan       2026-10-05T17:03:20Z 2026-10-05T17:11:56Z seconds=516 outcome=None
tasks      2026-10-05T17:11:59Z 2026-10-05T17:16:28Z seconds=269 outcome=None
implement  2026-10-05T17:17:50Z 2026-10-05T18:53:45Z seconds=5755 outcome=None
converge   2026-10-05T18:53:49Z 2026-10-05T19:01:18Z seconds=449 outcome=None
implement  2026-10-05T19:01:18Z 2026-10-05T19:33:12Z seconds=1914 outcome=None
converge   2026-10-05T19:33:12Z 2026-10-05T19:39:03Z seconds=351 outcome=None
gaps       2026-10-05T19:39:07Z 2026-10-05T19:44:46Z seconds=339 outcome=None
implement  2026-10-05T19:52:24Z 2026-10-05T21:55:31Z seconds=7387 outcome=None
demo       2026-10-05T22:08:13Z 2026-10-05T22:27:44Z seconds=1171 outcome=implementation
implement  2026-10-05T22:36:06Z 2026-10-05T23:29:03Z seconds=3177 outcome=None
demo       2026-10-05T23:32:43Z 2026-10-05T23:42:40Z seconds=597 outcome=implementation
implement  2026-10-05T23:43:07Z 2026-10-06T00:20:39Z seconds=2252 outcome=None
demo       2026-10-06T00:23:53Z 2026-10-06T00:31:54Z seconds=481 outcome=accepted
implement  2026-10-06T00:35:14Z 2026-10-06T01:11:28Z seconds=2174 outcome=None
adversary  2026-10-06T03:16:18Z 2026-10-06T03:33:00Z seconds=1002 outcome=None
implement  2026-10-06T03:33:35Z 2026-10-06T04:15:52Z seconds=2537 outcome=None
entries 17 stage time (sum seconds) 31439
worked (union in [ready,accepted]) 31439 overlap among brackets: 0
integration 10995 brackets inside: [('adversary', '2026-10-06T03:16:18Z', '2026-10-06T03:33:00Z'), ('implement', '2026-10-06T03:33:35Z', '2026-10-06T04:15:52Z')]
demo accepted 2026-10-06T00:31:54Z dependency 7538 window 9712
parks [('2026-10-04T18:14:46Z', '2026-10-04T18:56:39Z', 2513), ('2026-10-04T20:49:56Z', '2026-10-04T22:12:48Z', 4972), ('2026-10-05T01:25:20Z', '2026-10-05T02:50:47Z', 5127), ('2026-10-05T04:10:04Z', '2026-10-05T05:35:03Z', 5099), ('2026-10-05T08:13:04Z', '2026-10-05T08:56:35Z', 2611)] person (cause unrecorded) 20322
worker 63139
elapsed 133433 unattributed (incl. person) 20322 sum check True
```

## what the script says (--json, S08)
```json
{
 "elapsed": 133433,
 "stage_seconds": 31439,
 "worked_seconds": 31439,
 "waiting": {
  "integration": 10995,
  "dependency": 7538,
  "review": 0,
  "worker": 63139,
  "unattributed": 20322
 },
 "unattributed_person": 20322,
 "rework": {
  "seconds": 5429,
  "tokens": 12217422
 },
 "moments": {
  "ready": "2026-10-04T18:13:05Z",
  "accepted": "2026-10-06T07:16:58Z",
  "demo_accepted": "2026-10-06T00:31:54Z",
  "merged": "2026-10-06T03:14:44Z"
 },
 "cost": {
  "tokens": 174532695,
  "shared": 31119819,
  "sessions": {
   "c1c52109-a42e-4a63-be90-04df7ba894ab": 47724654,
   "d883234c-5eb4-40de-976d-81f2874b2842": 126808041
  }
 },
 "read_from": {
  "demo_accepted": "the demo bracket ended 2026-10-06T00:31:54Z",
  "merged": "3138416 (merge commit: slice/S08-scoped-mutation)",
  "ready": "b31c864 (slices/README.md: S04-parallel-gate)",
  "accepted": "c88fe2f (slices/README.md: S08-scoped-mutation)",
  "worked_seconds": "the record's brackets",
  "integration": "3138416 (merge commit: slice/S08-scoped-mutation)",
  "dependency": "1d6cc17 (slices/README.md: S06-scoped-gate of S06-scoped-gate); a person's patch: none present: no record names a park's cause",
  "review": "none present: no record names a park's cause",
  "unattributed_person": "specs/cruise-log.jsonl: each row ending stopped: human or parked:, to the next row's start; a person held the run, cause unrecorded",
  "worker": "specs/cruise-log.jsonl: from the log's first row to accepted, less every cause above; counts time outside any iteration",
  "elapsed": "ready: commit b31c864 (slices/README.md: S04-parallel-gate); accepted: commit c88fe2f (slices/README.md: S08-scoped-mutation)",
  "unattributed": "elapsed less worked time and every cause above: what no bracket, commit or log claims",
  "stage_seconds": "the record's brackets (17 ended)",
  "rework": "the 2 entries after a refused demo's bracket",
  "cost": "the transcripts, by delegate and bracket"
 }
}
```

## S08 implement 17:17:50Z-18:53:45Z: requests in the window by spawn chain (window.py, read-only over the transcripts)
```python
# Which subagents of session d883234c made requests inside S08's implement 17:17:50Z-18:53:45Z, and who spawned them.
import json, glob, os
B=os.path.expanduser('~/.claude/projects/-home-noahc-math-slipwai-graph/d883234c-5eb4-40de-976d-81f2874b2842')
lo,hi='2026-10-05T17:17:50','2026-10-05T18:53:45'
meta={}; spawns={}  # toolUseId -> agent file that issued it
for m in glob.glob(B+'/subagents/*.meta.json'):
    a=os.path.basename(m)[:-10]; meta[a]=json.load(open(m))
for p in [B+'.jsonl']+glob.glob(B+'/subagents/*.jsonl'):
    who='host' if p.endswith(B+'.jsonl') else os.path.basename(p)[:-6]
    for line in open(p,errors='replace'):
        if '"tool_use"' not in line: continue
        try: it=json.loads(line)
        except ValueError: continue
        for c in ((it.get('message') or {}).get('content') or []):
            if isinstance(c,dict) and c.get('type')=='tool_use': spawns[c.get('id')]=who
def chain(a):
    out=[]
    while a!='host' and a in meta:
        out.append(meta[a].get('description')); a=spawns.get(meta[a].get('toolUseId'),'?')
    return out
seen=set(); tok={}
for p in glob.glob(B+'/subagents/*.jsonl'):
    a=os.path.basename(p)[:-6]
    for line in open(p,errors='replace'):
        if '"usage"' not in line: continue
        try: it=json.loads(line)
        except ValueError: continue
        ts=(it.get('timestamp') or '')[:19]; m=it.get('message') or {}; u=m.get('usage'); k=it.get('requestId') or m.get('id')
        if it.get('type')!='assistant' or not isinstance(u,dict) or not (lo<=ts<=hi) or k in seen: continue
        seen.add(k); tok[a]=tok.get(a,0)+sum(u.get(f) or 0 for f in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'))
for a,n in sorted(tok.items(),key=lambda x:-x[1]):
    print(f"{n:>12}  {meta.get(a,{}).get('agentType')}  chain: {' <- '.join(map(str,chain(a)))}")
```
```
    45067029  drive-implement  chain: S08 US2 implement T002-T009 <- drive-slice S08-scoped-mutation
    14512455  drive-implement  chain: S06 T036+T037 per D140
    10579455  drive-slice  chain: drive-slice S14-result-contract
     9098453  drive-implement  chain: S14 converge fixes T012-T019 <- drive-slice S14-result-contract
     6816520  drive-gaps  chain: S06 after-converge gaps T018
     5670825  drive-converge  chain: S06 converge pass 5
     5470201  drive-slice  chain: drive-slice S08-scoped-mutation
     4651435  drive-converge  chain: S14 converge pass 1 <- drive-slice S14-result-contract
     3688198  drive-converge  chain: S06 converge pass 4
     2340047  drive-converge  chain: S14 converge pass 2 <- drive-slice S14-result-contract
     2132340  drive-gaps  chain: S14 post-converge gaps trace <- drive-slice S14-result-contract
     1933045  drive-implement  chain: S14 T007-T009 briefs, ladder, page <- drive-slice S14-result-contract
     1589609  drive-implement  chain: S14 T001-T002 hand-back shape <- drive-slice S14-result-contract
     1519048  drive-implement  chain: S14 T010 migrate and fragment <- drive-slice S14-result-contract
     1384797  drive-implement  chain: S06 T039–T042 implement
      590560  drive-skipper  chain: Skipper D140 S06 Makefile class
      378074  drive-implement  chain: S14 re-pin two cruise brief tests <- drive-slice S14-result-contract
```
S08's own: 45067029 + 5470201 = 50537230; the script's entry:
```
{'stage': 'implement', 'started': '2026-10-05T17:17:50Z', 'stage_seconds': 5755, 'recorded_seconds': 5755, 'tokens': 50537230, 'read_from': 'the transcripts, by delegate and bracket', 'delegates': ['S08 US2 implement T002-T009', 'drive-slice S08-scoped-mutation']}
```
Recorded usage for that entry (unchanged, the page's in/out): host 9194805 + opus subagents 41226585 + sonnet subagents 76077125 = 126498515
