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

The `--cache-dir` argument, if provided, should point to a path, such as `~/.git_cache`, that will be used for caching all cloned git repositories. When finished, fetch the repository and its dependencies:

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

```sh
# POSIX
gn gen out/<target>/<module> --args="import(\"//prebuilds/<module>.gni\") import(\"//prebuilds/mode/<release|debug>.gni\") import(\"//prebuilds/target/<target>.gni\")"
```

```pwsh
# Windows
gn gen out/<target>/<module> --args="import(\`"//prebuilds/<module>.gni\`") import(\`"//prebuilds/mode/<release|debug>.gni\`") import(\`"//prebuilds/target/<target>.gni\`")"
```

```sh
ninja -C out/<target>/<module> prebuilds
```

## License

Apache-2.0
