from setuptools import setup, find_packages
import os

version = '0.0.dev0'

setup(name='fuselage',
      version=version,
      url="http://yaybu.com/",
      description="Server deployment and configuration management in Python",
      long_description = open("README.rst").read() + "\n" + \
                         open("CHANGES").read(),
      author="Isotoma Limited",
      author_email="support@isotoma.com",
      license="Apache Software License",
      classifiers = [
          "Intended Audience :: System Administrators",
          "Operating System :: POSIX",
          "License :: OSI Approved :: Apache Software License",
      ],
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'six',
      ],
      extras_require = {
          'test': ['unittest2', 'mock', 'fakechroot'],
          },
      entry_points = """
      [console_scripts]
      fuselage = fuselage.main:main
      """
      )
