"""Reproducible local sizing of tracked main and pending #19; no policy edits."""
import ast, base64, json, platform, sqlite3, statistics, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path.cwd()
OUT=ROOT/'docs/verification/evidence/2026-10-28-issue42-sizing.json'
FIELDS={'username','query','requested_id','claimed_user_id','target_url','hostname','command','history'}
def git(ref,path): return subprocess.check_output(['git','show',f'{ref}:{path}'],stderr=subprocess.DEVNULL)
def corpus(ref):
    result=[]
    files=subprocess.check_output(['git','ls-tree','-r','--name-only',ref,'backend/tests'],text=True).splitlines()
    for path in files:
        if not path.endswith('.py'): continue
        tree=ast.parse(git(ref,path).decode())
        for node in ast.walk(tree):
            if not isinstance(node,ast.Dict): continue
            try: value=ast.literal_eval(node)
            except (ValueError,TypeError): continue
            if isinstance(value,dict) and value and set(value)<=FIELDS and all(isinstance(k,str) for k in value):
                if all(isinstance(v,(str,int,list)) and not isinstance(v,bool) for v in value.values()):
                    if all(not isinstance(v,str) or len(v)<=2000 for v in value.values()):
                        result.append(dict(payload=value,source=path))
    for path in ['docs/verification/2026-10-27-lens-review-cases.json','docs/verification/2026-10-27-learning-flow-cases.json']:
        try: data=json.loads(git(ref,path))
        except subprocess.CalledProcessError: continue
        def walk(obj):
            if isinstance(obj,dict):
                if isinstance(obj.get('payload'),dict) and set(obj['payload'])<=FIELDS:
                    result.append(dict(payload=obj['payload'],source=path))
                for v in obj.values(): walk(v)
            elif isinstance(obj,list):
                for v in obj: walk(v)
        walk(data)
    module=base64.b64encode(git(ref,'frontend/src/lesson-catalog.js')).decode()
    js="const m=await import('data:text/javascript;base64,"+module+"');const rows=[];for(const c of ['sql_injection','reflected_xss','idor','ssrf','command_injection','linux_basics','permissions'])for(const d of ['easy','medium'])for(const s of m.getLesson(c,d)?.steps||[])rows.push({category:c,suggestion:s.suggestion});process.stdout.write(JSON.stringify(rows));"
    lessons=json.loads(subprocess.check_output(['node','--input-type=module','-e',js],text=True,encoding='utf-8'))
    fields={'sql_injection':'username','reflected_xss':'query','idor':'requested_id','ssrf':'target_url','command_injection':'hostname','linux_basics':'command','permissions':'command'}
    for row in lessons:
        value=row['suggestion']
        if row['category']=='idor':
            try:value=int(value)
            except (ValueError,TypeError):continue
        result.append(dict(payload={fields[row['category']]:value},source='frontend lesson suggestion'))
    # Deliberate compatibility envelope, separate from existing teaching examples.
    for text in ['a'*2000,'박'*2000,'😀'*2000,'\x01'*2000,'"'*2000,'<script>'+'a'*1983+'</script>']:
        for field in ['username','query','target_url','hostname','command']:
            result.append(dict(payload={field:text},source='synthetic existing 2000-codepoint envelope'))
    longest='ls -l /lab/report.txt'
    result.append(dict(payload={'command':'whoami','history':[longest]*40},source='synthetic maximum count allowed history'))
    union="' UNION ALL SELECT 3,'learner','dummy'"
    idx=4
    while len(union+f" UNION ALL SELECT {idx},'learner','dummy'"+'--')<=2000:
        union+=f" UNION ALL SELECT {idx},'learner','dummy'";idx+=1
    result.append(dict(payload={'username':union+'--'},source='synthetic linear UNION ALL within 2000 chars'))
    short="' UNION ALL SELECT 3,1,1"
    idx=4
    while len(short+f" UNION ALL SELECT {idx},1,1"+'--')<=2000:
        short+=f" UNION ALL SELECT {idx},1,1";idx+=1
    result.append(dict(payload={'username':short+'--'},source='synthetic compact linear UNION ALL within 2000 chars'))
    unique={json.dumps(x['payload'],sort_keys=True,ensure_ascii=False):x for x in result}
    return list(unique.values())
