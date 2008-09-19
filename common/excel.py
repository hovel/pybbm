# -*- coding: utf-8 -*-
import xlrd

def iterate(row_spec, file_contents = None,
            filename=None, skip_first=0, sheets= [0]):
    """
    row_spec is tuple of dictionaries or just dictionary that maps key
    to row number

    use like:
    for row_number, user_id, map in iterate( \
            'sample.xls', ({'id':1}, {'id':2, 'map_name':3} ):
        assert {'id':'78844'} == user_id
        assert {'id':'12', 'map_name':u'Germany'} == map
    """
    # analyse row specification
    if isinstance(row_spec,dict):
        row_spec = (row_spec,)

    # process workbook
    wb = xlrd.open_workbook(filename=filename, file_contents=file_contents)
    for sheet in wb.sheets():
        for row_number in xrange(skip_first, sheet.nrows):
            items = [{} for x in range(len(row_spec))]
            values = sheet.row(row_number)
            for item_pos, item_spec in enumerate(row_spec):
                for key, value_pos in  item_spec.iteritems():
                    try:
                        items[item_pos][key] = values[value_pos].value
                    except IndexError,e :
                        pass
            yield [row_number] + items
