cmake_minimum_required(VERSION 3.10)

install(
    DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/ALBUS_ionosphere/include/
    DESTINATION ${CMAKE_SOURCE_DIR}/albusionosphere/include
    FILES_MATCHING PATTERN "*.h"
)

