#!/usr/bin/env python
#
# Copyright 2010 The Closure Linter Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup.py file for jscodestyle."""


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Unit Tests require mock on Python 2
TESTS_REQUIRE = []
try:
    # pylint: disable=unused-import
    import unittest.mock
except ImportError:
    TESTS_REQUIRE.append('mock')


setup(
    name='jscodestyle',
    version='2.3.19',
    description='JSCodeStyle',
    license='Apache',
    author='The JSCodeStyle Authors',
    author_email='theology@gmail.com',
    url='https://github.com/zeth/jscodestyle',
    install_requires=['python-gflags'],
    tests_require=TESTS_REQUIRE,
    package_dir={'jscodestyle': 'jscodestyle'},
    packages=['jscodestyle', 'jscodestyle.common'],
    test_suite="tests",
    entry_points={
        'console_scripts': [
            'jscodestyle = jscodestyle.gjslint:main',
            'gjslint = jscodestyle.gjslint:main',
            'fixjsstyle = jscodestyle.fixjsstyle:main'
        ]
    }
)
