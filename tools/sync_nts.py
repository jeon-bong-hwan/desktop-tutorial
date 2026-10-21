"""Server-side NTS tax-status lookup; credentials and business numbers stay private."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, re, sys
import urllib.parse, urllib.request

ROOT=Path(__file__).resolve().parents[1]
ENDPOINT='https://api.odcloud.kr/api/nts-businessman/v1/status'

def parse_targets(raw):
    targets=json.loads(raw)
    if not isinstance(targets,list) or not targets or len(targets)>1000:
        raise ValueError('Pilot lookup needs 1-1000 targets.')
    seen=set()
    for t in targets:
        if not isinstance(t,dict) or not re.fullmatch(r'[0-9]{10}',t.get('businessNumber','')) or not isinstance(t.get('id'),str) or not t['id'] or t['id'] in seen:
            raise ValueError('Each target needs a unique id and 10-digit businessNumber.')
        seen.add(t['id'])
    return targets

def lookup(targets,key,opener=urllib.request.urlopen):
    numbers=list(dict.fromkeys(t['businessNumber'] for t in targets));results={}
    for start in range(0,len(numbers),100):
        batch=numbers[start:start+100]
        req=urllib.request.Request(ENDPOINT+'?'+urllib.parse.urlencode({'serviceKey':key}),data=json.dumps({'b_no':batch}).encode(),headers={'Content-Type':'application/json'},method='POST')
        with opener(req,timeout=45) as response:payload=json.load(response)
        if payload.get('status_code')!='OK' or not isinstance(payload.get('data'),list):raise ValueError('Unexpected NTS response.')
        returned=payload['data']
        if len(returned)!=len(batch) or {r.get('b_no') for r in returned}!=set(batch):raise ValueError('Incomplete NTS response.')
        for r in returned:
            code=r.get('b_stt_cd','')
            if code not in ('','01','02','03'):raise ValueError('Unknown NTS status code.')
            results[r['b_no']]={'statusCode':code,'status':{'01':'계속사업자','02':'휴업자','03':'폐업자','':'미확인'}[code],'closureDate':r.get('end_dt') or None}
    # Never publish business numbers or raw tax response fields.
    return [{'id':t['id'],**results[t['businessNumber']]} for t in targets]

def main():
    path=ROOT/'sync/nts.json';previous=json.loads(path.read_text()) if path.exists() else {'records':[]}
    key=os.environ.get('NTS_API_KEY','').strip();raw=os.environ.get('NTS_TARGETS_JSON','').strip()
    now=datetime.now(timezone.utc).isoformat()
    status={**previous,'lastAttemptAt':now,'source':'국세청 사업자등록 상태조회','scope':'세무상 상태; 주유소 인허가·실제 영업 여부와 별개'}
    try:
        if not key or not raw:
            status.update(status='not-configured',message='인증키·사업자등록번호 연결자료 필요')
            code=2
        else:
            targets=parse_targets(raw);records=lookup(targets,key)
            status.update(status='ok',records=records,lastSuccessAt=now,message='국세청 상태조회 성공. 원천기관 반영 시차가 있을 수 있습니다.')
            code=0
    except Exception as exc:
        status.update(status='error',message='국세청 조회 실패 ('+type(exc).__name__+'). 기존 결과 유지.')
        code=1
    path.parent.mkdir(exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
    print(status['message'])
    return code

if __name__=='__main__':sys.exit(main())
