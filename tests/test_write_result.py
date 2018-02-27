import unittest
import numpy as np
from fmpy.util import write_mat, write_xls
from scipy.io import loadmat
import xlrd

class WriteResultTest(unittest.TestCase):

    def test_write_mat(self):

        values = [(0.0, 1.1, 1),
                  (0.1, 1.2, 0),
                  (0.2, 1.3, -3)]

        result = np.array(np.array(values,
                          dtype=[('time', 'f8'),
                                 ('d', 'f8'),
                                 ('i', 'i4')]))

        write_mat('test.mat', result=result)

        mat = loadmat('test.mat')

        names = mat['names']

        self.assertEqual(names[0].rstrip(), 'time')
        self.assertEqual(names[1].rstrip(), 'd')
        self.assertEqual(names[2].rstrip(), 'i')

        data = mat['data']

        self.assertTrue(np.all(data == np.array(values, dtype=np.float64).T))

    def test_write_xls(self):

        values = [(0.0, 1.1, 1),
                  (0.1, 1.2, 0),
                  (0.2, 1.3, -3)]

        result = np.array(np.array(values,
                          dtype=[('time', 'f8'),
                                 ('d', 'f8'),
                                 ('i', 'i4')]))

        write_xls('test.xls', result=result)

        # open the workbook
        book = xlrd.open_workbook('test.xls')

        # get the first sheet
        sh = book.sheet_by_index(0)

        # get the names, quantities and units
        self.assertEqual(sh.cell_value(0, 0), 'time')
        self.assertEqual(sh.cell_value(0, 1), 'd')
        self.assertEqual(sh.cell_value(0, 2), 'i')

        self.assertTrue(np.all(sh.col_values(0, 1, sh.nrows) == [0.0, 0.1, 0.2]))
        self.assertTrue(np.all(sh.col_values(1, 1, sh.nrows) == [1.1, 1.2, 1.3]))
        self.assertTrue(np.all(sh.col_values(2, 1, sh.nrows) == [1, 0, -3]))
