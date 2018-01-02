#!/usr/bin/env python3

"""
Copyright 2017 Dean Hall.  See LICENSE for details.

This is a tool to generate a mac_identity.py file.
An asymmetric cryptographic keypair is generated
such that the SHA512(SHA512(pub_key)) starts with 0xFC
"""

import hashlib, random


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

def _gen_specific_keypair(firstbyte):
    """Generate keypairs and forget them
    until we make one with a specific first byte.
    """
    done = False
    while not done:
        prv_key, pub_key = gen_keypair()
        h = hashlib.sha512()
        h.update(pub_key)
        h.update(h.digest())
        done = h.hexdigest().startswith(firstbyte)
    return (prv_key, pub_key)


if __name__ == "__main__":
    _, pub_key = gen_device_keypair()
    print("pub_key:", pub_key)
