#!/usr/bin/python3

from setuptools import setup

setup(
    name='MagicMirror',
    version='0.1',
    packages=['magic_mirror'],
    entry_points={'console_scripts': [
        'magic-mirror = magic_mirror.server:main']},
    install_requires=[
        'Flask',
        'requests'],
    package_data={
        'magic_mirror': [
            'templates/*.html',
            'static/d3.v3.min.js']
        }
    )