def worker(ref):
    inputs=corpus(ref)
    with tempfile.TemporaryDirectory(prefix='payloadlab42-measure-') as tmp:
        dest=Path(tmp)
        files=subprocess.check_output(['git','ls-tree','-r','--name-only',ref,'backend/app'],text=True).splitlines()
        for path in files:
            if path.endswith('.py'):
                p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git(ref,path))
        sys.path.insert(0,str(dest/'backend'))
        from app.labs import list_labs
        from app.routes.labs import attempt_lab,analyze_lab
        from app.labs import sql_injection as sql
        original=sqlite3.connect
        guard_events=[]
        connection_counters=[]
        def connect(*args,**kwargs):
            conn=original(*args,**kwargs);start=time.perf_counter();ticks=0
            counter_record=[0];connection_counters.append(counter_record)
            def guard():
                nonlocal ticks
                ticks+=100
                counter_record[0]=ticks
                stop=ticks>=100000 or time.perf_counter()-start>.05
                if stop: guard_events.append(dict(ticks=ticks))
                return int(stop)
            conn.set_progress_handler(guard,100)
            return conn
        sqlite3.connect=connect
        records=[];sql_records=[]
        for item in inputs:
            p=item['payload']
            for lab in list_labs():
                lid=lab.metadata.id
                field=('username' if lid.startswith('sql-') else 'query' if lid.startswith('reflected-') else 'requested_id' if lid.startswith('idor-') else 'target_url' if lid.startswith('ssrf-') else 'hostname' if lid.startswith('command-') else 'command')
                if field not in p: continue
                payload={k:v for k,v in p.items() if k==field or k=='history' and lid.startswith('permissions-') or k=='claimed_user_id' and lid.startswith('idor-')}
                for route in (analyze_lab,attempt_lab):
                    try:
                        connection_counters.clear()
                        start=time.perf_counter();v=route(lid,payload);elapsed=(time.perf_counter()-start)*1000
                        if hasattr(v,'model_dump'):v=v.model_dump(mode='json')
                        records.append(dict(lab=lid,route=route.__name__,payload=payload,source=item['source'],request_utf8=len(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()),request_ascii=len(json.dumps(payload,ensure_ascii=True).encode()),response_utf8=len(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()),sql_request_vm_upper=sum(c[0]+100 for c in connection_counters),elapsed_ms=elapsed))
                    except Exception as e:records.append(dict(lab=lid,route=route.__name__,payload=payload,error=type(e).__name__))
                if field=='username' and isinstance(payload[field],str):
                    raw=payload[field];filtered=sql._strip_uppercase_or(raw) if lid.endswith('medium') else raw
                    c=original(':memory:')
                    c.execute('CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,password TEXT)');c.executemany('INSERT INTO users VALUES(?,?,?)',sql._SEED_USERS);c.commit()
                    steps=[0];started=time.perf_counter()
                    def counter():
                        steps[0]+=1
                        return int(steps[0]>=100000 or time.perf_counter()-started>.05)
                    c.set_progress_handler(counter,1)
                    try:
                        rows=c.execute(sql.compose_query(filtered)).fetchall()
                        sql_records.append(dict(lab=lid,input=raw,vm_steps=steps[0],rows=len(rows),result_utf8=len(json.dumps(rows,ensure_ascii=False).encode())))
                    except sqlite3.Error:pass
                    finally:c.close()
        sqlite3.connect=original
        timings=[]
        for _ in range(30):
            for medium in (False,True):
                for raw in ['admin',"admin' OR '1'='1'--","admin' oR '1'='1'--","' UNION SELECT 3,'learner','dummy'--"]:
                    c=sql._seed_db();start=time.perf_counter()
                    try:c.execute(sql.compose_query(sql._strip_uppercase_or(raw) if medium else raw)).fetchall()
                    except sqlite3.Error:pass
                    finally:c.close()
                    timings.append((time.perf_counter()-start)*1000)
        return dict(ref=ref,sha=subprocess.check_output(['git','rev-parse',ref],text=True).strip(),distinct_payloads=len(inputs),records=records,sql=sql_records,guard_events=guard_events,timing=dict(samples=len(timings),max_ms=max(timings),median_ms=statistics.median(timings)))
