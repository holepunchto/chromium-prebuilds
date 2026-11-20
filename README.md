# chromium-prebuilds

Build definitions for making prebuilds of Chromium modules.

## Setup

Like Chromium itself, this repository is not intended for checkout using `git clone`. Instead, start by installing [`depot_tools`](https://commondatastorage.googleapis.com/chrome-infra-docs/flat/depot_tools/docs/html/depot_tools_tutorial.html#_setting_up) which is a toolset used for fetching and managing the Chromium source repositories. Next, create a new directory that will contain the Chromium sources and change into it:

```sh
mkdir chromium && cd chromium
```

Then, create a `.gclient` configuration file that will fetch this repository and its dependencies:

```sh
gclient config --name src/prebuilds [--cache-dir <path>] --unmanaged git@github.com:holepunchto/chromium-prebuilds.git
```

The `--cache-dir` argument, if provided, should point to a path, such as `~/.git_cache/`, that will be used for caching all cloned git repositories. When finished, fetch the repository and its dependencies:

```sh
gclient sync
```

This will take a while depending on the speed of your connection. When completed, create a link to the fetched build tools to mark the root of the build tree:

```sh
# POSIX
ln -s src/buildtools buildtools
```

```pwsh
# Windows
mklink /j buildtools src\buildtools
```

## Patching

The build definitions rely on a few patches that must be manually applied after each `gclient sync`. The patches are separated by submodule and can be applied using `git`:

```sh
git apply --directory src[/<submodule>] src/prebuilds/patches[/<submodule>]/*.patch
```

Make sure to revert the patches before doing another `gclient sync` as it requires a clean working tree:

```sh
git apply --reverse --directory src[/<submodule>] src/prebuilds/patches[/<submodule>]/*.patch
```

## Building

To build the various Chromium modules, start by changing into the `src/` directory:

```sh
cd src
```

Next, generate a build system using `gn` by importing the definition for your desired module, target, and mode, replacing `<target>` with one of the supported targets as defined by [`target/`](target/) and `<module>` with `v8`. The definition also holds any overrides that the target needs. iOS targets only support release builds.

> [!NOTE]
>
> To build with a sanitizer, additionally import one of the definitions in [`sanitizer/`](sanitizer/). An instrumented prebuild must only be linked into a program instrumented with the same sanitizers, or the two will disagree on the annotations they apply to shared libc++ containers. An uninstrumented prebuild disables the container annotations of libc++ in its `__config_site`, so that it can be linked into programs built with AddressSanitizer.

```sh
# POSIX
gn gen out/<target>/<module> --args="import(\"//prebuilds/<module>-<target>-<release|debug>.gni\")"
```

```pwsh
# Windows
gn gen out/<target>/<module> --args="import(\`"//prebuilds/<module>-<target>-<release|debug>.gni\`")"
```

> [!TIP]
>
> #### Examples
>
> To make a release build of V8 for Linux 64-bit ARM, do:
>
> ```sh
> gn gen out/linux-arm64/v8 --args="import(\"//prebuilds/v8-linux-arm64-release.gni\")"
> ```
>
> To make a release build of V8 for Windows 64-bit Intel, do:
>
> ```pwsh
> gn gen out/win32-x64/v8 --args="import(\`"//prebuilds/v8-win32-x64-release.gni\`")"
> ```
>
> To make a debug build of V8 for macOS 64-bit ARM instrumented with AddressSanitizer, do:
>
> ```sh
> gn gen out/darwin-arm64/v8-asan --args="import(\"//prebuilds/v8-darwin-arm64-debug.gni\") import(\"//prebuilds/sanitizer/address.gni\")"
> ```

Finally, run the build system for the `prebuilds` target:

```sh
ninja -C out/<target>/<module> prebuilds
```

The build writes a CMake package for each library to `out/<target>/<module>/package/`, each one an installable prefix of its own:

```
package/
  <module>/
    include/
    lib/lib<module>.a
    lib/cmake/<module>/
    share/licenses/<module>/
```

The licenses of the code in each library, including that of its third-party dependencies, are written to `share/licenses/`.

## Usage

The packages are found with `find_package(<module>)`. Point CMake at the `package/` directory of a build, or at the prefix the packages were installed to:

```sh
cmake -S . -B build -DCMAKE_PREFIX_PATH=<path>/out/<target>/<module>/package
```

Packages take the version of Chromium and only accept that exact version, or no version at all, as code compiled against the headers of one prebuild only works with the libraries of that same prebuild.

### `cmake-gn`

To use a GN build that isn't installed, such as one of your own with different arguments, find the packages with [`cmake-gn`](https://github.com/holepunchto/cmake-gn) instead. It reads the build from the GN root and output directory given by `GN_DIR` and `GN_OUT_DIR`, where the latter may be relative to the former:

```sh
cmake -S . -B build -DGN_DIR=<path>/src -DGN_OUT_DIR=out/<target>/<module>
```

```cmake
find_package(cmake-gn REQUIRED PATHS node_modules/cmake-gn)

add_gn_package(c++ INSTALL)
add_gn_package(v8 INSTALL)

target_link_libraries(<target> PRIVATE v8::static)
```

`add_gn_package()` finds the package that the build wrote to `package/<name>`, so build the `prebuilds` target before configuring. With `INSTALL`, the package is also installed with your project, which a package exported by your project needs to find its dependencies. Install `c++` along with `v8`, as the latter depends on the former.

### libc++

```cmake
find_package(c++ <version> REQUIRED)

target_link_libraries(<target> PRIVATE c++::static)
```

`c++::static` links the libc++ library, and `c++::headers` provides only the headers. Both replace the C++ standard library of the platform for the C++ code that links them. On Windows, they select the static runtime with `/MT`, or `/MTd` in debug builds. Elsewhere, they pass `-nostdinc++` and `-nostdlib++`. C code is unaffected, so a C program can link a static library that uses libc++ without any C++ settings of its own.

libc++ is built with its unstable ABI, which places it in the `std::__Cr` namespace. Its symbols therefore don't clash with those of another C++ standard library in the same program, but its types can't be passed to code compiled against another one. Compile all C++ code that shares standard library types with V8 against `c++::headers`.

The configuration of libc++, such as its hardening mode and its AddressSanitizer annotations, is written to the `__config_site` header of the package. The compiler runtime isn't included, so link the one of your toolchain, such as that of `llvm-runtime`.

### V8

```cmake
find_package(v8 <version> REQUIRED)

target_link_libraries(<target> PRIVATE v8::static)
```

`v8::static` links the V8 library along with the system libraries it needs, and `v8::headers` provides only the headers. Finding `v8` also finds the `c++` package next to it, and linking `v8::static` also links `c++::static`.

The configuration of V8 that its headers depend on is written to the `v8-gn.h` header of the package, which the headers read as `v8::headers` defines `V8_GN_HEADER`. V8 is built without RTTI, so `v8::headers` also compiles C++ without it.

V8 is built with pointer compression on all 64-bit targets and with the DrumBrake WebAssembly interpreter on all targets except Android, where DrumBrake is unavailable. DrumBrake allows WebAssembly to run with `--jitless`, which is required on iOS.

> [!IMPORTANT]
>
> Pointer compression and the caged heap of the C++ garbage collector each reserve a large, process-wide region of virtual memory when V8 is initialized. On iOS, these reservations exceed the default address space limit of apps, causing a `Failed to reserve virtual memory for process-wide V8 pointer compression cage` fatal error on devices. Apps that link the iOS prebuilds must therefore be signed with the [`com.apple.developer.kernel.extended-virtual-addressing`](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.kernel.extended-virtual-addressing) entitlement:
>
> ```xml
> <key>com.apple.developer.kernel.extended-virtual-addressing</key>
> <true/>
> ```

## License

Apache-2.0
