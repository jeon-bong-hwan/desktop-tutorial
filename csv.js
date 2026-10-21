export function parseCSV(text) {
 text=text.replace(/^\uFEFF/,'');const rows=[];let row=[],field='',quoted=false;
 for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++;}else if(!quoted&&field!=='')throw Error('따옴표 위치가 올바르지 않습니다.');else quoted=!quoted;}else if(c===','&&!quoted){row.push(field);field='';}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);if(row.some(x=>x.trim()))rows.push(row);row=[];field='';}else field+=c;}
 if(quoted)throw Error('닫히지 않은 따옴표가 있습니다.');row.push(field);if(row.some(x=>x.trim()))rows.push(row);if(rows.length<2)throw Error('헤더와 데이터 행이 필요합니다.');
 const headers=rows.shift().map(x=>x.trim());if(new Set(headers).size!==headers.length)throw Error('중복된 열 이름이 있습니다.');if(!headers.includes('사업장명')&&!headers.includes('업체명'))throw Error('사업장명 또는 업체명 열을 찾을 수 없습니다. 인허가 CSV인지 확인하세요.');
 return rows.map((r,i)=>{if(r.length!==headers.length)throw Error(`${i+2}번째 행의 열 개수가 다릅니다.`);return Object.fromEntries(headers.map((h,j)=>[h,r[j].trim()]));});
}
export function normalize(r){const event=Boolean(r['변동사유발생연월일']);return {name:r['사업장명']||r['업체명'],status:event?`변동: ${r['구분']||'미제공'}`:r['영업상태명']||r['상세영업상태명']||'미제공',detail:r['상세영업상태명']||'미제공',industry:r['업태구분명']||r['판매업종류']||'미제공',id:r['관리번호']||'미제공',updated:r['데이터갱신시점']||r['최종수정시점']||'미제공',address:r['도로명전체주소']||r['소재지전체주소']||r['도로명주소']||r['지번주소']||r['소재지']||'미제공',permit:r['인허가일자']||'미제공',closed:r['폐업일자']||'미제공',eventDate:r['변동사유발생연월일']||'해당 없음'};}
export function filterRows(rows,query,status){return rows.filter(r=>(!status||r.status===status)&&`${r.name} ${r.address} ${r.id}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));}

export function decodeCSVBuffer(buffer,preference='auto'){
 const encodings=preference==='auto'?['utf-8','euc-kr']:[preference];
 for(const encoding of encodings){try{return {text:new TextDecoder(encoding,{fatal:true}).decode(buffer),encoding};}catch(error){if(!(error instanceof TypeError))throw error;}}
 throw new Error('선택한 인코딩으로 읽을 수 없습니다. 자동 감지 또는 파일의 실제 인코딩을 선택하세요.');
}
