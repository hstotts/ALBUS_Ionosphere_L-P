"""Regression test for fixed-width RINEX 2 observation fields.

This test remains in the source tree and is intentionally absent from the
runtime CMake install list.
"""

import os
import sys
import unittest

import numpy as np


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Albus_RINEX_2 as AR2


class FixedWidthObservationTests(unittest.TestCase):
    def test_septentrio_record_keeps_blanks_and_lli_ssi_columns(self):
        # Representative MK01 RINEX 2.11 record. LLI/SSI occupy the last two
        # characters of each 16-character field; blank observations must not
        # shift the later S1/S2 fields.
        raw_lines = [
            "  22429600.520 7 117868482.87207  91845635.33805"
            "  22429600.128 5  22429599.836 5",
            "                                                     -1539.849 7"
            "     -1199.875 5",
            "                        43.175          30.649",
        ]
        raw = "".join(line.ljust(80) for line in raw_lines)
        codes = [
            "C1", "L1", "L2", "P2", "P1", "C2", "C5",
            "L5", "D1", "D2", "D5", "S1", "S2", "S5",
        ]
        positions = [AR2._DATA_POS.get(code) for code in codes]
        obs_data = (
            np.zeros((1, 1, AR2._DATA_POS_SIZE), dtype="float64")
            + AR2.BAD_DATA_CODE
        )

        AR2._parse_fixed_width_obs(
            raw,
            len(codes),
            positions,
            codes,
            0,
            0,
            obs_data,
            AR2._DATA_POS["LL"],
            AR2._DATA_POS["SF1"],
            AR2._DATA_POS["SF2"],
            AR2._DATA_POS["S1"],
            AR2._DATA_POS["S2"],
            AR2._DATA_POS["P1"],
            AR2.BAD_DATA_CODE,
        )

        expected = {
            "C1": 22429600.520,
            "L1": 117868482.872,
            "L2": 91845635.338,
            "P2": 22429600.128,
            "P1": 22429599.836,
            "S1": 43.175,
            "S2": 30.649,
        }
        for code, value in expected.items():
            with self.subTest(code=code):
                self.assertEqual(obs_data[0, 0, AR2._DATA_POS[code]], value)

        self.assertEqual(obs_data[0, 0, AR2._DATA_POS["SF1"]], 5.0)
        self.assertEqual(obs_data[0, 0, AR2._DATA_POS["SF2"]], 5.0)


if __name__ == "__main__":
    unittest.main()
