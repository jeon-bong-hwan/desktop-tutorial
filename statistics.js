// Each source is aggregated separately: snapshots and event histories must not be added together.
function dateParts(value){
 const m=String(value||'').trim().match(/^(\d{4})[-./]?(\d{2})[-./]?(\d{2})(?:$|[ T])/);
 if(!m)return null;
 const [year,month,day]=m.slice(1).map(Number),d=new Date(Date.UTC(year,month-1,day));
 return year>=1900&&d.getUTCFullYear()===year&&d.getUTCMonth()===month-1&&d.getUTCDate()===day?{year,month}:null;
}
export function aggregateEvents(rows,industry=''){
 const years=new Map();let excluded=0;
 for(const row of rows){
  if(industry&&(row['업태구분명']||row['판매업종류']||'미제공')!==industry)continue;
  const event=Object.hasOwn(row,'변동사유발생연월일');
  const candidates=event?(['신규','폐업'].includes((row['구분']||'').trim())?[[(row['구분']||'').trim(),row['변동사유발생연월일']]]:[]):[['신규',row['인허가일자']],['폐업',row['폐업일자']]];
  for(const [kind,value] of candidates){
   const parts=dateParts(value);if(!parts){if(value||event)excluded++;continue;}
   if(!years.has(parts.year))years.set(parts.year,Array.from({length:12},()=>({new:0,closed:0})));
   years.get(parts.year)[parts.month-1][kind==='신규'?'new':'closed']++;
  }
 }
 return {years,excluded};
}
export function setupStatistics(datasets){
 const $=id=>document.getElementById(id),make=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 let result={years:new Map(),excluded:0};
 const total=months=>months.reduce((a,b)=>({new:a.new+b.new,closed:a.closed+b.closed}),{new:0,closed:0});
 function chart(target,groups){
  const root=$(target);root.replaceChildren();
  if(!groups.length){root.append(make('p','집계할 날짜 자료가 없습니다.'));return;}
  const ns='http://www.w3.org/2000/svg',width=Math.max(720,groups.length*76+70),height=300,top=38,bottom=250,max=Math.max(1,...groups.flatMap(g=>[g.new,g.closed]));
  const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',groups.map(g=>`${g.label}: 신규 ${g.new}건, 폐업 ${g.closed}건`).join('; '));svg.style.minWidth=`${width}px`;
  const add=(tag,attrs,text)=>{const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;svg.append(n);return n;};
  for(let i=0;i<=4;i++){const y=bottom-(bottom-top)*i/4;add('line',{x1:58,x2:width-12,y1:y,y2:y,stroke:'#dfe5eb'});add('text',{x:50,y:y+4,'text-anchor':'end',fill:'#64748b','font-size':11},Math.round(max*i/4).toLocaleString());}
  const step=(width-70)/groups.length;
  groups.forEach((g,i)=>{const x=58+step*(i+.5);for(const [j,key,color] of [[0,'new','#087f8c'],[1,'closed','#db6743']]){const h=g[key]/max*(bottom-top),bx=x+(j?3:-24);const rect=add('rect',{x:bx,y:bottom-h,width:21,height:h,fill:color,rx:3});const title=document.createElementNS(ns,'title');title.textContent=`${g.label} ${j?'폐업':'신규'} ${g[key].toLocaleString()}건`;rect.append(title);add('text',{x:bx+10.5,y:bottom-h-6,'text-anchor':'middle',fill:color,'font-size':11},g[key].toLocaleString());}add('text',{x,y:275,'text-anchor':'middle',fill:'#334155','font-size':12},g.label);});root.append(svg);
 }
 function render(){
  const year=Number($('statsYear').value),months=result.years.get(year)||[],annual=[...result.years].sort((a,b)=>a[0]-b[0]).map(([y,m])=>({label:`${y}년`,...total(m)}));
  const monthly=months.map((m,i)=>({label:`${i+1}월`,...m}));
  $('monthlyTitle').textContent=year?`${year}년 월별 신규·폐업`:'월별 신규·폐업';
  const sums=total(months);$('statsSummary').textContent=months.length?`${year}년 신규 ${sums.new.toLocaleString()}건 · 폐업 ${sums.closed.toLocaleString()}건`:'집계 가능한 신규·폐업 기록이 없습니다.';
  chart('monthlyChart',monthly);chart('annualChart',annual);
  const table=make('table'),head=make('thead'),hr=make('tr');for(const text of ['기간','신규 (건)','폐업 (건)'])hr.append(make('th',text));head.append(hr);table.append(head);const body=make('tbody');for(const g of [...annual,...monthly]){const tr=make('tr');for(const text of [g.label,g.new.toLocaleString(),g.closed.toLocaleString()])tr.append(make('td',text));body.append(tr);}table.append(body);$('statsTable').replaceChildren(table);
 }
 function aggregate(){
  const d=datasets[Number($('statsDataset').value)];result=aggregateEvents(d?.rows||[],$('statsIndustry').value);const old=$('statsYear').value;
  $('statsYear').replaceChildren();for(const y of [...result.years.keys()].sort((a,b)=>b-a))$('statsYear').add(new Option(`${y}년`,y));
  if(result.years.has(Number(old)))$('statsYear').value=old;
  $('statsYear').disabled=!result.years.size;
  $('statsNote').textContent=`${d?.label||'자료 없음'} · ${$('statsIndustry').value||'모든 업종'} · 날짜 오류로 제외된 항목 ${result.excluded.toLocaleString()}건. 검색·상태 필터와 별도로 선택 자료 전체를 집계합니다.`;render();
 }
 function source(){const d=datasets[Number($('statsDataset').value)];$('statsIndustry').replaceChildren(new Option('모든 업종',''));for(const v of [...new Set((d?.rows||[]).map(r=>r['업태구분명']||r['판매업종류']||'미제공'))].sort())$('statsIndustry').add(new Option(v,v));if([...$('statsIndustry').options].some(o=>o.value==='주유소'))$('statsIndustry').value='주유소';aggregate();}
 function refresh(index){$('statsDataset').replaceChildren();datasets.forEach((d,i)=>$('statsDataset').add(new Option(d.label,i)));$('statsDataset').value=String(index??Math.max(0,datasets.findIndex(d=>d.rows.some(r=>Object.hasOwn(r,'변동사유발생연월일')))));source();}
 $('statsDataset').onchange=source;$('statsIndustry').onchange=aggregate;$('statsYear').onchange=render;refresh();return refresh;
}
