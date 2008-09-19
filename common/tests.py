# -*- coding: utf-8 -*-
from django.test import TestCase

class TestExcel(TestCase):
    def test_iterate_over_xls_from_odt(self):
        from os import path
        import excel

        file_path = path.join(path.dirname(path.abspath(__file__)),
                              'test_xls_form_odt.xls')
        spec   = ({'id' : 0},
                {'id' : 1, 'name': 2}) 
        iterator = excel.iterate(spec, filename=file_path, skip_first=1)
        
        for row_num, user_data, map_data in iterator:
            if row_num == 1:
                self.assertEqual(78844, user_data['id'])
                self.assertEqual(12, map_data['id'])
                self.assertEqual(u'Germany', map_data['name'])
                break
            else:
                self.fail('First row numner is not 1 but %s' % row_num)

                
