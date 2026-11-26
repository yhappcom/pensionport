"""Replay a pinned, bounded public-origin capture artifact, never approve a fact.

The expected ZIP digest and runner commit must be supplied from the separately
observed Actions receipt. A caller choosing its own pin is NOT proof of origin.
No ZIP member is extracted to disk. The raw bytes are returned only to the
current review; no publisher or network action is provided here.
"""
from datetime import datetime
from io import BytesIO
import json
import re
from urllib.parse import urlsplit
from zipfile import ZipFile, BadZipFile
from .codec import json_digest, require_hash, sha256
from .errors import InvalidInput

_HOSTS = frozenset({'www.law.go.kr','law.go.kr','www.fsc.go.kr','fsc.go.kr',
                    'kind.krx.co.kr','pdf.krx.co.kr','www.krx.co.kr','krx.co.kr','listing.krx.co.kr'})
_MAX_BODY = 2_500_000
_MAX_ZIP = 25_000_000


def _need(ok, code):
    if not ok:
        raise InvalidInput('PUBLIC_ORIGIN_' + code)


def _official_url(url):
    _need(type(url) is str and len(url)<=2048 and not any(ord(c)<32 for c in url), 'URL')
    try:
        p=urlsplit(url)
        _need(p.scheme=='https' and p.hostname in _HOSTS and not p.username
              and not p.password and p.port in (None,443) and not p.fragment, 'URL')
    except ValueError as exc:
        raise InvalidInput('PUBLIC_ORIGIN_URL') from exc


def replay_public_origin_archive(raw, *, expected_archive_sha256, expected_commit):
    expected=require_hash(expected_archive_sha256,'PUBLIC_ORIGIN_ARCHIVE_SHA256')
    _need(type(expected_commit) is str and re.fullmatch('[a-f0-9]{40}',expected_commit), 'COMMIT')
    _need(type(raw) is bytes and 0<len(raw)<=_MAX_ZIP and sha256(raw)==expected, 'ARCHIVE_BYTES')
    try:
        with ZipFile(BytesIO(raw)) as z:
            infos=z.infolist(); names=[i.filename for i in infos]
            _need(1<len(infos)<=41 and len(names)==len(set(names)) and 'receipt.json' in names
                  and all(re.fullmatch(r'(?:receipt\.json|[A-Z][A-Z0-9_]{0,63}\.html)',n) for n in names)
                  and all(0<i.file_size<=_MAX_BODY and not i.is_dir() and not i.flag_bits&1 for i in infos)
                  and sum(i.file_size for i in infos)<=_MAX_ZIP, 'ZIP_CENSUS')
            receipt=json.loads(z.read('receipt.json').decode('utf-8'))
            _need(type(receipt) is dict and set(receipt)=={'schema','code_commit','captured_utc',
                  'results','private_source_uploaded','finance_fact_approved','p0_go'}
                  and receipt['schema']=='IRE_R304_PUBLIC_ORIGIN_CAPTURE_V1'
                  and receipt['code_commit']==expected_commit
                  and all(receipt[k] is False for k in ('private_source_uploaded','finance_fact_approved','p0_go'))
                  and type(receipt['results']) is list and 0<len(receipt['results'])<=40, 'RECEIPT')
            observed=datetime.fromisoformat(receipt['captured_utc'])
            _need(observed.utcoffset() is not None and observed.utcoffset().total_seconds()==0,'CAPTURE_DATE')
            bodies={}; used={'receipt.json'}; seen_keys=set()
            for row in receipt['results']:
                _need(type(row) is dict and type(row.get('key')) is str
                      and re.fullmatch('[A-Z][A-Z0-9_]{0,63}',row['key'])
                      and row['key'] not in seen_keys,'ROW_IDENTITY')
                seen_keys.add(row['key']); _official_url(row.get('requested_url'))
                if row.get('failed_closed') is True:
                    _need(set(row)=={'key','requested_url','failed_closed','error_type','reason'},'FAILED_ROW')
                    continue
                _need(set(row)=={'key','requested_url','final_url','http_status','content_type','date_header',
                      'sha256','bytes','transport','semantic_document_content_verified','effective_date_verified','v123_approved'}
                      and type(row['http_status']) is int and row['http_status']==200
                      and type(row['content_type']) is str and any(x in row['content_type'].lower() for x in ('text/html','application/xhtml+xml'))
                      and row['transport']=='HTTPS_STDLIB_DEFAULT_TLS'
                      and all(row[k] is False for k in ('semantic_document_content_verified','effective_date_verified','v123_approved')),
                      'ROW_SCHEMA')
                _official_url(row['final_url']); key=row['key']+'.html'
                _need(key in names and row['requested_url'] not in bodies,'BODY_IDENTITY')
                body=z.read(key); used.add(key)
                _need(type(row['bytes']) is int and row['bytes']==len(body)
                      and sha256(body)==require_hash(row['sha256']),'BODY_HASH')
                bodies[row['requested_url']]={'body':body,'row':row}
            _need(used==set(names),'UNACCOUNTED_MEMBER')
    except (BadZipFile,KeyError,UnicodeError,ValueError,TypeError,OverflowError) as exc:
        if isinstance(exc,InvalidInput):raise
        raise InvalidInput('PUBLIC_ORIGIN_INVALID_ARCHIVE') from exc
    return {'archive_sha256':expected,'code_commit':expected_commit,
            'capture_receipt_sha256':json_digest(receipt),'capture_date':observed.date().isoformat(),
            'bodies':bodies,'failed_count':len(seen_keys)-len(bodies),
            'issuer_authenticity_independently_verified':False,'finance_fact_approved':False}
