# ALBUS RINEX 2 Refactor Review

## Implementation status — 2026-09-22

The release-safe subset of this review has now been implemented. The detailed
issue descriptions below are retained as the comparison record against the
supplied original; descriptions of broken "current" behavior refer to the
pre-implementation working copy reviewed at that time.

| Area | Decision and implemented result |
|---|---|
| RINEX 2 parsing | Removed the receiver-brand-selected token parser. All observation records now use their specified 16-character fixed-width fields, so blanks and LLI/SSI characters retain their meanings. |
| Station DCB override | Kept as a separate helper. Added strict CSV/mode validation, campaign-mean and daily behavior, daily fallback to the campaign mean, finite-value and duplicate checks, station normalization, cache reload on file changes, restoration of previously injected values when configuration changes, and clear configured-path failures. |
| ALBUS integration | The helper is now a required import and is installed by CMake. Its DCB values are inserted into both legacy station-bias dictionaries in seconds before the existing correction function runs. |
| Binary cache | Legacy binary caches are bypassed for local RINEX input, disabled external DCBs, or an active station override because those inputs are absent from the old cache key. |
| Local RINEX input | A supplied local file is checked explicitly, and one file is limited to one requested MJD day instead of silently truncating a wider request. |
| Local code/phase leveling | Retained as experimental relative leveling, not an absolute receiver DCB. It no longer reports the station DCB flags as valid. A deeper per-arc redesign is deferred. |
| Legacy core | Restored original quiet and non-strict defaults. The only intentional legacy-algorithm change in this patch is making an explicitly requested missing-GPS-bias exception independent of debug logging; that check is used by the single-station DCB path. Other legacy findings remain deferred. |
| Regression tests | `test_station_dcb_override.py` and `test_rinex2_fixed_width.py` remain in the source release. They are intentionally excluded from the runtime CMake install list. |

Final-release decision for `test_station_dcb_override.py`: **keep it in the
source distribution as a regression test, but do not install it as an ALBUS
runtime module.** It protects the calibrated override and cache-bypass
contract without becoming a production dependency.

## Purpose and attribution method

This review separates the current implementation into:

1. **Your additions and modifications** — code present in the working copy but absent or different in the supplied original.
2. **Previously existing ALBUS code** — behavior already present in the supplied original, including legacy defects that your changes did not introduce.

Comparison baseline:

- Supplied original: `/Users/haydenstotts/Desktop/Albus_RINEX_2.py`
- Working copy: `ALBUS_ionosphere/Python/Albus_RINEX_2.py`
- Original SHA-256: `5ddf3d756ac7b6632da602ed0bc969d8c3955c6722562388e170f106ab457ca8`
- Working SHA-256 at review time: `fb2a2d0b80df586bf126f3e6db0b4843bda26fcc0ce240751b7760a1f36832b7`
- Original length: 4,812 lines
- Working length: 5,332 lines

Attribution is based on a direct diff against the supplied original, not on comments such as `NEW` or on assumptions about authorship. This is a focused review of changed functions and the legacy functions they depend on, not an exhaustive audit of every unchanged line in the original.

## Pre-implementation executive summary

The refactor should be split before more implementation work:

- Keep the original ALBUS processing core largely intact.
- Isolate the station-DCB override in `station_dcb_override.py` with two small, explicit hooks.
- Treat local RINEX input, variable sampling, Septentrio parsing, and local code/phase leveling as separate features with separate tests.
- Put legacy ALBUS bug fixes in their own patch so they are not confused with regressions introduced by the new features.

Four issues in the new code should be addressed first:

1. The Septentrio token parser corrupts valid fixed-width MK01 RINEX observations.
2. Binary cache names do not include the local input file or correction mode, so cached data can silently bypass the requested workflow.
3. The local code/phase leveling routine is not an absolute receiver-DCB estimator, but its result is reported as though all constellation biases were valid.
4. Daily station-DCB fallback is broken, and the new helper is omitted from the install manifest.

## Change inventory relative to the original

