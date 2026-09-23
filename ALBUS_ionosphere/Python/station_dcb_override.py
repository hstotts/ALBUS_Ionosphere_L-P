"""Load and apply calibrated receiver-DCB overrides.

The feature is inactive unless ``ALBUS_STATION_DCB_CSV`` is set. CSV values
are receiver DCBs in nanoseconds on the CODE P1-P2 datum. ``apply`` converts
them to seconds and inserts them into both station-bias dictionaries used by
``Albus_RINEX_2.DCB_bias_correction``.

``ALBUS_STATION_DCB_MODE`` accepts:

* ``campaign-mean`` (default): use one mean value per station.
* ``daily``: use the dated value when available, otherwise the campaign mean.
"""

import csv
import datetime
import math
import os


CSV_ENV = "ALBUS_STATION_DCB_CSV"
MODE_ENV = "ALBUS_STATION_DCB_MODE"
CAMPAIGN_MEAN_MODE = "campaign-mean"
DAILY_MODE = "daily"
_VALID_MODES = (CAMPAIGN_MEAN_MODE, DAILY_MODE)
_MJD_EPOCH = datetime.date(1858, 11, 17)


class StationDCBConfigurationError(ValueError):
    """Raised when an explicitly configured override cannot be used safely."""


# Reload when the path or file metadata changes. Mode is not part of the key
# because the parsed representation contains both daily values and the mean.
_overrides = None
_overrides_key = None
_applied_originals = []
_MISSING = object()


def _restore_applied_values():
    """Undo values inserted by the preceding ``apply`` call.

    ALBUS retains its DCB dictionaries between calls. Restoring the values we
    replaced prevents a removed or changed override configuration from leaking
    into a later run in the same Python process. If another component changed
    a value after our injection, leave that newer value alone.
    """
    global _applied_originals
    for dictionary, mjd, station, original, injected in reversed(
        _applied_originals
    ):
        day_entry = dictionary.get(mjd)
        if day_entry is None:
            continue
        station_biases = day_entry[1]
        if station_biases.get(station, _MISSING) != injected:
            continue
        if original is _MISSING:
            station_biases.pop(station, None)
        else:
            station_biases[station] = original
    _applied_originals = []


def reset_cache():
    """Forget parsed data and restore values changed by the last application."""
    global _overrides, _overrides_key
    _restore_applied_values()
    _overrides = None
    _overrides_key = None


def _normalise_station(station_code):
    if station_code is None:
        return ""
    return str(station_code).strip().lower()


def _date_to_mjd(date_str):
    try:
        date = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except (AttributeError, TypeError, ValueError) as exc:
        raise StationDCBConfigurationError(
            "invalid date %r; expected YYYY-MM-DD" % (date_str,)
        ) from exc
    return (date - _MJD_EPOCH).days


def _get_mode():
    mode = os.environ.get(MODE_ENV, CAMPAIGN_MEAN_MODE).strip().lower()
    if mode not in _VALID_MODES:
        raise StationDCBConfigurationError(
            "%s must be one of %s, got %r"
            % (MODE_ENV, ", ".join(_VALID_MODES), mode)
        )
    return mode


def _configured_path():
    path = os.environ.get(CSV_ENV, "").strip()
    return os.path.abspath(os.path.expanduser(path)) if path else None


def is_configured():
    """Return whether a station-DCB CSV was explicitly configured."""
    return _configured_path() is not None


def _file_key(path):
    try:
        stat = os.stat(path)
    except OSError as exc:
        raise StationDCBConfigurationError(
            "%s=%r cannot be read: %s" % (CSV_ENV, path, exc)
        ) from exc
    if not os.path.isfile(path):
        raise StationDCBConfigurationError(
            "%s=%r is not a regular file" % (CSV_ENV, path)
        )
    return (path, stat.st_mtime_ns, stat.st_size)


def _row_error(path, row_number, message):
    return StationDCBConfigurationError(
        "%s row %d: %s" % (path, row_number, message)
    )


