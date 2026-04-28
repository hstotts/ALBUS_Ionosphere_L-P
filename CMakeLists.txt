cmake_minimum_required(VERSION 3.10)
project(AlbusIonosphere LANGUAGES CXX)

# 1. Get environment variables or fallback to defaults
set(ALBUS_PATH $ENV{ALBUS_PATH} CACHE PATH "Path to ALBUS install")
set(INSTALLDIR $ENV{ALBUS_PATH} CACHE PATH "Path to ALBUS install")
set(MAJOR_VERSION $ENV{MAJOR_VERSION} CACHE STRING "Major version")
set(MINOR_VERSION $ENV{MINOR_VERSION} CACHE STRING "Minor version")

# 2. Find Python and NumPy FIRST so Python3_EXECUTABLE is defined before use
find_package(Python3 REQUIRED COMPONENTS Interpreter Development NumPy)

# Get NumPy include path dynamically
execute_process(
  COMMAND ${Python3_EXECUTABLE} -c "import numpy; print(numpy.get_include())"
  OUTPUT_VARIABLE NumPy_INCLUDE_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

include_directories(${NumPy_INCLUDE_DIR})

# 3. Include directories for headers
include_directories(
    ${Python3_INCLUDE_DIRS}
    ${Python3_NumPy_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/ALBUS_ionosphere/C++/vex_to_sky2
    ${CMAKE_CURRENT_SOURCE_DIR}/ALBUS_ionosphere/C++/mim/test/PIMrunner
    ${CMAKE_CURRENT_SOURCE_DIR}/ALBUS_ionosphere/FORTRAN/SOFA/sofa
    ${CMAKE_CURRENT_SOURCE_DIR}/ALBUS_ionosphere/FORTRAN/IRI
    ${CMAKE_CURRENT_SOURCE_DIR}/ALBUS_ionosphere/FORTRAN/PIM/PIM_1.7/pim/source/vlb4
)

# 4. Link directories for .so or .a libraries
link_directories(${ALBUS_PATH}/lib)

# 5. Find LAPACKE (OpenBLAS on macOS via MacPorts)
find_library(LAPACKE_LIB NAMES lapacke openblas 
    PATHS /opt/homebrew/opt/openblas/lib REQUIRED)
message(STATUS "LAPACKE_LIB=${LAPACKE_LIB}")

# 6. Define preprocessor macros for version info
add_definitions(-DMAJOR_VERSION=${MAJOR_VERSION} -DMINOR_VERSION=${MINOR_VERSION})

# 7. Add ALBUS_ionosphere subdirectory
add_subdirectory(ALBUS_ionosphere)

# Get the correct Python site-packages path
execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_paths()['platlib'])"
  OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Get platform-correct extension suffix
execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c "from importlib.machinery import EXTENSION_SUFFIXES as s; print(s[0])"
  OUTPUT_VARIABLE PYTHON_EXTENSION_SUFFIX
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

# 8. Create the Python extension module
add_library(AlbusIonosphere MODULE AlbusIonosphere.cxx)

set_target_properties(AlbusIonosphere PROPERTIES
  PREFIX ""
  SUFFIX "${PYTHON_EXTENSION_SUFFIX}"
  INSTALL_RPATH "$ORIGIN"
  BUILD_WITH_INSTALL_RPATH TRUE
)

# Get NumPy include for target specifically
execute_process(
    COMMAND "${Python3_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
    OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

target_include_directories(AlbusIonosphere
    PRIVATE
        ${NUMPY_INCLUDE_DIR}
)

# 9. Link the required external libraries
target_link_libraries(AlbusIonosphere
    PRIVATE
    mim
    jmavex
    iri
    pim
    sofa
    vexplus
    vex
    fl
    gfortran
    m
    ${LAPACKE_LIB}
    ${Python3_LIBRARIES}
)

install(TARGETS AlbusIonosphere
        LIBRARY DESTINATION ${PYTHON_SITE_PACKAGES}
        PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE
                    GROUP_READ GROUP_EXECUTE
                    WORLD_READ WORLD_EXECUTE
)