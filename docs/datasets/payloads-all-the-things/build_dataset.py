"""Build machine-readable CSVs offline; never execute/render/request payloads."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from curated_samples import BENIGN, CMD, SQL, SSRF, UNCERTAIN, XSS

ROOT = Path(__file__).resolve().parent
COMMIT = '3ac27901c711bdf3f5b65a7b1d1820a1f65bd09a'
FIELDS = 'id,payload,label,attack_type,technique,target_platform,input_context,variant_type,family_id,source_url,source_commit,label_reason,validation_status,license'.split(',')
GROUPS = {'sql_injection': SQL, 'xss': XSS, 'command_injection': CMD, 'ssrf': SSRF}
CONTEXTS = {
    'sql_injection': '원문 SQLi 학습에서 신뢰하지 않는 입력으로 SQL 구조/식에 삽입하는 공격 시도. 전체 SELECT는 주입 뒤 실행하려는 코드 조각이며 단독으로는 정상 SQL일 수 있음. DBMS/삽입 경계/스키마 일치 필요.',
    'xss': '원문 XSS 시도의 HTML/속성/JavaScript/URI 문맥. 맞는 삽입 경계와 브라우저 이벤트가 필요하며 실행 성공을 뜻하지 않음.',
    'command_injection': '원문 CMDi 학습에서 신뢰하지 않는 입력이 셸 문자열 또는 인자에 결합되는 시도. 셸 종류/인자 처리/디코딩/이스케이프 조건이 필요. command1 등은 템플릿 자리표시자.',
    'ssrf': '원문 SSRF 학습에서 공개 목적지만 허용하는 서버 URL 가져오기 기능에 내부/로컬 목적지를 요청하려는 시도. URL 파서/DNS/네트워크/리다이렉트 정책에 따라 해석 다름.',
}


def source_proof(source, payload):
    relative = 'sources/' + source.replace('/', '__')
    raw = (ROOT / relative).read_bytes()
    value = payload.encode('utf-8')
    start = raw.find(value)
    if start < 0:
        raise ValueError(f'Not an exact upstream substring: {source}: {payload!r}')
    end = start + len(value)
    first = raw[:start].count(b'\n') + 1
    last = raw[:end - 1].count(b'\n') + 1
    url = f'https://github.com/swisskyrepo/PayloadsAllTheThings/blob/{COMMIT}/{quote(source)}#L{first}-L{last}'
    return url, dict(local_path=relative, byte_start=start, byte_end=end, line_start=first, line_end=last, payload_sha256=hashlib.sha256(value).hexdigest())


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    manifest = dict(schema_version=1, source_repository='https://github.com/swisskyrepo/PayloadsAllTheThings', source_commit=COMMIT, generated_by='build_dataset.py (offline)', entries={}, sources=[], counts={})
    for kind, samples in GROUPS.items():
        rows = []
        for index, (source, payload, platform, technique, variant, family) in enumerate(samples, 1):
            row_id = f'{kind}-attack-{index:03}'
            url, proof = source_proof(source, payload)
            manifest['entries'][row_id] = proof
            rows.append(dict(zip(FIELDS, [row_id, payload, 'attack', kind, technique, platform, CONTEXTS[kind], variant, family, url, COMMIT, '원문의 공격 시나리오에서 사용된 시도라는 문서상 라벨. 성공/유효성/악의의 보편적 판정 아님.', 'documentation_reviewed_not_executed', 'MIT'])))
        for index, (payload, context) in enumerate(BENIGN[kind], 1):
            row_id = f'{kind}-benign-{index:03}'
            rows.append(dict(zip(FIELDS, [row_id, payload, 'benign', kind, 'normal_input', 'context_defined', context, 'original', f'{kind}_benign_{index:03}', '', '', 'PayloadLab 별도 작성: 명시한 문맥의 정상 입력. 다른 실행 문맥에서 무조건 안전하다는 뜻 아님.', 'documentation_reviewed_not_executed', 'MIT'])))
        source, payload, platform, technique, reason = UNCERTAIN[kind]
        row_id = f'{kind}-uncertain-001'
        url, proof = source_proof(source, payload)
        manifest['entries'][row_id] = proof
        rows.append(dict(zip(FIELDS, [row_id, payload, 'uncertain', kind, technique, platform, '문자열만 제공됨; 삽입 문맥/권한/정책 미지정', 'context_unspecified', f'{kind}_context_review', url, COMMIT, 'review_only: ' + reason, 'documentation_reviewed_not_executed', 'MIT'])))
        with (output / f'{kind}.csv').open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
            writer.writeheader()
            writer.writerows(rows)
        manifest['counts'][kind] = {label: sum(r['label'] == label for r in rows) for label in ('attack', 'benign', 'uncertain')}
    for path in sorted((ROOT / 'sources').glob('*.md')):
        raw = path.read_bytes()
        source = path.name.replace('__', '/')
        manifest['sources'].append(dict(local_path='sources/' + path.name, source_path=source, sha256=hashlib.sha256(raw).hexdigest(), source_url=f'https://github.com/swisskyrepo/PayloadsAllTheThings/blob/{COMMIT}/{quote(source)}'))
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    return manifest['counts']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir), ensure_ascii=False))
