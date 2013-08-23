from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup


setup(
    name='awibmanager',
    version='0.1',
    author='Tom Elliott',
    author_email='tom.elliott@nyu.edu',
    packages=['awibmanager'],
    url='',
    license='See LICENSE.txt',
    description='Scripts for managing the Ancient World Image Bank (AWIB)',
    long_description=open('README.txt').read(),
    install_requires = ['flickrapi>=1.4.2'],
)
