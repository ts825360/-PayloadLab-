"""Export fixed local review cases; no browser, network, or shell payload execution.
Run from repository root: python docs/verification/scripts/lens_review_cases.py
"""
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
BASE = '23b05593b73f6d9c9556eecd68abad5fbb8f6801'
sys.path.insert(0, str(ROOT / 'backend'))
from app.routes.labs import analyze_lab, attempt_lab


def baseline_module(path, name):
    source = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT).decode('utf-8')
    module = types.ModuleType(name)
    exec(compile(source, f'{BASE}:{path}', 'exec'), module.__dict__)
    return module


old_trace = baseline_module('backend/app/learning_trace.py', 'review_base_trace')
old_extensions = baseline_module('backend/app/labs/practice_extensions.py', 'review_base_extensions')
old_trace.get_extension_trace = old_extensions.get_extension_trace
CASES = [
    ('SQL-01', 'sql-injection-easy', {'username': '박태성'}, 'empty'),
    ('SQL-02', 'sql-injection-easy', {'username': ''}, 'empty'),
    ('SQL-03', 'sql-injection-easy', {'username': "admin'"}, 'syntax_error'),
    ('SQL-04', 'sql-injection-easy', {'username': "admin' '1'='1'--"}, 'syntax_error'),
    ('SQL-05', 'sql-injection-medium', {'username': "admin' OR '1'='1'--"}, 'syntax_error'),
    ('SQL-06', 'sql-injection-easy', {'username': "admin' OR '1'='1'--"}, 'matched'),
    ('SQL-07', 'sql-injection-easy', {'username': "O''Reilly"}, 'empty'),
    ('SQL-08', 'sql-injection-easy', {'username': "admin'' OR 1=1--'"}, 'syntax_error'),
    ('SQL-09', 'sql-injection-easy', {'username': "admin'--"}, 'matched'),
    ('SQL-10', 'sql-injection-easy', {'username': "admin' OR '1'='1"}, 'matched'),
    ('XSS-01', 'reflected-xss-easy', {'query': 'hello'}, 'unrecognized'),
    ('XSS-02', 'reflected-xss-easy', {'query': '<b>hello</b>'}, 'unrecognized'),
    ('XSS-03', 'reflected-xss-easy', {'query': '<script>'}, 'unrecognized'),
    ('XSS-04', 'reflected-xss-easy', {'query': '<script></script>'}, 'recognized'),
    ('XSS-05', 'reflected-xss-medium', {'query': '<script>hello</script>'}, 'unrecognized'),
    ('IDOR-01', 'idor-easy', {'requested_id': 1042}, 'own'),
    ('IDOR-02', 'idor-easy', {'requested_id': 1043}, 'exposed'),
    ('IDOR-03', 'idor-easy', {'requested_id': 9999}, 'missing'),
    ('IDOR-04', 'idor-medium', {'requested_id': 1043, 'claimed_user_id': 1}, 'blocked'),
    ('IDOR-05', 'idor-medium', {'requested_id': 1043, 'claimed_user_id': 2001}, 'exposed'),
    ('SSRF-01', 'ssrf-easy', {'target_url': 'https://example.com/news'}, 'fetched'),
    ('SSRF-02', 'ssrf-medium', {'target_url': 'http://127.0.0.1/admin'}, 'blocked'),
    ('SSRF-03', 'ssrf-medium', {'target_url': 'http://preview.lab.invalid@127.0.0.1/admin'}, 'fetched'),
    ('SSRF-04', 'ssrf-medium', {'target_url': 'http://user@127.0.0.1/preview.lab.invalid'}, 'fetched'),
    ('SSRF-05', 'ssrf-easy', {'target_url': 'http://localhost:bad'}, 'unsupported'),
    ('SSRF-06', 'ssrf-easy', {'target_url': 'http://😀@localhost/admin'}, 'fetched'),
    ('SSRF-07', 'ssrf-easy', {'target_url': 'http://10.0.0.1/admin'}, 'fetched'),
    ('CMD-01', 'command-injection-easy', {'hostname': 'example.com'}, 'command_ok'),
    ('CMD-02', 'command-injection-easy', {'hostname': 'example.com; whoami'}, 'injected'),
    ('CMD-03', 'command-injection-medium', {'hostname': 'example.com; whoami'}, 'blocked'),
    ('CMD-04', 'command-injection-medium', {'hostname': 'example.com && id'}, 'injected'),
    ('CMD-05', 'command-injection-medium', {'hostname': 'example.com && whoami; pwd'}, 'blocked'),
    ('CMD-06', 'command-injection-easy', {'hostname': 'example.com;'}, 'unsupported'),
    ('CMD-07', 'command-injection-easy', {'hostname': 'example.com || whoami'}, 'unsupported'),
    ('LINUX-01', 'linux-basics-easy', {'command': 'ls'}, 'quiz_correct'),
    ('LINUX-02', 'linux-basics-easy', {'command': ''}, 'quiz_incorrect'),
    ('LINUX-03', 'linux-basics-easy', {'command': 'ls -l /lab'}, 'quiz_incorrect'),
    ('LINUX-04', 'linux-basics-medium', {'command': 'ls /lab'}, 'quiz_incorrect'),
    ('LINUX-05', 'linux-basics-medium', {'command': 'ls /lab -l'}, 'quiz_incorrect'),
    ('LINUX-06', 'linux-basics-medium', {'command': 'pwd'}, 'quiz_incorrect'),
    ('LINUX-07', 'linux-basics-medium', {'command': 'ls -l /lab'}, 'quiz_correct'),
]


def evidence(trace):
    keys = ('raw_input', 'effective_input', 'composition', 'execution', 'lens',
            'row_explanations', 'relations', 'network', 'command_model', 'quiz',
            'browser_execution_verified', 'phase')
    return {key: trace[key] for key in keys if key in trace}


records = []
for case_id, lab, payload, expected in CASES:
    result = attempt_lab(lab, payload)
    current = result.learning_trace
    previous = old_trace.build_learning_trace(lab, payload, result)
    analysis = analyze_lab(lab, payload)
    assert current['execution']['status'] == expected, case_id
    assert analysis['execution'] is None, case_id
    assert previous['execution']['status'] == expected, case_id
    records.append(dict(id=case_id, lab=lab, payload=payload, expected_status=expected,
                        actual_status=current['execution']['status'], success=result.success,
                        before=evidence(previous), after=evidence(current), analysis=evidence(analysis)))
output = ROOT / 'docs/verification/2026-10-27-lens-review-cases.json'
output.write_text(json.dumps(dict(base_commit=BASE, method='direct route function calls; not HTTP or browser execution',
                                 case_count=len(records), cases=records), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(records)} cases matched expected status; before/after and analysis exported to {output.name}')
