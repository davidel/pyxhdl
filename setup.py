#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(name='pyxhdl',
      version='0.34',
      description='Use Python as HDL language, and generate equivalent SystemVerilog and VHDL code',
      author='Davide Libenzi',
      packages=find_packages(),
      package_data={
          'pyxhdl': ['hdl_libs/**', ],
      },
      python_requires='>=3.9',
      install_requires=[
          'numpy',
          'python_misc_utils',
      ],
      )