| Area | Classification | Summary |
|---|---|---|
| Module defaults and import-time prints | Your modification | `DEBUG_SET` changed from `False` to `True`; environment and path diagnostics now print on every import. |
| `_is_float_token` | Your new function | Token classifier used by the new Septentrio path. |
| `_parse_fixed_width_obs` | Your new function | Extracts the original fixed-width observation parsing into a helper, with changed loss-of-lock behavior. |
| `_parse_sept_token_obs` | Your new function | Adds whitespace-token parsing selected using vendor text in the header. |
| `read_RINEX_obs_file` | Existing function modified by you | Adds variable intervals, deferred antenna offsets, vendor detection, header satellite count handling, and parser dispatch. |
| `_compute_AzEl` | Existing function fixed by you | Corrects the original misspelling `AritmeticError` to `ArithmeticError`. |
| `DCB_bias_correction` | Existing function modified by you | Changes `raise_bias_error` default and adds a DCB diagnostic print. |
| `estimate_and_apply_local_code_bias` | Your new function | Adds per-satellite code-to-carrier leveling when external products are disabled. |
| `get_station_base_file` | Existing function modified by you | Adds direct local-RINEX-file input. |
| `get_station_base_observations` | Existing function modified by you | Adds local file input, external-DCB selection, local leveling, and station-override injection. |
| Binary/single/multiple wrappers | Existing functions modified by you | Propagate new options, change bias-error defaults, and bypass cache for configured station overrides. |
| `station_dcb_override.py` | Your new module | Loads calibrated receiver DCBs from CSV and injects them into the legacy dictionaries. |
| `test_station_dcb_override.py` | Your new test script | Checks campaign-mean identity and attempts to check daily fallback. |

# Part I — Your new and modified code

## What is already sound

- The station override is injected after normal CODE/IONEX loading, so it does not require changing the legacy DCB mathematics.
- The override writes the same seconds-valued receiver bias into both station dictionaries, avoiding the legacy `bias_in_dicts` source-precedence rule.
- The injection range covers the center and neighbor MJDs used by `bias_range_wrapper`.
- The campaign-mean synthetic identity check passes bit-for-bit against the natural published-station path.
- Deferring `ANTENNA: DELTA H/E/N` until `APPROX POSITION XYZ` becomes available is a reasonable compatibility improvement.
- Correcting `AritmeticError` to `ArithmeticError` in `_compute_AzEl` is a valid fix to an original typo.
- Appending optional arguments to the public wrappers is generally backward-compatible for callers that use the original positional arguments. The changed defaults are a separate compatibility concern described below.

## P0 — Remove or replace the vendor-selected token parser

**Your code:**

- `_is_float_token`, current lines 233-238
- `_parse_sept_token_obs`, current lines 290-351
- vendor detection and dispatch in `read_RINEX_obs_file`, current lines 462-474 and 823-845

The MK01 files are fixed-width RINEX 2.11 files. A comment containing `Septentrio` or a marker containing `SEPT` identifies the receiver vendor; it does not indicate a different observation-field grammar. The current code uses that vendor text to force token parsing.

This produces three confirmed parsing errors:

1. RINEX LLI/SSI characters can be attached to the 14-character numeric value when whitespace splitting is used. For example, a fixed-width value of `117868482.872` with LLI `0` and SSI `7` becomes the numeric token `117868482.87207`.
2. Blank observation fields disappear under `split()`, shifting subsequent tokens into the wrong observation types.
3. A standalone signal-strength digit is also treated as a generic nonzero lock-loss flag.

Evidence from `/Users/haydenstotts/ALBUS/albus_waterhole/MISC_RINEX/MK013650.25o`, first satellite record:

| Field | Correct fixed-width result | Current token result |
|---|---:|---:|
| `C1` | `22429600.520` | `22429600.520` |
| `L1` | `117868482.872` | `117868482.87207` |
| `L2` | `91845635.338` | `91845635.33805` |
| `S1` | `43.175` | missing |
| `S2` | `30.649` | missing |

Recommended change:

