# C++ CMake builds

- In C++, `cmake -S . -B build` configures and `cmake --build build` compiles portably.
- In C++, `cmake_minimum_required(VERSION 3.20)` plus `project(app)` opens every CMakeLists.
- In C++, `add_executable(app main.cpp)` declares binaries from source lists.
- In C++, `target_compile_features(app PRIVATE cxx_std_20)` pins language standards per target.
- In C++, `target_include_directories` with PUBLIC/PRIVATE scopes header visibility correctly.
- In C++, `target_link_libraries` connects targets; prefer targets over raw flags.
- In C++, `find_package(fmt)` locates installed libraries for linking.
- In C++, out-of-source `build/` directories keep trees clean and deletable.
- In C++, `CMAKE_BUILD_TYPE=Release` enables optimization; default lacks it on single-config generators.
- In C++, `ctest --test-dir build` runs registered tests after building.
