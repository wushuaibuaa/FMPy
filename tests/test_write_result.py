import unittest
import numpy as np
from fmpy.util import write_mat
from scipy.io import loadmat


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
