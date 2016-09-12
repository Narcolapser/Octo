#!/usr/bin/env python

from distutils.core import setup

CLASSIFIERS = [
	'Intended Audience :: Developers',
	'License :: OSI Approved :: Apache Software License',
]
long_desc = 'coming soon.' 


setup(name='Octo',
	version='0.2',
	description='uPortal Log reader',
	long_description=long_desc,
	author='Toben Archer',
	author_email='sandslash+Octo@gmail.com',
	maintainer='Toben Archer',
	maintainer_email='sandslash+Octo@gmail.com',
	url='https://github.com/Narcolapser/Octo',
	packages=[''],
	install_requires=['paramiko'],
	license='Apache 2.0',
	classifiers=CLASSIFIERS
)
