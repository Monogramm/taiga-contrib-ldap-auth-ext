#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

setup(
    name = 'taiga-contrib-ldap-auth-ext',
    version = ":versiontools:taiga_contrib_ldap_auth_ext:",
    description = "The (extended) Taiga plugin for ldap authentication",
    long_description = "",
    keywords = 'taiga, ldap, auth, plugin',
    author = 'madmath03',
    author_email = 'mb.mathieu.brunot@gmail.com',
    url = 'https://github.com/Monogramm/taiga-contrib-ldap-auth-ext',
    license = 'AGPL',
    include_package_data = True,
    packages = find_packages(),
    install_requires=[
        'django >= 1.7',
		'ldap3 >= 0.9.8.4'
    ],
    setup_requires = [
        'versiontools >= 1.8',
    ],
    classifiers = [
        "Programming Language :: Python",
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
