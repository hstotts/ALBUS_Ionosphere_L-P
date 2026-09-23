This software determines the ionosphere total electron content (TEC) over any 
location on the Earth as a function of location and time. It then
uses the TEC and a model of the Earth's magnetc field to compute the 
ionosphere's effect on the Faraday Rotion Meaure (RM) observed for an
astronomical radio source. The ionosphere's contribution to the RM can
then be renoved.  The software may be of interest to both radio astronomers 
and to ionosphere scientists. Test observations suggest that our analysis 
gives results consistent with those found by on-site site experiments that 
used local GPS receivers. 

The software derives the TEC of the ionosphere by using publicly available 
observation data of Global Positioning System (GPS) satellites. It
searches through a database of several thousand ground-based GPS receivers and
then gets GPS receiver data from those stations located within a specified 
distance of the position of the telescope being used for the radio 
astronomy observation.

In principle, the Faraday rotation angle is a function of source
direction and antenna position, but Faraday rotation is usually 
a large-scale effect and it may have approximately the same value across 
an entire telescope primary beam field of view (perhaps about one degree). 
For arrays smaller than a few kilometres, the rotation angle will usually
also be the same for all stations. These assumptions reduce the number of 
independent parameters considerably, but they may  break down as the observing 
 wavelength gets longer due to the wavelength squared effect and increasing 
field of view, as well as when telescope arrays have longer baselines.

In reality, from the ground we usually cannot directly measure the 
distribution of the electrons along the line of sight nor directly measure 
the magnetic field strength as a function of position and direction. 
In order to calculate a rotation measure, many routines place all the electrons
at some "standard" height and attach a magnetic field value from a model of the
terrestrial field. In contrast, the software that we describe goes beyond
this simple algorithm by distributing the electrons along the line of sight
taking into account modern understanding of ionospheric physics, and employs a
model of the terrestrial magnetic field that accounts for change of intensity
and direction with height.

The software makes extensive use of Python scripts. This branch uses the
Python 3 `pyproject.toml`, CMake, and scikit-build workflow and is not intended
for Python 2.

You need to install pycurl, astropy, pyephem or python casacore, numpy 
and matplotlib for the system to work. A number of support programs to handle 
RINEX files are also needed. These programs are specified in the INSTALL 
file.

