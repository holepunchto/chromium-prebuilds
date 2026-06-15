gclient_gn_args_from = "src"

vars = {
  "chromium_version": "148.0.7778.265",
  "chromium_git": "https://chromium.googlesource.com",
}

deps = {
  "src": {
    "url": Var("chromium_git") + "/chromium/src.git@" + Var("chromium_version"),
  },
}

recursedeps = [
  "src",
]
