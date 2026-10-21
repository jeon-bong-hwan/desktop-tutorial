import importlib.util
import io
import json
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('sync_data',Path(__file__).parents[1]/'tools/sync_data.py')
sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)

class CollectorTests(unittest.TestCase):
    def row(self,name='주유소'):
        return {'사업장명':name,'영업상태명':'영업/정상','업태구분명':'주유소','관리번호':name}
    def test_complete_pagination_and_header_auth(self):
        calls=[]
        def opener(request,timeout):
            calls.append(request)
            return io.BytesIO(json.dumps({'data':[self.row(str(len(calls)))],'totalCount':2}).encode())
        rows=sync.collect('https://api.odcloud.kr/api/example/v1/test','test-only',opener)
        self.assertEqual(len(rows),2)
        self.assertIn('page=2',calls[1].full_url)
        self.assertNotIn('test-only',calls[0].full_url)
        self.assertEqual(calls[0].get_header('Authorization'),'Infuser test-only')
    def test_incomplete_and_changed_sources_fail(self):
        for payload in [{'data':[],'totalCount':10},{'data':[{'사업장명':'x'}],'totalCount':1},{'data':[self.row()],'totalCount':0}]:
            with self.assertRaises(ValueError):sync.collect('https://api.odcloud.kr/api/example/v1/test','test-only',lambda req,timeout:io.BytesIO(json.dumps(payload).encode()))
    def test_untrusted_or_secret_bearing_url_is_rejected(self):
        for url in ['http://api.odcloud.kr/api/x','https://other.example/api/x','https://api.odcloud.kr/api/x?serviceKey=secret','https://user:secret@api.odcloud.kr/api/x','https://api.odcloud.kr/x']:
            with self.assertRaises(ValueError):sync.validate_url(url)

if __name__=='__main__':unittest.main()
