import test from 'node:test';
import assert from 'node:assert/strict';
import {aggregateEvents} from '../statistics.js';
test('event dates count only new and closure events, separately by year and industry',()=>{
 const rows=[['신규','2024-01-02','주유소'],['폐업','2024-12-31','주유소'],['휴업','2024-01-03','주유소'],['신규','2025-02-03','주유소'],['신규','2024-02-30','주유소'],['신규','2024-01-02','일반판매소']].map(([kind,date,industry])=>({'구분':kind,'변동사유발생연월일':date,'판매업종류':industry}));
 const {years,excluded}=aggregateEvents(rows,'주유소');assert.equal(years.get(2024)[0].new,1);assert.equal(years.get(2024)[11].closed,1);assert.equal(years.get(2025)[1].new,1);assert.equal(excluded,1);
});
test('snapshot dates count both permit and closure without guessing from current status',()=>{
 const {years}=aggregateEvents([{'인허가일자':'20200229','폐업일자':'2023-03-04','영업상태명':'폐업'},{'영업상태명':'폐업'}]);
 assert.equal(years.get(2020)[1].new,1);assert.equal(years.get(2023)[2].closed,1);assert.equal(years.size,2);
});