def _load():
    """Load and validate the configured CSV, reusing it while unchanged."""
    global _overrides, _overrides_key

    path = _configured_path()
    if path is None:
        # Do not retain an earlier active configuration after the environment
        # variable is removed.
        _overrides = {}
        _overrides_key = None
        return _overrides

    key = _file_key(path)
    if _overrides is not None and _overrides_key == key:
        return _overrides

    per_station = {}
    try:
        fp = open(path, "r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise StationDCBConfigurationError(
            "%s=%r cannot be opened: %s" % (CSV_ENV, path, exc)
        ) from exc

    with fp:
        reader = csv.DictReader(fp)
        fieldnames = set(reader.fieldnames or ())
        if "station" not in fieldnames:
            raise StationDCBConfigurationError(
                "%s is missing required 'station' column" % path
            )
        value_columns = [
            name for name in ("dcb_cal_ns", "dcb_ns") if name in fieldnames
        ]
        if not value_columns:
            raise StationDCBConfigurationError(
                "%s must contain 'dcb_cal_ns' or 'dcb_ns'" % path
            )

        for row_number, row in enumerate(reader, start=2):
            station = _normalise_station(row.get("station"))
            raw_value = None
            value_column = None
            for name in value_columns:
                candidate = (row.get(name) or "").strip()
                if candidate:
                    raw_value = candidate
                    value_column = name
                    break

            # Ignore a completely blank line, but reject partial rows so a
            # malformed calibration cannot be silently skipped.
            if not station and raw_value is None:
                continue
            if not station:
                raise _row_error(path, row_number, "missing station code")
            if len(station) != 4 or not station.isalnum():
                raise _row_error(
                    path,
                    row_number,
                    "station %r must be a four-character alphanumeric code"
                    % station,
                )
            if raw_value is None:
                raise _row_error(path, row_number, "missing DCB value")

            try:
                ns = float(raw_value)
            except ValueError as exc:
                raise _row_error(
                    path,
                    row_number,
                    "%s=%r is not numeric" % (value_column, raw_value),
                ) from exc
            if not math.isfinite(ns):
                raise _row_error(
                    path,
                    row_number,
                    "%s=%r must be finite" % (value_column, raw_value),
                )

            entry = per_station.setdefault(
                station, {"daily": {}, "values": []}
            )
            entry["values"].append(ns)

            raw_date = (row.get("date") or "").strip()
            if raw_date:
                try:
                    mjd = _date_to_mjd(raw_date)
                except StationDCBConfigurationError as exc:
                    raise _row_error(path, row_number, str(exc)) from exc
                if mjd in entry["daily"]:
                    raise _row_error(
                        path,
                        row_number,
                        "duplicate station/date entry for %s on %s"
                        % (station.upper(), raw_date),
                    )
                entry["daily"][mjd] = ns

    if not per_station:
        raise StationDCBConfigurationError(
            "%s contains no usable station DCB rows" % path
        )

    loaded = {}
    for station, entry in per_station.items():
        loaded[station] = {
            "mean": sum(entry["values"]) / len(entry["values"]),
            "daily": entry["daily"],
        }

    _overrides = loaded
    _overrides_key = key
    mode = _get_mode()
    print(
        "station_dcb_override: loaded %d station(s) from %s (mode=%s): %s"
        % (
            len(_overrides),
            path,
            mode,
            ", ".join(
                "%s=%+.3f ns" % (station.upper(), entry["mean"])
                for station, entry in sorted(_overrides.items())
            ),
        )
    )
    return _overrides


def has_override(station_code):
    """Return whether a calibrated DCB is available for ``station_code``."""
    return _normalise_station(station_code) in _load()


def get_override_ns(station_code, mjd):
    """Return the effective receiver DCB in ns, or ``None`` if unavailable."""
    entry = _load().get(_normalise_station(station_code))
    if entry is None:
        return None
    if _get_mode() == DAILY_MODE:
        return entry["daily"].get(int(mjd), entry["mean"])
    return entry["mean"]


def apply(bias_IONEX, bias_CODE_monthly, mjd_first, mjd_last):
    """Inject configured station DCBs into both legacy bias dictionaries.

    Dictionary values are stored in seconds. Only existing MJD entries are
    touched. The bounds are inclusive. The return value is the number of
    station/day pairs applied to at least one dictionary.
    """
    global _applied_originals

    # Persistent ALBUS dictionaries may still contain the preceding
    # configuration. Return them to their original state before loading and
    # applying the configuration that is active now.
    _restore_applied_values()
    overrides = _load()
    if not overrides:
        return 0
    _get_mode()  # Validate before mutating either dictionary.

    applied = {}
    changed_values = []
    try:
        for mjd in range(int(mjd_first), int(mjd_last) + 1):
            for station in overrides:
                ns = get_override_ns(station, mjd)
                if ns is None:
                    continue
                injected = ns * 1.0e-9
                touched = False
                seen_dictionaries = set()
                for dictionary in (bias_IONEX, bias_CODE_monthly):
                    if id(dictionary) in seen_dictionaries:
                        continue
                    seen_dictionaries.add(id(dictionary))
                    if mjd in dictionary:
                        station_biases = dictionary[mjd][1]
                        original = station_biases.get(station, _MISSING)
                        station_biases[station] = injected
                        changed_values.append(
                            (dictionary, mjd, station, original, injected)
                        )
                        touched = True
                if touched:
                    applied.setdefault(station, []).append(mjd)
    except Exception:
        _applied_originals = changed_values
        _restore_applied_values()
        raise

    _applied_originals = changed_values

    for station, mjds in sorted(applied.items()):
        print(
            "station_dcb_override: applied %s to %d day(s), MJD %d..%d"
            % (station.upper(), len(mjds), min(mjds), max(mjds))
        )
    return sum(len(mjds) for mjds in applied.values())
