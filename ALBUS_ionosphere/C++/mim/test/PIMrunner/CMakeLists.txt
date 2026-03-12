cmake_minimum_required(VERSION 3.10)
project(JMA_Code C CXX)



find_library(LAPACKE_LIB NAMES lapacke PATHS /opt/local/lib REQUIRED)
message(STATUS "LAPACKE_LIB=${LAPACKE_LIB}")



#----------------------------------------------------------------------------
# Include directories (similar to -I options in the Makefile)
#----------------------------------------------------------------------------
include_directories(${PYTHONINCLUDEDIR})

include_directories(${CMAKE_SOURCE_DIR}/ALBUS_ionosphere/C++/vex_to_sky2)
include_directories(${CMAKE_SOURCE_DIR}/ALBUS_ionosphere/include)
#include_directories(../../../../FORTRAN/IRI)
#include_directories(../../../../FORTRAN/PIM/PIM_1.7/pim/source/vlb4)





#----------------------------------------------------------------------------
# Add compile options if desired (e.g. adding -I${PYTHONINCLUDEDIR} to CFLAGS)
#----------------------------------------------------------------------------
add_compile_options(-I${PYTHONINCLUDEDIR})

#----------------------------------------------------------------------------
# Specify source and header files
#----------------------------------------------------------------------------
set(SRCS
    3C.cxx
    GPS.cxx
    GPS_collection.cxx
    GPS_receiver_obs.cxx
    GPS_satellites.cxx
    GPS_times.cxx
    MC_direction.cxx
    MT_random.cxx
    VTEC.cxx
    atmosphere_point.cxx
    cal_source.cxx
    data_calibrator.cxx
    filter.cxx
    iono_runner.cxx
    ionosphere.cxx
    ionosphere_fake.cxx
    ionosphere_gen.cxx
    ionosphere_gps.cxx
    ionosphere_iri.cxx
    ionosphere_iriplus.cxx
    ionosphere_pim.cxx
    jma_igrf13.c
    latlon_cart.cxx
    linfit.cxx
    linfit_grad.cxx
    physical_constants.cxx
    pim_runner.cxx
    random_source.cxx
    sofa_helpers.cxx
    space_rotation_matrix.cxx
    space_unit_vector.cxx
    space_vector.cxx
    station_latlon.cxx
    station_maker.cxx
    station_reference.cxx
    ${CMAKE_SOURCE_DIR}/ALBUS_ionosphere/C++/vex_to_sky2/vex_iono_processor.cxx
)

# List header files (for IDE integration; not strictly required for compilation)
set(HEADERS
    3C.h
    GPS.h
    GPS_collection.h
    GPS_criteria.h
    GPS_receiver.h
    GPS_receiver_obs.h
    GPS_satellites.h
    GPS_times.h
    MC_direction.h
    MC_random.h
    MT_random.h
    VTEC.h
    atmosphere_point.h
    cal_source.h
    data_calibrator.h
    filter.h
    iono_runner.h
    ionosphere.h
    ionosphere_fake.h
    ionosphere_gen.h
    ionosphere_gps.h
    ionosphere_iri.h
    ionosphere_iriplus.h
    ionosphere_pim.h
    latlon_cart.h
    linfit.h
    linfit_grad.h
    location.h
    observation.h
    observation_3D.h
    physical_constants.h
    pim_runner.h
    random_source.h
    sofa_helpers.h
    space_rotation_matrix.h
    space_unit_vector.h
    space_vector.h
    station_latlon.h
    station_maker.h
    station_reference.h
)

#----------------------------------------------------------------------------
# Create the library target (shared or static based on BUILD_SHARED_LIBS)
#----------------------------------------------------------------------------
add_library(mim SHARED ${SRCS})


# Set version information for the shared library (if BUILD_SHARED_LIBS is ON)
set_target_properties(mim 
   PROPERTIES OUTPUT_NAME "mim"
 VERSION "${VER_MAJOR}.${VER_MINOR}.${VER_SUBSUB}"
  SOVERSION "${VER_MAJOR}"

)

#----------------------------------------------------------------------------
# Specify additional include directories for the library target
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
# Specify additional link directories (analogous to -L options)
#----------------------------------------------------------------------------



#----------------------------------------------------------------------------
# Link external libraries (analogous to the LIBRARIES variable in the Makefile)
#
# The original Makefile used:
#   -L$(INSTALLDIR)/lib -L/usr/lib -lpim -liri -ljmavex -lvexplus -lvex -lsofa -lfl -lm
#
# Here we assume that libraries named pim, iri, jmavex, vexplus, vex, sofa, fl and m
# are available. You might need to adjust these or use find_library() if necessary.
#----------------------------------------------------------------------------
#target_link_libraries(mim PRIVATE
#    jmavex
#    pim
#    iri
#    vexplus
#    vex
#    sofa
#    fl
#    m
#    lapacke
#    
#)
target_link_libraries(mim PUBLIC
    jmavex
    pim
    iri
    vexplus
    vex
    sofa
    fl
    m
    ${LAPACKE_LIB}
)

set(EXECUTABLES
    lofar
    lofar2
    lofar3
    lofar4
    lofar5
    lofar6
    lofar7
    lofar8
    lofar9
    lofar10
    test_pim
    test2_pim
    vlba_obs
)
foreach(exec ${EXECUTABLES})
  # Assume the main file for each executable is named "<exec>.cxx"
  add_executable(${exec} ${exec}.cxx)
  target_link_libraries(${exec} PRIVATE mim
  #  pim
  #  iri
  #  jmavex
  #  vexplus
  #  vex
  #  sofa
  #  fl
  #  m
  #  lapacke
  )
  target_include_directories(${exec} PRIVATE
    ${PYTHONINCLUDEDIR}
    ${INSTALLDIR}/C++/vex_to_sky2
  )
endforeach()




set_target_properties(mim PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH TRUE
)


 execute_process(
  COMMAND ${Python3_EXECUTABLE} -c "import site; print(site.getsitepackages()[0])"
  OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

install(TARGETS mim
        LIBRARY DESTINATION ${PYTHON_SITE_PACKAGES}
)

install(TARGETS ${EXECUTABLES}
        RUNTIME DESTINATION ${PYTHON_SITE_PACKAGES}/bin)



