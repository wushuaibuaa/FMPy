from fmpy.cross_check.validate_vendor_repo import validate_signal
import numpy as np
import unittest


class CrossCheckTest(unittest.TestCase):

    def test_validate_signal(self):

        t = np.linspace(-0.1, 1.1, 13)
        y = np.zeros_like(t)
        y[0] = -0.2  # before t_start
        y[5] = 1  # peak in the middle
        y[-1] = 0.2  # after t_stop

        t_ref = t.copy()
        y_ref = y.copy()

        # add almost outlier
        y[2] = -0.09

        # add actual outlier
        y[-3] = 0.2

        t_band, y_min, y_max, i_out = validate_signal(t, y, t_ref, y_ref, 0.0, 1.0, num=21, dx=5)

        y_min_expected = -0.1 * np.ones(21)
        y_max_expected = 0.1 * np.ones(21)

        y_max_expected[5] = 0.6
        y_max_expected[6:11] = 1.1
        y_max_expected[11] = 0.6

        self.assertTrue(np.allclose(y_min, y_min_expected))
        self.assertTrue(np.allclose(y_max, y_max_expected))

        # # use this to plot
        # import matplotlib.pyplot as plt
        # plt.plot(t_band, y_min, 'g.-', linewidth=0.7)
        # plt.plot(t_band, y_max, 'g.-', linewidth=0.7)
        # plt.plot(t, y, 'b.-', linewidth=0.7)
        # plt.plot(t[i_out], y[i_out], 'ro')
        # plt.show()
