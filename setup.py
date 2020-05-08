#!/usr/bin/env python
# pylint: disable=C0103
import codecs
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
bin_dir = Path("./bin")
script_files = sorted([bin_file.relative_to(bin_dir.parent).as_posix() for bin_file in bin_dir.glob("*") if bin_file.is_file() and not bin_file.name.startswith("_")])

test_requirements = [
  'pytest-cov',
  'pytest-mock',
  'pytest-xdist',
  'pytest',
]

setup(
  name='bash-history',
  version=version,
  description='Common Python helper functions',
  long_description=long_description,
  long_description_content_type='text/markdown',
  url='https://github.com/lancethomps/bash-history',
  project_urls={
    'Bug Reports': 'https://github.com/lancethomps/bash-history/issues',
    'Source': 'https://github.com/lancethomps/bash-history',
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
  packages=['bash_history', 'bash_historytests'],
  install_requires=requirements,
  classifiers=[],
  cmdclass={
    'test': PyTest,
  },
  tests_require=test_requirements,
  scripts=script_files,
)
