from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='pywebapp',
      version=version,
      description="Support library for Python Web Applications",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='wsgi web',
      author='Ian Bicking',
      author_email='ianb@colorstudy.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "pyyaml",
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
