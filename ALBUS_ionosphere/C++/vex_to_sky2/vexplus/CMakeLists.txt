cmake_minimum_required(VERSION 3.10)
project(vexplus CXX)

#----------------------------------------------------------------------------
# Configuration variables
#----------------------------------------------------------------------------
# Define an INSTALLDIR variable (by default, use CMAKE_INSTALL_PREFIX)
if(NOT DEFINED INSTALLDIR)
  set(INSTALLDIR ${CMAKE_INSTALL_PREFIX} CACHE PATH "Installation directory")
endif()


#----------------------------------------------------------------------------
# Include directories
#----------------------------------------------------------------------------
# These mimic the Makefile’s -I options.
# Adjust the paths as needed.
include_directories(
  ../vex2005
)

#----------------------------------------------------------------------------
# Source and header files
#----------------------------------------------------------------------------
set(SRCS
  vexplus.cxx
)

set(HEADERS
  vexplus.h
)

#----------------------------------------------------------------------------
# Library Targets
#----------------------------------------------------------------------------
# Create a shared library target that will produce libvexplus.so with versioning.
add_library(vexplus SHARED ${SRCS})
set_target_properties(vexplus PROPERTIES
  OUTPUT_NAME "vexplus"
  VERSION "${VER_MAJOR}.${VER_MINOR}.${VER_SUBSUB}"
  SOVERSION "${VER_MAJOR}"
)



target_link_libraries(vexplus PRIVATE vex)

set_target_properties(vexplus PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH TRUE
)
#----------------------------------------------------------------------------
# Installation rules
#----------------------------------------------------------------------------
# Install the shared library and header file(s) to the specified directories.

execute_process(
  COMMAND ${Python3_EXECUTABLE} -c "import site; print(site.getsitepackages()[0])"
  OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

install(TARGETS vexplus
        LIBRARY DESTINATION ${PYTHON_SITE_PACKAGES}
)

