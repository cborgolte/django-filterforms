#!/usr/bin/env python

from distutils.core import setup

setup(
    name='django-filterforms',
    version='0.1',
    description='Use a Django Form for filtering querysets.',
    long_description='Use a Django Form for filtering querysets.',
    author='Christoph Borgolte',
    author_email='christoph.borgolte@gmail.com',
    url='',
    download_url='',
    classifiers=['Development Status :: 4 - Beta',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'Operating System :: OS Independent',
                 'Topic :: Software Development'
    ],
    packages=['filter_forms',],
)
