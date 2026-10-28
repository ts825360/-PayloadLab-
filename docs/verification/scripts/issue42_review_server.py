"""Local UI review only. Requires explicit acknowledgement of unapproved policy."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'backend'))
from app.review_app import create_review_app
from app.core.request_limits import InputLimits
from app.core.sql_limits import SQLLimits
from app.labs.practice_extensions import PERMISSION_COMMANDS
from app.labs.sql_injection import QUERY_PREFIX,QUERY_SUFFIX
import uvicorn


def review_authorizer(action,arg1,arg2,database,trigger):
    if action in (sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_RECURSIVE): return sqlite3.SQLITE_OK
    if action==sqlite3.SQLITE_FUNCTION and arg2 in {'length','printf','sum'}: return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acknowledge-unapproved-policy',action='store_true',required=True)
    parser.add_argument('--port',type=int,default=8102)
    args=parser.parse_args()
    p=json.loads((ROOT/'docs/verification/evidence/2026-10-28-issue42-sizing-summary.json').read_text(encoding='utf-8'))['proposal']
    input_limits=InputLimits(p['string_codepoints'],p['body_bytes'],p['history_count'],p['history_total_codepoints'],(1<<53)-1,frozenset(PERMISSION_COMMANDS))
    statement=4*p['string_codepoints']+len((QUERY_PREFIX+QUERY_SUFFIX+'EXPLAIN ').encode())
    statement=1<<(statement-1).bit_length()
    sql_limits=SQLLimits(p['sql_vm_shared_request'],p['sql_request_deadline_ms'],p['returned_rows'],p['single_sql_value_bytes'],p['sql_result_bytes'],p['sql_result_bytes'],statement)
    app=create_review_app(input_limits=input_limits,sql_limits=sql_limits,sql_authorizer=review_authorizer,response_bytes=p['api_response_bytes'])
    print('REVIEW ONLY: unapproved policy; loopback only; production app unchanged',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=args.port,log_level='warning',ws='none')