- Parse all RINEX 2 observation records by their specified 16-character field width, including Septentrio-produced files.
- Keep `_parse_fixed_width_obs` if extracting the old loop improves readability, but do not select a grammar from the receiver brand.
- If a genuinely nonconforming token-format file must be supported, detect it from structural evidence, preserve explicit blank-field positions, and add a dedicated fixture proving the exact field mapping. Do not infer it from `MARKER NAME` or `COMMENT`.
- Add golden tests using at least one MK01 epoch with blanks, LLI/SSI values, and continuation lines.

## P0 — Make binary caches configuration-aware or bypass them

**Your code:** `get_station_base_observations_with_bin`, current lines 4604-4681

The original cache key contains station and MJD range only. The new result can also depend on:

- `local_rinex_obs_file` path and contents;
- `use_external_dcb_files`;
- `estimate_local_dcb_if_missing`;
- override CSV contents;
- override mode and effective daily value.

Current consequences:

- Supplying a local RINEX file can return an older web-derived cache without reading the supplied file.
- A local-file result can be written under the same name as the web-derived result and affect later runs.
- A run requesting local leveling can receive externally corrected cached data, or vice versa.
- The current station-override bypass covers only a station found in the override CSV; it does not cover the other new modes.

Minimum safe change: force `use_bin_files = 0` whenever `local_rinex_obs_file` is supplied, external DCBs are disabled, local leveling is enabled, or a station override is active.

Longer-term change: store a cache metadata/fingerprint containing all correction inputs and reject cache entries whose fingerprint differs.

Also guard the override bypass with `use_external_dcb_files`; currently a configured override disables caching even when the caller has explicitly disabled external DCB use.

## P0 — Do not represent local code/phase leveling as an absolute DCB

**Your code:**

- `estimate_and_apply_local_code_bias`, current lines 2332-2406
- fallback branch in `get_station_base_observations`, current lines 3948-3965

The routine estimates one median `P4 - L4` offset per GPS satellite and shifts `P2`. That value combines code biases, phase ambiguity, and any cycle-slip/arc changes. It is useful as relative code-to-carrier leveling, but it is not a receiver DCB on the CODE datum.

Two correctness problems follow:

- The median is taken over the entire satellite day rather than over continuous phase arcs. Cycle slips or ambiguity resets can mix incompatible offsets.
- The fallback creates `bias_valid` as all ones. The comment says only GPS is valid and other constellations are unchanged, but all GPS, GLONASS, and Galileo flags are marked valid. More importantly, even the GPS flag should not mean “absolute station DCB available” if only relative leveling occurred.

Recommended change:

- Rename this feature to code/phase leveling and document it as relative.
- Return a distinct correction-status value instead of overloading `sta_bias_valid`.
- If the existing flag must be preserved temporarily, initialize it to zeros and set only the explicitly defined status; do not mark unsupported constellations valid.
- Estimate offsets per continuous phase arc using existing loss-of-lock/block information, then define how multiple arcs are combined.
- Add synthetic tests with a known cycle slip, missing P1 with C1 fallback, insufficient samples, and multiple satellites.
- Remove the unused `station_code` argument unless it is used in diagnostics or result metadata.

## P0 — Complete the station-DCB helper integration

**Your code:** `station_dcb_override.py`, the two core hook sites, the test, and `CMakeLists.txt`

### Daily fallback defect

`get_override_ns` documents a campaign-mean fallback for a missing daily value, but currently returns `None`:

```python
return entry["daily"].get(int(mjd))
```

Use:

```python
return entry["daily"].get(int(mjd), entry["mean"])
```

The supplied test currently passes the campaign-mean identity check and then crashes with a `TypeError` at its missing-day check.

### Install defect

`station_dcb_override.py` is not listed in `CMakeLists.txt` `SRCS`. Installed copies therefore receive `Albus_RINEX_2.py` without the imported helper. Because both hook sites catch `ImportError` and do nothing, the installed program can silently omit a configured correction.

Add the helper to `SRCS` and to `MODULES` if that unused list is retained. Add a staged-install import smoke test.

### Fail-closed configuration

No environment variable should remain a no-op. If `ALBUS_STATION_DCB_CSV` is explicitly set, a missing helper, missing CSV, missing required headers, empty usable dataset, or invalid/non-finite DCB should stop processing with a precise error. Silent uncorrected output is unsafe here.

