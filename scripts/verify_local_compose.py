"""Smoke-test an already running local PayloadLab Compose stack (stdlib only).

No container startup, shell execution, external targets, or deployment changes.
The URLs inside SSRF/CMDi payloads are strings for the existing simulation.
"""
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from xml.etree import ElementTree


API = 'http://127.0.0.1:8001'
WEB = 'http://127.0.0.1:5173'
CASES = [
    ('sql-injection-easy', {'username': "admin'OR'1'='1'--"}, 'matched'),
    ('sql-injection-medium', {'username': "admin'or'1'='1'--"}, 'matched'),
    ('reflected-xss-easy', {'query': '<script>alert(1)</script>'}, 'recognized'),
    ('reflected-xss-medium', {'query': '<SCRIPT>alert(1)</SCRIPT>'}, 'recognized'),
    ('idor-easy', {'requested_id': 1043}, 'exposed'),
    ('idor-medium', {'requested_id': 1043, 'claimed_user_id': 2001}, 'exposed'),
    ('ssrf-easy', {'target_url': 'http://127.0.0.1/admin'}, 'fetched'),
    ('ssrf-medium', {'target_url': 'http://preview.lab.invalid@127.0.0.1/admin'}, 'fetched'),
    ('command-injection-easy', {'hostname': 'example.com;whoami'}, 'injected'),
    ('command-injection-medium', {'hostname': 'example.com && whoami'}, 'injected'),
    ('linux-basics-easy', {'command': 'ls'}, 'quiz_correct'),
    ('linux-basics-medium', {'command': 'ls -l /lab'}, 'quiz_correct'),
    ('permissions-easy', {'command': 'cat /lab/report.txt', 'history': []}, 'permission_denied'),
]


def read(path, payload=None):
    body = None if payload is None else json.dumps(payload).encode('utf-8')
    request = Request(API + path, data=body, headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def verify():
    assert read('/health') == {'status': 'ok'}, 'API health failed'
    assert {lab['id'] for lab in read('/labs')} == {case[0] for case in CASES}, 'Lab catalog changed'
    for lab_id, payload, status in CASES:
        analysis = read(f'/labs/{lab_id}/analyze', payload)
        assert analysis['phase'] == 'analysis' and analysis['execution'] is None, lab_id
        trace = read(f'/labs/{lab_id}/attempt', payload)['learning_trace']
        assert trace['execution']['status'] == status, (lab_id, trace['execution'])
        if lab_id.startswith(('ssrf-', 'command-injection-', 'linux-basics-', 'permissions-')):
            assert trace['simulated'] is True, lab_id
    try:
        read('/labs/permissions-medium/attempt', {'command': 'whoami'})
    except HTTPError as error:
        assert error.code == 404, error.code
    else:
        raise AssertionError('Permissions Normal must remain unregistered')
    elevated = read('/labs/permissions-easy/attempt', {
        'command': 'cat /lab/report.txt', 'history': ['sudo /lab/maintenance'],
    })['learning_trace']
    assert elevated['terminal']['current_user'] == 'root'
    assert 'training-report' in elevated['execution']['stdout']
    with urlopen(WEB, timeout=15) as response:
        assert response.status == 200 and b'id="root"' in response.read()
    for name in ('payloadlab-wordmark.svg', 'payloadlab-wordmark-dark.svg'):
        with urlopen(f'{WEB}/brand/{name}', timeout=15) as response:
            svg = ElementTree.fromstring(response.read())
        assert svg.tag == '{http://www.w3.org/2000/svg}svg', name
        assert not any(element.tag.endswith(('script', 'foreignObject', 'image')) for element in svg), name
    print('PASS: health; 13 lab analyses + attempts; permissions Normal 404; virtual permission transition; frontend HTTP; two SVG assets')


if __name__ == '__main__':
    verify()
