cmake_minimum_required(VERSION 3.22)

project(fastops LANGUAGES CXX)

find_package(Eigen3 3.4 REQUIRED NO_MODULE)

add_library(fastops SHARED
    cpp/src/fastops.cpp
)

target_include_directories(fastops
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/cpp/include
)

target_link_libraries(fastops PRIVATE Eigen::Eigen)

target_compile_features(fastops PRIVATE cxx_std_17)

target_compile_definitions(fastops
    PRIVATE
        FASTOPS_API_VERSION=1
        FASTOPS_ENABLE_DIAGNOSTICS=1
)

target_compile_options(fastops
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -Werror
)

set_target_properties(fastops PROPERTIES
    OUTPUT_NAME "fastops"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)
