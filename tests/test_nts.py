import importlib.util,io,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('nts',Path(__file__).parents[1]/'tools/sync_nts.py');nts=importlib.util.module_from_spec(spec);spec.loader.exec_module(nts)
class NTSTests(unittest.TestCase):
    def test_tax_response_and_private_number_redaction(self):
        targets=[{'id':'municipality:station','businessNumber':'1234567890'}]
        def opener(req,timeout):
            self.assertEqual(req.method,'POST');self.assertEqual(json.loads(req.data),{'b_no':['1234567890']})
            return io.BytesIO(json.dumps({'status_code':'OK','data':[{'b_no':'1234567890','b_stt_cd':'03','end_dt':'20260101'}]}).encode())
        result=nts.lookup(targets,'test-only',opener)
        self.assertEqual(result[0]['status'],'폐업자');self.assertNotIn('1234567890',json.dumps(result));self.assertNotIn('test-only',json.dumps(result))
    def test_invalid_targets_and_incomplete_response(self):
        for raw in ['[]','[{"id":"a","businessNumber":"123"}]']:
            with self.assertRaises(ValueError):nts.parse_targets(raw)
        with self.assertRaises(ValueError):nts.lookup([{'id':'a','businessNumber':'1234567890'}],'test',lambda req,timeout:io.BytesIO(b'{"status_code":"OK","data":[]}'))
    def test_not_registered_is_unknown_not_closed(self):
        r=nts.lookup([{'id':'a','businessNumber':'1234567890'}],'test',lambda req,timeout:io.BytesIO(b'{"status_code":"OK","data":[{"b_no":"1234567890","b_stt_cd":""}]}'))
        self.assertEqual(r[0]['status'],'미확인')
