#!/usr/bin/env python3

from distutils.core import setup

setup(name="HeyMac",
      version="0.1.0",
      description="Data Link Layer (2) protocol for low-power, lossy wireless data transfer",
      author="Dean Hall",
      author_email="dwhall256@gmail.com",
      url="https://github.com/dwhall/HeyMac",
      packages=['HeyMac',],
      requires=[
            "farc",
            "dpkt",
            "pyserial",
            "RPi",
            ],
     )
