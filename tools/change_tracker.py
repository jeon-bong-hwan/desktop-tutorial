"""Compare published licensing snapshots, without inferring closure from absence."""

def identity(row):
    municipality=str(row.get('개방자치단체코드') or '').strip()
    management=str(row.get('관리번호') or '').strip()
    if not municipality or not management:
        raise ValueError('Municipality code and management ID are required.')
    return municipality+':'+management

def index_rows(rows):
    indexed={}
    for row in rows:
        key=identity(row)
        if key in indexed:raise ValueError('Duplicate municipality and management ID.')
        indexed[key]=row
    return indexed

def compare(previous,current,detected_at):
    before=index_rows(previous);after=index_rows(current);events=[]
    for key,new in after.items():
        old=before.get(key)
        if old is None:
            kind='원본에 추가'
        elif (old.get('영업상태명',''),old.get('상세영업상태명',''),old.get('폐업일자','')) != (new.get('영업상태명',''),new.get('상세영업상태명',''),new.get('폐업일자','')):
            kind='상태 변경'
        else:continue
        events.append({'id':key,'name':new.get('사업장명',''),'industry':new.get('업태구분명',''),'kind':kind,'previousStatus':old.get('영업상태명') if old else None,'status':new.get('영업상태명') or '미제공','previousDetail':old.get('상세영업상태명') if old else None,'detail':new.get('상세영업상태명') or '미제공','closureDate':new.get('폐업일자') or None,'sourceUpdatedAt':new.get('데이터갱신시점') or None,'detectedAt':detected_at})
    for key,old in before.items():
        if key not in after:
            events.append({'id':key,'name':old.get('사업장명',''),'industry':old.get('업태구분명',''),'kind':'원본에서 제외 · 폐업 확정 아님','previousStatus':old.get('영업상태명'),'status':'원본 확인 필요','detail':'원본 확인 필요','closureDate':None,'sourceUpdatedAt':None,'detectedAt':detected_at})
    return events
