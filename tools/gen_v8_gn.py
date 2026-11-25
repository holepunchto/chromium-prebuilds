#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def parse_args():
  parser = argparse.ArgumentParser(
      description='Generate v8-gn.h for a build that passes the definitions '
      'of V8 on the command line instead.')
  parser.add_argument('--script', required=True)
  parser.add_argument('--output', required=True)
  parser.add_argument('--source-root', required=True)
  parser.add_argument('--build-dir', required=True)
  parser.add_argument('--depfile', required=True)

  return parser.parse_args()


def find_gn(source_root):
  exe = 'gn.exe' if sys.platform == 'win32' else 'gn'
  platform = {'darwin': 'mac', 'win32': 'win'}.get(sys.platform, 'linux64')
  path = os.path.join(source_root, 'buildtools', platform, exe)

  if os.path.isfile(path):
    return path

  return shutil.which(exe)


# V8 only defines the action that writes v8-gn.h when the header is enabled, so
# describe it in a separate output directory with the header enabled. Querying
# the active output directory would also race with the actions of the build.
def gen_v8_gn_args(source_root, build_dir):
  gn = find_gn(source_root)

  if not gn:
    raise RuntimeError('gn not found in buildtools or on PATH')

  with tempfile.TemporaryDirectory(dir=os.path.dirname(build_dir)) as tmp_dir:
    shutil.copyfile(
        os.path.join(build_dir, 'args.gn'), os.path.join(tmp_dir, 'args.gn'))

    with open(os.path.join(tmp_dir, 'args.gn'), 'a') as f:
      f.write('\nv8_generate_external_defines_header = true\n')

    open(os.path.join(tmp_dir, 'build.ninja'), 'w').close()

    output = subprocess.check_output(
        [
            gn, 'desc', '-q', '--root=' + source_root, tmp_dir,
            '//v8:gen_v8_gn', 'args', '--format=json'
        ],
        cwd=source_root,
        text=True)

  return next(iter(json.loads(output).values()))['args']


def main():
  args = parse_args()

  source_root = os.path.abspath(args.source_root)
  build_dir = os.path.abspath(args.build_dir)
  output = os.path.abspath(args.output)

  script_args = gen_v8_gn_args(source_root, build_dir)
  index = script_args.index('-o')
  script_args = script_args[:index] + script_args[index + 2:]

  os.makedirs(os.path.dirname(output), exist_ok=True)

  subprocess.check_call([sys.executable, args.script, '-o', output] +
                        script_args)

  # The script leaves an unchanged header untouched, which would otherwise
  # leave it older than the inputs of the action and rerun it on every build.
  os.utime(output)

  # The definitions change with the files that the build files are generated
  # from, which GN doesn't allow an action to list as inputs.
  with open(os.path.join(build_dir, 'build.ninja.d')) as f:
    dependencies = f.read().split(':', 1)[1]

  with open(args.depfile, 'w') as f:
    f.write('%s:%s' % (args.output, dependencies))


if __name__ == '__main__':
  sys.exit(main())
