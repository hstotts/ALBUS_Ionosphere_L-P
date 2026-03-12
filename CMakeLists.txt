cmake_minimum_required(VERSION 3.10)
project(AlbusIonosphere LANGUAGES CXX)

# 1. Get environment variables or fallback to defaults
set(ALBUS_PATH $ENV{ALBUS_PATH} CACHE PATH "Path to ALBUS install")
set(INSTALLDIR $ENV{ALBUS_PATH} CACHE PATH "Path to ALBUS install")
set(MAJOR_VERSION $ENV{MAJOR_VERSION} CACHE STRING "Major version")
set(MINOR_VERSION $ENV{MINOR_VERSION} CACHE STRING "Minor version")

# Get NumPy include path dynamically
execute_process(
  COMMAND ${Python3_EXECUTABLE} -c "import numpy; print(numpy.get_include())"
  OUTPUT_VARIABLE NumPy_INCLUDE_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

include_directories(${NumPy_INCLUDE_DIR})

# 2. Find Python and NumPy (REQUIRED for pybind11 / NumPy C API)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development NumPy)

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

# 5. Define preprocessor macros for version info
add_definitions(-DMAJOR_VERSION=${MAJOR_VERSION} -DMINOR_VERSION=${MINOR_VERSION})

# 6. Add ALBUSionosphere if it has sources or more targets
add_subdirectory(ALBUS_ionosphere)

# 7. Create the shared library module
#add_library(AlbusIonosphere SHARED AlbusIonosphere.cxx)


# Ensure correct file name for Python extension
#set_target_properties(AlbusIonosphere PROPERTIES
#  PREFIX ""  # No 'lib' prefix
#  SUFFIX ".cpython-310-x86_64-linux-gnu.so"  # Match your Python version/platform
#)

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

add_library(AlbusIonosphere MODULE AlbusIonosphere.cxx)

set_target_properties(AlbusIonosphere PROPERTIES
  PREFIX ""
  SUFFIX "${PYTHON_EXTENSION_SUFFIX}"
  INSTALL_RPATH "$ORIGIN"
  BUILD_WITH_INSTALL_RPATH TRUE
)



# 8. Link the required external libraries
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
    ${Python3_LIBRARIES}
)

# Get Python site-packages directory
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

execute_process(
    COMMAND "${Python3_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
    OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

target_include_directories(AlbusIonosphere
    PRIVATE
        ${NUMPY_INCLUDE_DIR}
)


install(TARGETS AlbusIonosphere
        LIBRARY DESTINATION ${PYTHON_SITE_PACKAGES}
        PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE
                    GROUP_READ GROUP_EXECUTE
                    WORLD_READ WORLD_EXECUTE
)

