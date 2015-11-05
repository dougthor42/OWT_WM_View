# -*- coding: utf-8 -*-
"""
Created on Tue May 12 12:58:55 2015

@author: dthor
"""
### #------------------------------------------------------------------------
### Imports
### #------------------------------------------------------------------------
# Standard Library
from setuptools import setup, find_packages
import logging

# Third Party

# Package / Application
from owt_wm_view import (__version__,
                         __project_url__,
                         __project_name__,
                         )

# turn off logging if we're going to build a distribution
logging.disable(logging.CRITICAL)

setup(
    name=__project_name__,
    version=__version__,
    description="OWT Wafer Map Viewer",
    packages=find_packages(),
    author="Douglas Thor",
    url=__project_url__,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications",
        "Environment :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities",
        ],
    requires=["wxPython",
              "keyring",
              "docopt",
              "BeautifulSoup4",
              ],
)