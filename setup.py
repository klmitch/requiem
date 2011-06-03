#!/usr/bin/python

from distutils.core import setup

setup(
    name='Rest',
    version='0.1',
    description="REST Client Constructor",
    author="Kevin L. Mitchell",
    author_email="kevin.mitchell@rackspace.com",
    url="http://github.com/klmitch/rest",
    packages=['rest'],
    license="LICENSE.txt",
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: Other/Proprietary License',  # temporary, until we decide
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    )
