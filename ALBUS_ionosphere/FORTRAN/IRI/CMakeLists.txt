cmake_minimum_required(VERSION 3.10)
project(JMA_IRI LANGUAGES C CXX Fortran)

set(CMAKE_Fortran_FLAGS "-O2")
set(CMAKE_C_FLAGS "-O2")
set(CMAKE_CXX_FLAGS "-O2")

set(HEADERS
    jma_irisub_c.h
)

set(SRCS
    cira.f
    igrf.f
    iridreg.f
    irifun.f
   
)

set(OBJS
    cira.f
    igrf.f
    iridreg.f
    irifun.f
)

set(NOBJS
    irisub.f
    iritec.f
    jma_irisub.F
    jma_irisub_c.c
)

set(NEOBJS
    irisubne.f
    iritecne.f
)
add_compile_options(--std=legacy)

add_executable(iritestne iritestne.f ${OBJS} ${NEOBJS})
target_link_libraries(iritestne ${LIBRARIES})

# Build shared library

add_library(iri SHARED ${OBJS} ${NOBJS})
set_target_properties(iri PROPERTIES VERSION ${VER_MAJOR}.${VER_MINOR}.${VER_SUBSUB})

# make_ap executable

add_executable(make_ap make_ap.cxx)
target_link_libraries(make_ap ${LIBRARIES})

set_target_properties(iri PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH TRUE
)

execute_process(
  COMMAND ${Python3_EXECUTABLE} -c "import site; print(site.getsitepackages()[0])"
  OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

install(TARGETS iri
        LIBRARY DESTINATION ${PYTHON_SITE_PACKAGES}
)





