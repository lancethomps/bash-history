#!/usr/bin/env python
# pylint: disable=C0103
import codecs
import re
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
  user_options = [('pytest-args=', 'a', "Arguments to pass into py.test")]

  def initialize_options(self):
    TestCommand.initialize_options(self)
    try:
      from multiprocessing import cpu_count

      self.pytest_args = ['-n', str(cpu_count()), '--boxed']
    except (ImportError, NotImplementedError):
      self.pytest_args = ['-n', '1', '--boxed']

  def finalize_options(self):
    TestCommand.finalize_options(self)
    self.test_args = []
    self.test_suite = True

  def run_tests(self):
    import pytest

    errno = pytest.main(self.pytest_args)
    sys.exit(errno)


requirements = codecs.open('./requirements.txt').read().splitlines()
long_description = codecs.open('./README.md').read()
version = codecs.open('./VERSION').read().strip()


def include_script_file(bin_file: Path) -> bool:
  if not bin_file.is_file():
    return False

  if bin_file.name.startswith("_"):
    return False

  with open(bin_file.as_posix(), 'r') as rf:
    line = rf.readline()
    if not line.strip().endswith("usr/bin/env python"):
      return False

    line = rf.readline()
    if re.fullmatch(r"^# *skip *= *true", line.strip()):
      return False

  return True


bin_dir = Path("./bin")
script_files = sorted([bin_file.relative_to(bin_dir.parent).as_posix() for bin_file in bin_dir.glob("*") if include_script_file(bin_file)])
if script_files:
  print("scripts config no longer used, fix these script files to use console_scripts: %s" % script_files)
  exit(1)

test_requirements = [
  'pytest-cov',
  'pytest-mock',
  'pytest-xdist',
  'pytest',
]

setup(
  name='bashhistory',
  version=version,
  description='Common Python helper functions',
  long_description=long_description,
  long_description_content_type='text/markdown',
  url='https://github.com/lancethomps/bashhistory',
  project_urls={
    'Bug Reports': 'https://github.com/lancethomps/bashhistory/issues',
    'Source': 'https://github.com/lancethomps/bashhistory',
  },
  author='Lance Thompson',
  license='MIT',
  keywords=[
    'bash',
    'history',
    'shell',
    'utils',
  ],
  python_requires='>=3.6',
  packages=['bashhistory', 'bashhistorytests'],
  install_requires=requirements,
  extras_require={'pcre': ['python-pcre']},
  classifiers=[
    'Intended Audience :: Developers',
    'Environment :: Console',
    'Topic :: System :: Logging',
    'Topic :: System :: Shells',
    'Topic :: Utilities',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3 :: Only'
  ],
  cmdclass={
    'test': PyTest,
  },
  tests_require=test_requirements,
  entry_points={
    "console_scripts": [
      "hist = bashhistory.cli:hist",
      "hist_db_create = bashhistory.cli:hist_db_create",
      "hist_db_insert = bashhistory.cli:hist_db_insert",
      "hist_grep = bashhistory.cli:hist_grep",
      "hist_grep_copy = bashhistory.cli:hist_grep_copy",
      "hist_grep_exec = bashhistory.cli:hist_grep_exec",
    ]
  },
)
