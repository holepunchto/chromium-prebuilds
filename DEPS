gclient_gn_args_from = "src"

vars = {
  "chromium_version": "126.0.6478.36",
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
