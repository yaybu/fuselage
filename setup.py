import os

from setuptools import find_packages, setup

version = '1.0.0'

setup(
    name='fuselage',
    version=version,
    url="http://yaybu.com/",
    description="Server deployment and configuration management in Python",
    long_description = open("README.rst").read(),
    author="Isotoma Limited",
    author_email="support@isotoma.com",
    license="Apache Software License",
    classifiers = [
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: CPython",
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
