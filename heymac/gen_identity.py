#!/usr/bin/env python3

"""
Copyright 2017 Dean Hall.  See LICENSE for details.

This is a tool to generate a HeyMac identity configuration file.
An asymmetric cryptographic keypair is generated
such that the SHA512(SHA512(pub_key)) starts with 0xFC or 0xFD
"""

import hashlib
import json
import os.path
import random

import utl


def gen_keypair():
    """Generates 256 bit keypair
    """
    # TODO: run system() to call real crypto tool to generate a key pair
    prv_key = bytes(bytearray(32))
    pub_key = random.getrandbits(256).to_bytes(32, 'big')
    return (prv_key, pub_key)


def gen_personal_keypair():
    return _gen_specific_keypair("fc")

def gen_device_keypair():
    return _gen_specific_keypair("fd")

def _gen_specific_keypair(prefix):
    """Generates keypairs and forgets them
    until one is made with a specific prefix (nibble, byte or bytes).
    """
    done = False
    while not done:
        prv_key, pub_key = gen_keypair()
        h = hashlib.sha512()
        h.update(pub_key)
        h.update(h.digest())
        done = h.hexdigest().startswith(prefix)
    return (prv_key, pub_key)


if __name__ == "__main__":
    name = input("Full name: ")
    callsign = input("Callsign: ")
    _, pub_key = gen_device_keypair()

    fn = os.path.join(utl.get_app_data_path("HeyMac"), "mac_identity.json")
    with open(fn, 'w') as f:
        json_str = json.dumps({
            "name": name,
            "callsign": callsign,
            "pub_key": pub_key.hex()})
        f.write(json_str)
    print("Wrote: %s" % fn)
