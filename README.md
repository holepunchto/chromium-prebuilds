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
ln -s src/buildtools buildtools
```

## Patching

The build definitions rely on a few patches that must be manually applied after each `gclient sync`. The patches can be applied using `git`:

```sh
git apply --directory src src/prebuilds/patches/*.patch
```

Make sure to revert the patches before doing another `gclient sync` as it requires a clean working tree:

```sh
git apply --reverse --directory src src/prebuilds/patches/*.patch
```

## Cross compiling

The Chromium build system supports cross compiling for variants of the same host platform, such as making both ARM and Intel Darwin builds on an ARM Darwin system. For some platforms, additional packages might be needed as documented in the following.

### Linux

- `ia32` and `arm` on `x64` host
  - Packages: `gcc-multilib`

## License

Apache-2.0