if len(sys.argv)>1:
    print(json.dumps(worker(sys.argv[1]),ensure_ascii=False));sys.exit()
results=[]
for ref in ['64c9cb141108cafa5c6d215fc9eb4981c100b9b7','714a7412f6d638a297de33a07e37ff6f2027e720']:
    result=subprocess.check_output([sys.executable,__file__,ref],text=True,encoding='utf-8',env={**__import__('os').environ,'PYTHONIOENCODING':'utf-8'})
    results.append(json.loads(result))
report=dict(environment=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,os=platform.platform()),scope='Tracked literal test payloads and committed #19 case JSON; not all possible inputs, HTTP, browser or concurrency',versions=results)
all_records=[x for v in results for x in v['records'] if 'error' not in x]
normal=[x for x in all_records if not x['source'].startswith('synthetic')]
sql_rows=[x for v in results for x in v['sql']]
nextpow=lambda n: 1 << (n-1).bit_length()
worst_request=len(json.dumps({'command':'😀'*2000,'history':['ls -l /lab/report.txt']*40},ensure_ascii=True).encode())
summary=dict(route_samples=len(all_records),normal_route_samples=len(normal),normal_max_input=max(len(v) for x in normal for v in x['payload'].values() if isinstance(v,str)),normal_max_response=max(x['response_utf8'] for x in normal),envelope_max_response=max(x['response_utf8'] for x in all_records),max_request_ascii_shape=worst_request,max_sql_vm=max(x['vm_steps'] for x in sql_rows),max_request_vm_upper=max(x['sql_request_vm_upper'] for x in all_records),max_sql_rows=max(x['rows'] for x in sql_rows),max_sql_result=max(x['result_utf8'] for x in sql_rows),max_route_ms=max(x['elapsed_ms'] for x in all_records),route_errors=sum('error' in x for v in results for x in v['records']),guard_events=sum(len(v['guard_events']) for v in results))
summary['proposal']=dict(string_codepoints=2000,history_count=40,history_total_codepoints=2000,body_bytes=nextpow(worst_request),sql_vm_shared_request=nextpow(8*summary['max_request_vm_upper']),sql_request_deadline_ms=320//4,returned_rows=nextpow(summary['max_sql_rows']),single_sql_value_bytes=nextpow(4*2000),sql_result_bytes=nextpow(3*4*2000),api_response_bytes=nextpow(2*summary['envelope_max_response']))
assert summary['route_errors']==summary['guard_events']==0
assert all(x['response_utf8']<summary['proposal']['api_response_bytes'] for x in all_records)
report['summary']=summary
OUT.with_name('2026-10-28-issue42-sizing-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in results:
    ok=[x for x in r['records'] if 'error' not in x]
    print(json.dumps(dict(ref=r['ref'],payloads=r['distinct_payloads'],routes=len(ok),errors=len(r['records'])-len(ok),max_input_chars=max([len(v) for x in ok for v in x['payload'].values() if isinstance(v,str)],default=0),max_request_ascii=max(x['request_ascii'] for x in ok),max_response_utf8=max(x['response_utf8'] for x in ok),max_sql_steps=max(x['vm_steps'] for x in r['sql']),max_sql_rows=max(x['rows'] for x in r['sql']),max_sql_result=max(x['result_utf8'] for x in r['sql']),guard_events=len(r['guard_events']),timing=r['timing']),ensure_ascii=False))
