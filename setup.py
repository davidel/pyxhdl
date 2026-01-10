#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(name='pyxhdl',
      version='0.2',
      description='Python HDL',
      author='Davide Libenzi',
      packages=find_packages(),
      package_data={
          'pyxhdl': ['hdl_libs/**', ],
      },
      install_requires=[
          'numpy',
          'py_misc_utils @ git+https://github.com/davidel/py_misc_utils@main',
      ],
      )
