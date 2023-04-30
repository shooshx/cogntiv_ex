cmake_minimum_required(VERSION 3.0)
set(CMAKE_CXX_COMPILER gcc-11)

project(cogntiv_cpp)

add_executable(cpp_client cpp_client.cpp)

target_include_directories(cpp_client PRIVATE $ENV{BOOST_ROOT} 
                                              $ENV{FMT_ROOT}/include
                          )
						  
target_link_libraries(cpp_client PRIVATE pthread stdc++ m)						  
						  
# g++-11 cpp_client.cpp -I$BOOST_ROOT -I$FMT_ROOT/include -lpthread						  