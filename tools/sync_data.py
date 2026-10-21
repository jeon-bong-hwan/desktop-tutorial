"""Refresh the licensing snapshot from a configured official ODCloud file API.

The portal detail page is not an API endpoint. API credentials belong in GitHub
Actions Secrets, never in the browser or saved data.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import csv
import io
import os
import re
import sys
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
DETAIL_URL = 'https://www.data.go.kr/data/15044961/fileData.do'

def validate_url(url):
    parts = urllib.parse.urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname != 'api.odcloud.kr'
        or parts.username or parts.password or parts.port not in (None,443)
        or not parts.path.startswith('/api/') or parts.query or parts.fragment):
        raise ValueError('Use the HTTPS api.odcloud.kr /api/... endpoint from the official API documentation, without query parameters.')
    return url

def collect(url, key, opener=urllib.request.urlopen):
    validate_url(url)
    rows=[]
    total=None
    for page in range(1,1001):
        request=urllib.request.Request(url+'?'+urllib.parse.urlencode({'page':page,'perPage':1000}),headers={'Authorization':'Infuser '+key,'Accept':'application/json'})
        with opener(request,timeout=60) as response:
            payload=json.load(response)
        batch=payload.get('data')
        count=payload.get('totalCount')
        if not isinstance(batch,list) or not isinstance(count,int) or isinstance(count,bool) or count<=0:
            raise ValueError('Expected a nonempty ODCloud data array with totalCount.')
        if total is None:total=count
        if count!=total:raise ValueError('Source changed during pagination; retry later.')
        if not batch or len(rows)+len(batch)>total:
            raise ValueError('Incomplete or inconsistent pagination.')
        for row in batch:
            if not isinstance(row,dict) or not row.get('사업장명') or '영업상태명' not in row or '업태구분명' not in row or '관리번호' not in row:
                raise ValueError('Required licensing columns are missing; existing data retained.')
        rows.extend(batch)
        if len(rows)==total:return rows
    raise ValueError('Pagination safety limit reached.')

def validate_csv_url(url):
    parts=urllib.parse.urlsplit(url)
    host=parts.hostname or ''
    if parts.scheme!='https' or not (host=='data.go.kr' or host.endswith('.go.kr')) or parts.username or parts.password or parts.port not in (None,443) or parts.fragment:
        raise ValueError('Use an official government HTTPS CSV download URL.')
    return url

class GovernmentRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_csv_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def collect_csv(url, opener=None):
    validate_csv_url(url)
    if opener is None:opener=urllib.request.build_opener(GovernmentRedirect()).open
    with opener(url,timeout=60) as response:
        raw=response.read(32*1024*1024+1)
    if len(raw)>32*1024*1024:raise ValueError('Source file exceeds 32MB limit.')
    try:text=raw.decode('utf-8-sig')
    except UnicodeDecodeError:text=raw.decode('cp949')
    reader=csv.DictReader(io.StringIO(text),strict=True)
    required={'사업장명','영업상태명','업태구분명','관리번호'}
    if not required.issubset(reader.fieldnames or []):raise ValueError('Download is not the expected licensing CSV.')
    rows=list(reader)
    if not rows or any(not r.get('사업장명') or None in r or any(v is None for v in r.values()) for r in rows):raise ValueError('Source CSV is empty or malformed.')
    return rows

def status_file(status):
    folder=ROOT/'sync';folder.mkdir(exist_ok=True)
    (folder/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')

def main():
    url=os.environ.get('STATION_API_URL','').strip()
    key=os.environ.get('STATION_API_KEY','').strip()
    csv_url=os.environ.get('STATION_CSV_URL','').strip()
    status_path=ROOT/'sync/status.json'
    previous=json.loads(status_path.read_text()) if status_path.exists() else {}
    attempt=datetime.now(timezone.utc).isoformat()
    status={**previous,'sourcePage':DETAIL_URL,'lastAttemptAt':attempt,'mode':'scheduled-snapshot','status':'error'}
    if not csv_url and (not url or not key):
        status.update(status='not-configured',message='No public CSV URL or authenticated API source is configured. Uploaded data retained.')
        status_file(status)
        print(status['message'],file=sys.stderr)
        return 2
    try:
        rows=collect_csv(csv_url) if csv_url else collect(url,key)
        path=ROOT/'initial-data.js'
        text=path.read_text();prefix='globalThis.STATION_DATASETS='
        start=text.index(prefix)+len(prefix)
        datasets=json.loads(text[start:].strip().rstrip(';'))
        columns=['관리번호','사업장명','영업상태명','상세영업상태명','업태구분명','도로명주소','지번주소','인허가일자','폐업일자','데이터갱신시점','최종수정시점']
        projected=[{k:str(row.get(k) or '').strip() for k in columns} for row in rows]
        ids=[r['관리번호'] for r in projected]
        if any(not i for i in ids) or len(ids)!=len(set(ids)):
            raise ValueError('Blank or duplicate management IDs; existing data retained.')
        old_count=len(datasets[0]['rows'])
        if old_count and len(projected)<old_count*0.8:
            raise ValueError('Unexpected reduction exceeding 20%; manual source review required.')
        updated=[r['데이터갱신시점'] for r in projected if r['데이터갱신시점']]
        status.update(status='ok',lastSuccessAt=attempt,rowCount=len(rows),sourceUpdatedThrough=max(updated) if updated else None,message='Official source snapshot refreshed; not a real-time operation guarantee.')
        datasets[0]={'label':'석유판매업 인허가 · 공식 원본 정기 갱신','rows':projected,'note':'공식 원본 정기 수집 자료입니다. 실시간 영업 여부를 보증하지 않습니다. 원본 갱신시점과 마지막 수집시각을 구분해 확인하세요.','sourcePage':DETAIL_URL}
        output='// Official API snapshot; authentication values are never included.\n'+prefix+json.dumps(datasets,ensure_ascii=False).replace('<','\\u003c')+';\n'
        temp=path.with_suffix('.tmp');temp.write_text(output);temp.replace(path)
        status_file(status)
        print('Refreshed',len(rows),'licensing records.')
        return 0
    except Exception as exc:
        # Never log request URLs, query strings, response bodies or secret values.
        status.update(message='Official source refresh failed ('+type(exc).__name__+'). Existing snapshot retained.')
        status_file(status);print(status['message'],file=sys.stderr)
        return 1

if __name__=='__main__':
    sys.exit(main())
