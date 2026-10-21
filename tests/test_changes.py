import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('changes',Path(__file__).parents[1]/'tools/change_tracker.py');changes=importlib.util.module_from_spec(spec);spec.loader.exec_module(changes)
class ChangeTests(unittest.TestCase):
    def row(self,code='100',status='영업/정상'):
        return {'개방자치단체코드':code,'관리번호':'same','사업장명':'시험주유소','업태구분명':'주유소','영업상태명':status}
    def test_municipalities_are_distinct(self):
        self.assertEqual(len(changes.index_rows([self.row('100'),self.row('200')])),2)
    def test_unchanged_no_event_and_closure_changed(self):
        self.assertEqual(changes.compare([self.row()],[self.row()],'now'),[])
        events=changes.compare([self.row()],[self.row(status='폐업')],'now')
        self.assertEqual(events[0]['previousStatus'],'영업/정상');self.assertEqual(events[0]['status'],'폐업')
    def test_missing_is_not_closed(self):
        e=changes.compare([self.row()],[],'now')[0]
        self.assertEqual(e['status'],'원본 확인 필요');self.assertIsNone(e['closureDate'])
    def test_duplicate_composite_rejected(self):
        with self.assertRaises(ValueError):changes.index_rows([self.row(),self.row()])
