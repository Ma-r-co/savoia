import sys
from setuptools import setup


if sys.version_info < (3, 7):
    print("Building SAMPLE_PROJECT requires at least Python 3.7 to run.")
    sys.exit(1)

setup()
