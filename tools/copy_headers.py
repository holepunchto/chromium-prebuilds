#!/usr/bin/env python3

import argparse
import os
import shlex
import shutil
import sys


def parse_args():
  parser = argparse.ArgumentParser(
      description='Copy headers into a directory, replacing its contents.')
  parser.add_argument('--output', required=True)
  parser.add_argument('--stamp', required=True)
  parser.add_argument('--depfile')
  parser.add_argument(
      '--tree',
      action='append',
      default=[],
      help='Copy every .h file in the directory and its subdirectories')
  parser.add_argument(
      '--file',
      action='append',
      default=[],
      nargs=2,
      metavar=('BASE', 'PATH'),
      help='Copy the file to its path relative to the base directory')

  argv = []

  for arg in sys.argv[1:]:
    if arg.startswith('@'):
      with open(arg[1:]) as f:
        argv += shlex.split(f.read())
    else:
      argv.append(arg)

  return parser.parse_args(argv)


def main():
  args = parse_args()

  copies = {}
  dependencies = []

  for tree in args.tree:
    for root, _, files in os.walk(tree):
      # Directories change when files are added or removed, which a list of
      # the copied files wouldn't notice.
      dependencies.append(root)

      for name in files:
        if name.endswith('.h'):
          path = os.path.join(root, name)
          copies[os.path.relpath(path, tree)] = path

  for base, path in args.file:
    copies[os.path.relpath(path, base)] = path

  shutil.rmtree(args.output, ignore_errors=True)

  for relative, path in sorted(copies.items()):
    destination = os.path.join(args.output, relative)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.copyfile(path, destination)
    dependencies.append(path)

  if args.depfile:
    with open(args.depfile, 'w') as f:
      escaped = [path.replace(' ', '\\ ') for path in dependencies]
      f.write('%s: %s\n' % (args.stamp, ' '.join(escaped)))

  with open(args.stamp, 'w'):
    pass


if __name__ == '__main__':
  sys.exit(main())