## P1 — Restore quiet defaults and make strictness explicit

**Your modifications:**

- `DEBUG_SET = True`, current line 8
- import-time environment prints, current lines 44-54
- `raise_bias_error` defaults changed from `0` to `1` in the DCB function and public wrappers
- per-day observation diagnostic loops, current lines 3909-3930
- DCB print nested under the Galileo-missing branch, current lines 2321-2323

These changes alter normal library behavior, generate large output, expose environment details, and can turn formerly accepted missing-bias runs into failures. Import-time `os.getuid`/`os.geteuid` also reduces portability.

Recommended change:

- Restore `DEBUG_SET = False`.
- Remove import-time prints and the unconditional observation scan.
- Route optional diagnostics through one logging/debug mechanism.
- Restore original public defaults unless a deliberate breaking API change is documented and tested.
- Fix the legacy `raise_bias_error` logic separately as described in Part II.
- Move the GPS-bias status message out of the “Galileo bias missing” block if it is retained.

## P1 — Define station-override configuration lifetime

**Your code:** `station_dcb_override.py` plus mutation of the legacy static dictionaries

`_overrides` loads once. If an early call occurs without the environment variable, setting it later has no effect. Changing or unsetting the path continues to use old values.

The helper also mutates persistent dictionaries owned by `get_station_base_observations`. Resetting only `_overrides` does not remove values injected into those dictionaries.

For the current command-line workflow, the simplest safe contract is: path and mode are immutable for the process lifetime, and a different calibration requires a new process. Document and validate that contract.

For notebooks or services, add a public reload/reset API and either clear the core dictionaries or apply overrides to per-call copies. Tests should not write the private `_overrides` variable directly.

## P1 — Validate local-file time-range behavior

**Your code:** `get_station_base_observations`, current lines 3767-3770

When a local file is supplied, the requested range is silently reduced to one day. This is acceptable only if the public contract explicitly says one local file equals one requested day.

Recommended change:

- Reject multi-day requests with a clear message, or accept a date-to-file mapping/list.
- Verify that the file date matches the requested day.
- Bypass or fingerprint binary caches as described above.
- Document the option in every wrapper that exposes it.

## P2 — Separate interval support from parser work

**Your code:** `read_RINEX_obs_file`, current lines 424-429 and 611-625

Respecting a RINEX `INTERVAL` value may be desirable, but it changes a major original invariant: ALBUS formerly forced a 30-second grid and interpolated undersampled input. This change should not be coupled to Septentrio parsing.

Keep it only after regression tests cover:

- 1-, 10-, 15-, 30-, and 60-second input;
- missing `INTERVAL` header;
- gaps and irregular timestamps;
- one-day boundary allocation;
- downstream phase blocks, satellite interpolation, binary serialization, and multiple-station MJD comparison.

Make the policy a function argument or configuration value rather than the local constant `FORCE_STANDARD_30S = False`.

## P2 — Remove the header satellite-count allocation change unless proven necessary

**Your code:** `read_RINEX_obs_file`, current lines 757-768

RINEX `# OF SATELLITES` describes distinct satellites in the file; `max_sat` is used as the per-epoch observation-slot dimension. Increasing the per-epoch dimension to total distinct satellites plus one is not needed to represent `Sat_array` values and can increase memory/cache sizes.

Retain this only with a fixture that fails without it and a clear explanation of the required invariant.

## P2 — Refactor and validate the override CSV loader

**Your code:** `station_dcb_override.py`

- Accept only `campaign-mean` and `daily`; mode typos currently fall back silently to campaign mean.
- Normalize lookup arguments with `strip().lower()`.
- Validate documented station-code length or document the broader accepted form.
- Reject or explicitly resolve duplicate `(station, date)` rows. Daily mode currently keeps the last value while campaign mean counts all duplicates.
- Reject `nan` and `inf` with `math.isfinite`.
- Open with `newline=""` and an explicit encoding such as `utf-8-sig`.
- Include path, row, field, and value in parse errors.
- Reduce one-line-per-station-per-day output or put it behind verbose logging.

