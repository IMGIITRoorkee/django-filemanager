#!/usr/bin/env python
import os
import sys

from setuptools import find_packages, setup


def get_install_requires():
    """
    parse requirements.txt, ignore links, exclude comments
    """
    requirements = []
    for line in open('requirements.txt').readlines():
        # skip to next iteration if comment or empty line
        if line.startswith('#') or line == '' or line.startswith('http') or line.startswith('git'):
            continue
        # add line to requirements
        requirements.append(line)
    return requirements


setup(
    name="django-filemanager",
    version="0.0.1",
    author="Information Management Group",
    author_email="img.iitr.img@gmail.com",
    description="A file manager for Django",
    license="MIT",
    packages=find_packages(exclude=["tests", ]),
    install_requires=get_install_requires(),
    zip_safe=False,
    include_package_data=True,
    test_suite='tests.main',
)
