#!/usr/bin/env python
from setuptools import setup, find_packages
from pip.req import parse_requirements

# parse requirements
# reqs = parse_requirements("requirements/common.txt")

# setup the project
setup(
    name="django-filemanager",
    version="0.0.1",
    author="Information Management Group",
    author_email="img.iitr.img@gmail.com",
    description="A file manager for Django",
    license="IMG",
    packages=find_packages(exclude=["tests", ]),
    # install_requires=[str(x).split(' ')[0] for x in reqs],
    zip_safe=False,
    include_package_data=True,
    test_suite='tests.main',
)