## P2 — Make tests isolated and discoverable

**Your code:** `test_station_dcb_override.py`

The current script has no `test_*` functions or `unittest.TestCase`, so normal test discovery does not execute it. It also edits the environment and a private cache without guaranteed cleanup after failure; the observed daily-mode crash bypassed its cleanup.

Use `unittest` if no additional test dependency is desired. Split behaviors into independent tests with cleanup/finally handling. Add:

- golden fixed-width MK01 parsing tests;
- parser tests with blanks and LLI/SSI characters;
- local-file/cache isolation tests;
- correction-mode/cache isolation tests;
- code/phase leveling tests with cycle slips;
- station override daily fallback and invalid-config tests;
- a mocked test that proves each `Albus_RINEX_2` hook calls or bypasses the helper correctly;
- a staged-install import test.

The current station test calls `ovr.apply` directly. It proves compatibility with `DCB_bias_correction`, but it does not exercise the actual `get_station_base_observations` hook or the binary-cache hook.

## P3 — Remove commented-out duplicate definitions

Several original signatures and calls were commented out above the new definitions. Version control already preserves them. Removing these blocks will make the actual API and diff easier to inspect without changing runtime behavior.

# Part II — Previously existing ALBUS functions and issues

The issues below exist in the supplied original. They should not be attributed to the new helper or parser work. Fix them in separate commits with focused regression tests.

## P0 legacy — Galileo DCB correction uses the wrong frequency variable

**Existing function:** `DCB_bias_correction`

For Galileo satellites, the original assigns `nu_5 = nu_E5_Gal`, but the correction later always uses `nu_2`. Because the loop previously processed GLONASS satellites, Galileo can use the stale GLONASS `nu_2` value.

This is an original core correctness issue. Fix the constellation-specific carrier-frequency selection in a dedicated legacy patch and add GPS/GLONASS/Galileo synthetic tests.

## P1 legacy — `raise_bias_error` is incorrectly controlled by debug mode

**Existing function:** `DCB_bias_correction`; original lines 2094-2098

The original raises only when both `DEBUG_SET` and `raise_bias_error` are true:

```python
if DEBUG_SET and raise_bias_error:
```

The public parameter therefore does nothing when normal debug mode is off. Debug should control the diagnostic print, not whether a requested correctness exception occurs.

Recommended legacy fix:

```python
if raise_bias_error:
    if DEBUG_SET:
        print(...)
    raise ...
```

Your change to make debug true and strict defaults one happened to expose this older coupling; it did not create the coupling.

## P1 legacy — `get_station_base_file` reports download failure using undefined `m`

**Existing function:** `get_station_base_file`; original line 3322

The exception message formats `m`, which is not defined in that function. A download failure can therefore raise `NameError` and hide the intended `No_RINEX_File_Error`. Use the normalized `MJD` variable.

## P1 legacy — Observation-file open failure can be masked in `finally`

**Existing function:** `read_RINEX_obs_file`

If `open` fails before `fp` is assigned, the outer `finally: fp.close()` can raise another error and obscure the intended file-open exception. Initialize `fp = None` and close conditionally, or use a context manager.

## P1 legacy — `bias_range_wrapper` hides the original exception

**Existing function:** `bias_range_wrapper`

The bare `except` converts every error into a generic `RINEX_Data_Barf`, losing the failing MJD/key and traceback. Catch expected lookup errors explicitly and chain the original exception with contextual data.

## P2 legacy — The original parser discards an entire satellite record on any lock/missing-data flag

**Existing function:** `read_RINEX_obs_file`

The original sets loss-of-lock for several missing or flagged observations and then replaces the entire satellite row with `BAD_DATA_CODE`. Your parser refactor removed this wholesale discard, which may recover useful fields, but that policy change was mixed with the broken token parser.

Handle this as a separate legacy behavior change:

- retain correctly parsed fixed-width values;
- keep LLI separate from SSI;
- define exactly which downstream algorithms exclude flagged phase values;
- test partial records and real cycle slips.

## P2 legacy — Static DCB dictionaries make run state persistent

