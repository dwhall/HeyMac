#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""


import logging
import socket
import sys

import farc

import app_chat_ahsm


def main():
    logging.basicConfig(
            #filename = __file__ + "." + socket.gethostname() + ".log",
            stream = sys.stdout,
            format = "%(asctime)s %(message)s",
            level = logging.INFO)

    # Instantiate state machines
    chatAhsm = app_chat_ahsm.ChatAhsm()

    # Start state machines (with priorities)
    chatAhsm.start(70)

    # Start state machines and event loop
    farc.run_forever()


if __name__ == "__main__":
    main()
