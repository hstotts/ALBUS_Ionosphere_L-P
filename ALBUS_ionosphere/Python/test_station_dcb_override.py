"""Regression tests for calibrated station-DCB overrides.

Keep this file in the source release, but do not install it as a runtime ALBUS
module. Run it with the project environment from this directory:

    python -m unittest -v test_station_dcb_override.py
"""

import os
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Albus_RINEX_2 as AR2
import station_dcb_override as override


MAX_SAT = AR2.MAX_POSSIBLE_SATELLITES
DPOS = AR2._DATA_POS
BAD = AR2.BAD_DATA_CODE

MJD0 = 61040  # 2025-12-31
SAT = 5
STA = "SUTH"
RECV_NS = -0.423
SAT_P2_NS = 3.374
SAT_C1_NS = 1.067


def make_obs():
    """Return a small synthetic day with one GPS satellite."""
    count = 8
    mjd = MJD0 + (np.arange(count) * 3600.0 + 300.0) / 86400.0
    sat_array = np.zeros((count, MAX_SAT), dtype="int32") - 1
    obs_data = np.zeros((count, 1, AR2._DATA_POS_SIZE)) + BAD
    for index in range(count):
        sat_array[index, SAT] = 0
        obs_data[index, 0, DPOS["C1"]] = 22.0e6 + 40.0 * index
        obs_data[index, 0, DPOS["P1"]] = 22.0e6 + 40.0 * index + 1.5
        obs_data[index, 0, DPOS["P2"]] = 22.0e6 + 40.0 * index + 4.0
        obs_data[index, 0, DPOS["L1"]] = 1.2e8 + 10.0 * index
        obs_data[index, 0, DPOS["L2"]] = 0.9e8 + 10.0 * index
    return mjd, sat_array, obs_data


def bias_dicts(with_station):
    """Build dictionaries in the layout consumed by DCB_bias_correction."""
    stations = {STA.lower(): RECV_NS * 1e-9} if with_station else {}
    ionex = {}
    monthly = {}
    c1_monthly = {}
    for mjd in (MJD0 - 1, MJD0, MJD0 + 1):
        ionex[mjd] = [{SAT: SAT_P2_NS * 1e-9}, dict(stations)]
        monthly[mjd] = [{SAT: SAT_P2_NS * 1e-9}, dict(stations)]
        c1_monthly[mjd] = [{SAT: SAT_C1_NS * 1e-9}, {}]
    return ionex, monthly, c1_monthly


def run_correction(ionex, monthly, c1_monthly):
    mjd, sat_array, obs_data = make_obs()
    valid = AR2.DCB_bias_correction(
        mjd,
        sat_array,
        obs_data,
        STA,
        ionex,
        monthly,
        c1_monthly,
        raise_bias_error=0,
    )
    return obs_data, valid


class StationDCBOverrideTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.saved_env = {
            name: os.environ.get(name)
            for name in (override.CSV_ENV, override.MODE_ENV)
        }
        os.environ.pop(override.CSV_ENV, None)
        os.environ.pop(override.MODE_ENV, None)
        override.reset_cache()

    def tearDown(self):
        os.environ.pop(override.CSV_ENV, None)
        os.environ.pop(override.MODE_ENV, None)
        for name, value in self.saved_env.items():
            if value is not None:
                os.environ[name] = value
        override.reset_cache()
        self.temp_dir.cleanup()

    def write_csv(self, text, filename="override.csv"):
        path = os.path.join(self.temp_dir.name, filename)
        with open(path, "w", encoding="utf-8", newline="") as fp:
            fp.write(text)
        return path

    def configure_standard_csv(self):
        path = self.write_csv(
            "date,station,dcb_cal_ns\n"
            "2025-12-30,%s,%.6f\n"
            "2025-12-31,%s,%.6f\n"
            % (STA, RECV_NS - 0.1, STA, RECV_NS + 0.1)
        )
        os.environ[override.CSV_ENV] = path
        return path

    def test_no_environment_is_inert(self):
        self.assertFalse(override.is_configured())
        self.assertFalse(override.has_override(STA))
        ionex, monthly, _ = bias_dicts(with_station=False)
        self.assertEqual(override.apply(ionex, monthly, MJD0 - 1, MJD0 + 1), 0)

    def test_campaign_mean_matches_natural_dcb_path(self):
        natural_obs, natural_valid = run_correction(
            *bias_dicts(with_station=True)
        )
        no_bias_obs, no_bias_valid = run_correction(
            *bias_dicts(with_station=False)
        )
        self.assertEqual(natural_valid[0], 1)
        self.assertEqual(no_bias_valid[0], 0)
        self.assertFalse(np.array_equal(no_bias_obs, natural_obs))

        self.configure_standard_csv()
        os.environ[override.MODE_ENV] = override.CAMPAIGN_MEAN_MODE
        ionex, monthly, c1_monthly = bias_dicts(with_station=False)
        applied = override.apply(ionex, monthly, MJD0 - 1, MJD0 + 1)
        overridden_obs, overridden_valid = run_correction(
            ionex, monthly, c1_monthly
        )

        self.assertEqual(applied, 3)
        self.assertEqual(overridden_valid[0], 1)
        self.assertTrue(np.array_equal(overridden_obs, natural_obs))
        for mjd in (MJD0 - 1, MJD0, MJD0 + 1):
            self.assertAlmostEqual(
                ionex[mjd][1][STA.lower()], RECV_NS * 1e-9, places=18
            )
            self.assertAlmostEqual(
                monthly[mjd][1][STA.lower()], RECV_NS * 1e-9, places=18
            )

    def test_daily_value_and_campaign_mean_fallback(self):
        self.configure_standard_csv()
        os.environ[override.MODE_ENV] = override.DAILY_MODE

        self.assertAlmostEqual(
            override.get_override_ns(STA.lower(), MJD0),
            RECV_NS + 0.1,
            places=12,
        )
        self.assertAlmostEqual(
            override.get_override_ns("  SUTH  ", MJD0 + 100),
            RECV_NS,
            places=12,
        )

    def test_removed_configuration_restores_persistent_bias_values(self):
        self.configure_standard_csv()
        original_seconds = 2.5e-9
        ionex, monthly, _ = bias_dicts(with_station=False)
        monthly[MJD0][1][STA.lower()] = original_seconds

        override.apply(ionex, monthly, MJD0, MJD0)
        self.assertIn(STA.lower(), ionex[MJD0][1])
        self.assertNotEqual(monthly[MJD0][1][STA.lower()], original_seconds)

        os.environ.pop(override.CSV_ENV)
        self.assertEqual(override.apply(ionex, monthly, MJD0, MJD0), 0)
        self.assertNotIn(STA.lower(), ionex[MJD0][1])
        self.assertEqual(monthly[MJD0][1][STA.lower()], original_seconds)

    def test_invalid_mode_fails_closed(self):
        self.configure_standard_csv()
        os.environ[override.MODE_ENV] = "daliy"
        with self.assertRaises(override.StationDCBConfigurationError):
            override.get_override_ns(STA, MJD0)

    def test_missing_csv_fails_closed(self):
        os.environ[override.CSV_ENV] = os.path.join(
            self.temp_dir.name, "missing.csv"
        )
        with self.assertRaises(override.StationDCBConfigurationError):
            override.has_override(STA)

    def test_invalid_csv_rows_fail_closed(self):
        cases = {
            "missing_station_header": "date,dcb_ns\n2025-12-31,-0.4\n",
            "non_finite": "date,station,dcb_ns\n2025-12-31,SUTH,nan\n",
            "duplicate_date": (
                "date,station,dcb_ns\n"
                "2025-12-31,SUTH,-0.4\n"
                "2025-12-31,SUTH,-0.5\n"
            ),
        }
        for name, contents in cases.items():
            with self.subTest(name=name):
                os.environ[override.CSV_ENV] = self.write_csv(
                    contents, filename=name + ".csv"
                )
                override.reset_cache()
                with self.assertRaises(override.StationDCBConfigurationError):
                    override.has_override(STA)

    def test_override_and_local_input_bypass_legacy_binary_cache(self):
        self.configure_standard_csv()
        computed = ("mjd", "sat", "obs", "xyz", "valid", "blocks")

        with mock.patch.object(AR2, "_read_Albus_MJD") as read_cache, \
             mock.patch.object(
                 AR2, "get_station_base_observations", return_value=computed
             ) as calculate:
            result = AR2.get_station_base_observations_with_bin(
                MJD0,
                MJD0,
                STA,
                use_bin_files=1,
                use_external_dcb_files=1,
            )
        self.assertEqual(result, computed)
        read_cache.assert_not_called()
        calculate.assert_called_once()

        os.environ.pop(override.CSV_ENV)
        override.reset_cache()
        with mock.patch.object(AR2, "_read_Albus_MJD") as read_cache, \
             mock.patch.object(
                 AR2, "get_station_base_observations", return_value=computed
             ) as calculate:
            result = AR2.get_station_base_observations_with_bin(
                MJD0,
                MJD0,
                STA,
                use_bin_files=1,
                local_rinex_obs_file="local.25o",
            )
        self.assertEqual(result, computed)
        read_cache.assert_not_called()
        calculate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