**Existing function:** `get_station_base_observations`

The original stores downloaded DCB dictionaries as function attributes. That improves reuse but makes behavior dependent on earlier calls. The station override makes this more visible because it mutates those same dictionaries.

Do not redesign this inside the first override patch. Either document process-level state or later introduce an explicit context/cache object in a separate core refactor.

## P2 legacy — The reset sentinel does not return after clearing state

**Existing function:** `get_station_base_observations`

The documented `MJD_start=0`, `MJD_end=0`, `station_code='////'` path clears dictionaries but then continues through normal date and file processing. If this path is used, return immediately after clearing.

## P3 legacy — Additional original cleanup candidates

These are lower priority and should remain separate from feature work:

- `SBAS_warned` is initialized, but the branch assigns `SBAS_warn`, so warnings may repeat.
- The shell-based `crx2rnx` command does not safely handle paths containing spaces or shell metacharacters.
- Numerous invalid backslash escapes in legacy docstrings emit `SyntaxWarning` under current Python.
- Some documentation contains spelling errors and no longer states all effective assumptions.

# Recommended refactor boundaries

Use separate changesets in this order:

1. **Regression safety:** add golden tests for original fixed-width parsing and current MK01 fixtures.
2. **Parser correction:** keep fixed-width RINEX parsing, preserve partial records deliberately, and remove vendor-selected token parsing.
3. **Local-file input:** add the file option with explicit one-day semantics and cache bypass/fingerprinting.
4. **Station DCB override:** fix daily fallback, validation, install packaging, and hook tests while keeping the two core hook sites small.
5. **Local code/phase leveling:** define relative—not absolute—semantics, per-arc handling, and separate status reporting.
6. **Variable interval support:** enable only after downstream interval regression tests.
7. **Legacy fixes:** Galileo frequency, debug-gated exceptions, undefined error variable, exception chaining, and reset behavior.
8. **Cleanup:** remove debug prints, commented-out old definitions, and formatting noise.

Suggested module boundaries:

- `Albus_RINEX_2.py`: legacy algorithms plus narrowly defined calls into helpers.
- `station_dcb_override.py`: calibrated external receiver-DCB loading, validation, and application.
- `rinex2_observation_parser.py`: fixed-width record parsing and fixture-based tests, if extracting it is worthwhile.
- `local_code_phase_leveling.py`: explicitly relative code/phase leveling, arc handling, and its tests.

# Verification performed

- Direct diff and function inventory against the supplied original.
- The modified modules compile in the project Python environment.
- Nine focused unit tests pass: eight station-override/configuration/cache tests and one fixed-width RINEX record test.
- The campaign-mean override produces observation data bit-for-bit identical to the natural published-station DCB path in the synthetic correction test.
- Daily mode uses the exact dated value and falls back to the station campaign mean when that date is absent.
- Missing files, malformed rows, invalid modes, duplicate dates, and non-finite values fail clearly.
- The CMake runtime source list includes `station_dcb_override.py` and excludes the two regression-test files.
- The real MK01 file `/Users/haydenstotts/ALBUS/albus_waterhole/MISC_RINEX/MK013650.25o` parses on its declared 10-second grid (8,640 epochs) with its fixed-width observation values preserved.
- A single-station MK01 run with a calibrated daily override completes through the normal DCB correction path, marks the GPS receiver bias valid, and stores `-0.423 ns` as `-4.23e-10 s` in the legacy bias dictionaries.

# Acceptance criteria

- Valid fixed-width MK01 observations map to the correct fields, including blanks, continuation lines, LLI, and SSI.
- No parser mode is selected solely from receiver/vendor text.
- Local files and correction modes cannot reuse or overwrite incompatible binary caches.
- Relative code/phase leveling is not reported as an absolute published/calibrated DCB.
- Daily station overrides fall back to campaign mean as documented.
- An explicitly configured invalid override fails clearly.
- Installed ALBUS includes and imports `station_dcb_override.py`.
- With all new options disabled, behavior matches the supplied original except for separately documented legacy bug fixes.
- Legacy fixes have independent tests and commits, so responsibility and regression risk remain clear.
