cmake_minimum_required(VERSION 3.10)
project(JMA_code_Python)

#-----------------------------------------------------------------------------
# Define lists of files and modules
#-----------------------------------------------------------------------------

set(SRCS
  Albus_rnx3_to_rnx2.py
  Albus_Coordinates.py
  MS_Iono_agw_azel_par.py
  Albus_RINEX.py
  Albus_RINEX_2.py
  GPS_stations.py
  Albus_iono_object.py
  MS_Iono_functions.py
  jma_tools.py
)

set(MODULES
  Albus_rnx3_to_rnx2
  Albus_Coordinates
  MS_Iono_agw_azel_par
  Albus_RINEX
  Albus_RINEX_2
  GPS_stations
  Albus_iono_object
  MS_Iono_functions
)

set(PROG Albus_RINEX_download.py)
set(DATA gps_pos_default.snx)


find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_paths()[\"purelib\"])"
  OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
  OUTPUT_STRIP_TRAILING_WHITESPACE
)


execute_process(
    COMMAND "${Python3_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_path('scripts'))"
    OUTPUT_VARIABLE PYTHON_BIN_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)



install(
  PROGRAMS ${PROG}
  DESTINATION ${PYTHON_BIN_DIR}
)

install(
  FILES ${SRCS}
  DESTINATION ${PYTHON_SITE_PACKAGES}
)
#need to this file executable
install(CODE "execute_process(COMMAND chmod +x ${PYTHON_SITE_PACKAGES}/bin/Albus_RINEX_download.py)")


#string(REPLACE ";" " " MODULES_STR "${MODULES}")


