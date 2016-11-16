#!/usr/bin/env python3
from setuptools import setup
from delugetools import __version__

setup(name='delugetools',
      version=__version__,
      description='toolkit for managing multiple deluge clients',
      url='http://gitlab.xmopx.net/dave/python-delugetools',
      author='dpedu',
      author_email='dave@davepedu.com',
      packages=['delugetools'],
      install_requires=['bencodepy==0.9.5', 'deluge-client'],
      entry_points={'console_scripts': [
          'deluge-cull = delugetools.cull:main',
          'deluge-add = delugetools.add:main']},
      zip_safe=False)