More sites (especially Geosciences Australia) are now producing only RINEX3 files. 
For analysis, we use RINEX2 files. To convert RINEX3 to RINEX2 you need to get 
and install gfzrnx, available from https://gnss.gfz-potsdam.de/services/gfzrnx
and RX3name (see http://acc.igs.org/software.html) Unfortunately these programs 
seem to be available only in binary format.

Unfortunately, due to security concerns, sites are also changing access methods 
from simple anonymous ftp to more secure procedures such as sftp etc and we are
currently working on modifying our access procedures to reach such sites.
secure access procedures 

A somewhat more detained description of the software is given in
the, as yet, unpublished paper twillis_ALBUS_paper.pdf available in
this directory.

## Platform support in this branch

This branch differs from earlier ALBUS versions because the mixed Python,
C/C++, and Fortran build has been migrated to modern macOS systems. The
packaging now uses `pyproject.toml`, CMake, and scikit-build to produce the
native Python extension for the host platform.

| Platform | Current status |
|---|---|
| Intel macOS | Supported by the migration work, using a GNU compiler stack, OpenBLAS/LAPACKE, and Flex supplied by MacPorts or an equivalent package manager. |
| Apple Silicon macOS | Supported by the migration work. The tested setup used Homebrew GCC/G++/GFortran 15, OpenBLAS/LAPACKE, and Flex, together with NumPy 2.x-compatible C++ changes and legacy Fortran compatibility flags. |
| Native Linux with `pip install .` | Expected to be the smaller port because ALBUS already uses GNU C/C++/Fortran and Unix runtime conventions, but the current pip build has not been validated on Linux. The items below must be completed before Linux is declared supported. |
| Native Windows | **Not currently supported or verified by this branch.** The same source checkout should not be expected to build or run natively on Windows without additional porting. |
| Windows with WSL2 | WSL2 can use the future native-Linux pip procedure and is the lowest-risk Windows route. It is not a substitute for a native Windows wheel and has not yet been validated for this release. |

### Reproducing this branch's station-DCB results on Windows

The native-build warning above applies to this complete macOS branch. It does
not prevent the platform-neutral station-DCB feature from being added to an
ALBUS checkout that already builds and runs on Windows. The recommended
Windows starting point is the current working
[`ratt-ru/ALBUS_ionosphere`](https://github.com/ratt-ru/ALBUS_ionosphere)
checkout; do not replace it with this complete macOS tree.

To reproduce the calibrated station-DCB processing path, add or merge these
files from this branch into the Windows checkout:

1. Add `ALBUS_ionosphere/Python/station_dcb_override.py` in full.
2. Merge the result-producing changes from
   `ALBUS_ionosphere/Python/Albus_RINEX_2.py`. These include the override
   import and application, override/local-input cache bypass, one-day local
   RINEX support, native 10-second sampling, fixed-width RINEX 2 observation
   parsing, deferred `ANTENNA: DELTA H/E/N` handling, and the explicit
   missing-DCB error check. Do not replace the complete upstream file without
   reviewing its newer Windows changes.
3. Add `station_dcb_override.py` to `SRCS` and `MODULES` in
   `ALBUS_ionosphere/Python/CMakeLists.txt` so `pip install .` installs it.
4. Supply the same calibration CSV used for the reference run. It must contain
   `station`, `date`, and either `dcb_cal_ns` or `dcb_ns` as described below.

The current local-file campaign scripts also use `ALBUS_LOCAL_RINEX` and
`ALBUS_LOCAL_STATION`. If that workflow is required, port only a cleaned-up
local-file/station selection hook from `MS_Iono_functions.py` that passes the
local filename into `Albus_RINEX_2`. Do not copy the complete development
version of `MS_Iono_functions.py`, which contains campaign-specific diagnostics
and station defaults. This extra hook is not required when the Windows run
uses ALBUS's normal station selection and RINEX download path.

For the same final numerical result, code alone is not sufficient. Use the
same RINEX observation file, station-DCB CSV, IONEX product, SP3/orbit product,
processing dates and options. For PIM calculations covering the 2025--2026
campaign, also update both model-input files from this branch:

- `ALBUS_ionosphere/FORTRAN/PIM/PIM_1.7/noaa_dat/IMF24.dat`
- `ALBUS_ionosphere/FORTRAN/PIM/PIM_1.7/noaa_dat/kpf107.dat`

Keep the Windows repository's native-build files, `GPS_stations.py`, and
download implementation unless a separate Windows-specific fix is required.
In particular, do not copy the macOS compiler paths, GFZRNX signing wrapper,
virtual environment, build directory, `.DS_Store` files, local `run.txt`, or
files containing absolute `/Users/...` paths.

Add the following source-only regression tests as part of the Windows feature
merge, but do not install them as runtime modules:

- `ALBUS_ionosphere/Python/test_station_dcb_override.py`
- `ALBUS_ionosphere/Python/test_rinex2_fixed_width.py`

Passing these tests plus one end-to-end run using the same input products is
the acceptance check for equivalent station-DCB results. Small last-digit
floating-point differences between compiler platforms may still occur.

### Supported distribution method

The supported build direction for this branch is the PEP 517 pip workflow:

```bash
python -m pip install .
```

The repository's `Dockerfile` and `Jenkinsfile.sh` belong to the older Docker
workflow that was phased out before the Intel and Apple Silicon migrations.
They are already excluded from the source distribution by `pyproject.toml` and
must not be treated as a supported installation, test, or Windows-compatibility
path for this version.

### Portability audit and required changes

The station DCB override itself is pure Python and uses platform-neutral
`os.path`, `csv`, and date handling. It does not add a Linux or Windows porting
requirement. The remaining portability work is in the native build, package
layout, data lookup, and external-command workflows.

| Area and affected files | Required for native Linux pip support | Additional work required for native Windows |
|---|---|---|
| Python build metadata: `pyproject.toml` | Align `requires-python` with `numpy>=1.26` instead of advertising Python 3.6, then test the declared Python/NumPy combinations in clean environments. | Use the same supported Python range and confirm that every runtime dependency provides a Windows wheel or has a documented native build prerequisite. |
| Compiler selection: `ALBUS_ionosphere/include/JMA_math.h`, `ALBUS_ionosphere/FORTRAN/IRI/CMakeLists.txt`, and the top-level CMake files | Test with GCC, G++, and GFortran. Apply `-std=legacy` and `-fallow-argument-mismatch` only when the Fortran compiler is GNU instead of overwriting global flags. | Choose and support one toolchain. The lowest-change option is MinGW-w64/MSYS2 GCC, G++, and GFortran because `JMA_math.h` currently rejects non-GCC compilers. Supporting MSVC would require removing that GCC-only guard, resolving GNU-specific C/C++ constructs, and pairing MSVC with a compatible Windows Fortran compiler. |
| OpenBLAS/LAPACKE discovery: top-level `CMakeLists.txt` and `ALBUS_ionosphere/C++/mim/test/PIMrunner/CMakeLists.txt` | Remove `/opt/homebrew` and `/opt/local` assumptions. Use cache variables or imported CMake/pkg-config targets and verify the Linux OpenBLAS/LAPACKE development package. | Locate a Windows OpenBLAS/LAPACKE build through the selected toolchain or package manager and link its imported target. Do not assume Unix library names or directories. |
| Flex/Bison and runtime libraries: `vex2005/CMakeLists.txt` and the root link list | Discover Flex and Bison normally and link a discovered Flex target/library rather than the raw name `fl`. Let CMake carry the Fortran runtime rather than hard-coding `gfortran`; link `m` only on Unix. | Use toolchain-compatible Flex/Bison (for example the MSYS2 versions for a MinGW build). Generated scanner code may need `YY_NO_UNISTD_H` or an equivalent Windows guard. Remove the Unix-only `fl`, `gfortran`, and `m` assumptions. |
| Python/scikit-build installation: root, `ALBUS_ionosphere`, `Python`, and library `CMakeLists.txt` files | Install extension modules, shared libraries, Python modules, and `libdata` relative to scikit-build's install prefix instead of calculating and writing directly to the active interpreter's absolute `site-packages`. Remove the post-install `chmod`. | Add `RUNTIME DESTINATION` for the `.pyd` and dependent `.dll` files. Either export the symbols required by dependent shared libraries (`WINDOWS_EXPORT_ALL_SYMBOLS` or explicit export macros) or link the internal ALBUS libraries statically into the Python module. Do not run `chmod`. |
| Runtime library lookup: every CMake target using `INSTALL_RPATH "$ORIGIN"` | Keep `$ORIGIN` for Linux and install all ALBUS `.so` dependencies beside the extension. Decide whether pip builds require a local system OpenBLAS/GFortran runtime or a repaired, self-contained wheel. | Windows has no RPATH. Place required ALBUS DLLs beside the `.pyd` (or use static internal libraries) and ensure OpenBLAS and compiler-runtime DLLs are discoverable. |
| Packaged model data: `ALBUS_ionosphere/CMakeLists.txt`, `ionosphere_iri.h`, `ionosphere_pim.h`, and `pim_runner.h` | Stop compiling the source-tree `INSTALLDIR` into the binaries. Install `libdata` inside the wheel and resolve it relative to the installed package or through one explicit runtime data-directory setting. | Use the same package-relative lookup; compiled Unix-style source paths are not valid installation locations on Windows. |
| Filesystem and process calls: `Albus_RINEX.py`, `Albus_RINEX_2.py`, `Albus_RINEX_clean.py`, `Albus_rnx3_to_rnx2.py`, and `MS_Iono_functions.py` | Replace shell-constructed commands where practical so filenames with spaces are safe. Linux still provides the current commands, but direct `subprocess` argument lists are more reliable. | Replace `/bin/rm`, `mv`, `gunzip`, `unzip`, shell wildcards, and `>` redirection with `pathlib`, `shutil`, `gzip`, `zipfile`, and `subprocess.run(..., check=True)` using argument lists and explicit output file handles. Replace `os.system('date')` with Python datetime logging. |
| User and executable paths: `GPS_stations.py`, `Albus_RINEX.py`, and external-tool callers | Replace required `HOME`/`PYTHONPATH` indexing and `/usr/local/bin/RX3name` with `Path.home()`, package resources, `os.pathsep`, `shutil.which()`, or explicit configuration. | These changes are mandatory because Windows may not define `HOME`, uses different default directories, and resolves `.exe` programs through `PATH` rather than `/usr/local/bin`. |
| External RINEX programs: GFZRNX, RX3name, RNXCMP/`crx2rnx`, ResCor, and RinexDump workflows | Install or document Linux builds and add startup checks that report exactly which executable is missing. | Obtain compatible Windows executables or port the required tools, normalize executable discovery, and test their command-line/output behavior. The macOS GFZRNX signing wrapper is not portable to Windows. |
| Build scope: native-library CMake files currently build several legacy test/example executables during a package build | Add an `ALBUS_BUILD_LEGACY_TOOLS` option, default it off for pip builds, and build only libraries and programs needed at runtime. | This reduces the Windows port surface substantially; any retained executable must receive its own Windows compile and runtime test. |
| Validation and release | Add a clean Linux pip-build job, import smoke test, unit tests, and one end-to-end single-station RINEX/DCB run. Inspect the resulting wheel for unresolved `.so` dependencies. | Add the equivalent native Windows job and inspect the wheel for missing DLLs. Test paths containing spaces, temporary files, downloads, RINEX conversion, station DCB override modes, and a full single-station run before publishing a Windows support claim. |

### Practical implementation order

1. Make the pip/CMake install destinations package-relative and make model-data
   lookup relocatable. This is shared work for Linux and Windows.
2. Replace hard-coded macOS library paths and raw `fl`, `gfortran`, and `m`
   linkage with platform-conditional discovered targets.
3. Validate `pip install .` and the single-station regression suite on native
   Linux. At that point Linux and WSL2 support can be documented as tested.
4. Replace the POSIX shell operations and hard-coded executable/home paths with
   Python and configurable executable discovery.
5. Add Windows DLL installation/export handling, select the native Windows
   compiler stack, and validate a Windows wheel end to end.

Until those acceptance tests exist, the correct release labels are:

- **macOS: supported by this migration;**
- **Linux/WSL2: plausible through the pip source build, but unverified;**
- **native Windows: unsupported and requires the port above.**

On Apple Silicon, the distributed GFZRNX executable may also require its
PAR-packed `.bundle` libraries to be extracted into a persistent directory and
ad-hoc signed. A wrapper can set `PAR_GLOBAL_TEMP` to that directory and sign
newly extracted bundles before launching GFZRNX. This workaround is specific
to macOS code signing and is not part of a Windows setup.

## Calibrated station DCB overrides

[`station_dcb_override.py`](ALBUS_ionosphere/Python/station_dcb_override.py)
allows a locally calibrated receiver differential code bias (DCB) to replace
the receiver value obtained from the normal
IONEX/CODE products. The satellite DCBs still come from the normal external
products, and the existing ALBUS DCB correction mathematics is unchanged.

The override is inactive unless `ALBUS_STATION_DCB_CSV` is set. CSV values are
in nanoseconds on the CODE P1-P2 datum. The file must contain:

- `station`: a four-character alphanumeric station code;
- either `dcb_cal_ns` or `dcb_ns`: a finite DCB value in nanoseconds; and
- optionally `date`: an ISO date in `YYYY-MM-DD` form.

For example:

```csv
date,station,dcb_cal_ns
2025-12-30,MK01,-0.412
2025-12-31,MK01,-0.423
```

Configure the override before starting ALBUS:

```bash
export ALBUS_STATION_DCB_CSV=/absolute/path/to/station_dcb.csv
export ALBUS_STATION_DCB_MODE=daily
```

In Windows PowerShell, set the same options as follows:

```powershell
$env:ALBUS_STATION_DCB_CSV = "C:\path\to\station_dcb.csv"
$env:ALBUS_STATION_DCB_MODE = "daily"
```

For an explicitly selected local RINEX file, the cleaned-up Windows integration
described above may additionally use:

```powershell
$env:ALBUS_LOCAL_RINEX = "C:\path\to\mk012300.25o"
$env:ALBUS_LOCAL_STATION = "MK01"
```

`ALBUS_STATION_DCB_MODE` accepts two values:

- `campaign-mean` (the default) uses the mean of all rows for each station;
- `daily` uses the value for the requested date and falls back to that
  station's campaign mean when the date is absent.

The override is applied only on the external-DCB processing path, so API calls
must keep `use_external_dcb_files=1`. Runs using a configured station override
automatically bypass the legacy binary observation cache because its filename
does not encode the calibration source. Invalid modes, unreadable CSV files,
malformed rows, duplicate station/date rows, and non-finite values stop the run
with a configuration error rather than silently producing uncorrected output.

To disable the feature, start a new process without these variables or unset
them before the next call:

```bash
unset ALBUS_STATION_DCB_CSV ALBUS_STATION_DCB_MODE
```

In PowerShell:

```powershell
Remove-Item Env:ALBUS_STATION_DCB_CSV -ErrorAction SilentlyContinue
Remove-Item Env:ALBUS_STATION_DCB_MODE -ErrorAction SilentlyContinue
```

The source-release regression tests are
[`test_station_dcb_override.py`](ALBUS_ionosphere/Python/test_station_dcb_override.py)
and
[`test_rinex2_fixed_width.py`](ALBUS_ionosphere/Python/test_rinex2_fixed_width.py).
They are intentionally not installed as runtime modules.

## Installation on macOS - adapted from ratt-ru
**We strongly recommend using a clean python virtual environment for the installation process
and advise against installing this package into system folders as the installation process may
not currently be fully reversable without manual intervention.**

***Installation on macOS requires MacPorts, Homebrew, or an equivalent source
of the GNU C/C++/Fortran compilers, OpenBLAS/LAPACKE, and Flex. The commands
below show the Intel MacPorts layout. Apple Silicon installations should use
the corresponding Homebrew paths and versioned compiler executables.***

1. Clone this branch (download the repository locally):
   ```bash
   git clone https://github.com/hstotts/ALBUS_Ionosphere_L-P.git
   ```

2. Navigate into the project directory:
   ```bash
   cd ALBUS_Ionosphere_L-P
   ```

3. Create and activate a Python virtual environment (isolates project dependencies):
   ```bash
   python -m venv albus_env
   source albus_env/bin/activate
   ```

4. Update Python packaging tools and install required Python dependencies:
   ```bash
   pip install --upgrade pip setuptools wheel build
   pip install numpy astropy matplotlib ephem pycurl requests
   ```

5. Configure compilers and library paths from MacPorts (required for building native code and linking OpenBLAS):
   ```bash
   export CC=/opt/local/bin/gcc-mp-11
   export CXX=/opt/local/bin/g++-mp-11
   export FC=/opt/local/bin/gfortran-mp-11
   export CPATH=/opt/local/include:/opt/local/include/openblas
   export LIBRARY_PATH=/opt/local/lib
   export DYLD_LIBRARY_PATH=/opt/local/lib
   ```

6. Build and install the ALBUS package with CMake configuration for OpenBLAS and Fortran support:
   ```bash
   CMAKE_ARGS="\
   -DCMAKE_BUILD_TYPE=Release \
   -DCMAKE_Fortran_FLAGS='-std=legacy -fallow-argument-mismatch' \
   -DCMAKE_INCLUDE_PATH=/opt/local/include;/opt/local/include/openblas \
   -DCMAKE_LIBRARY_PATH=/opt/local/lib \
   -DLAPACKE_LIB=/opt/local/lib/libopenblas.dylib \
   " \
   pip install .
   ```

   **Editable (`-e`) installations are not currently supported**

7. Install `meerkat_moon.py`, `RX3Name`, `GFZRNX`, and `C2RNX`, and place them in the correct locations. Update CDDIS .netrc in home directory if needed. More information on this step will be added soon.

8. Set required runtime environment variables for ALBUS execution:
   ```bash
   export PATH="$HOME/ALBUS_LOCAL_PIP:$PATH"
   export PYTHONPATH="$HOME/ALBUS_LOCAL_PIP:$PYTHONPATH"
   export ALBUS_TESTCASE_OUTPUT="$HOME/ALBUS_LOCAL_PIP/albus_waterhole"
   ```

9. Run the program with the test RINEX file and station configuration:
   ```bash
   MPLBACKEND=agg \
   ALBUS_LOCAL_RINEX=$HOME/ALBUS_LOCAL_PIP/albus_waterhole/suth3650.25o \
   ALBUS_LOCAL_STATION=SUTH \
   ALBUS_USE_EXTERNAL_DCB=0 \
   python $HOME/ALBUS_LOCAL_PIP/albus_waterhole/meerkat_moon.py
   ```

**Note that the user still needs to compile and install RINEXCMP and have gfzrnx and RX3name in the PATH before running**















