#!/usr/bin/env python
from distutils.core import setup

setup(name='MiGBox',
      version='0.01',
      description='MiGBox',
      author='Benjamin Ertl',
      author_email='',
      url='https://github.com/bertl4398/MiGBox',
      package_dir={'MiGBox': ''},
      packages=['MiGBox.core','MiGBox.cli','MiGBox.gui'],
     )
