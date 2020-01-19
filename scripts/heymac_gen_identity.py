#!/usr/bin/env python3

"""
Copyright 2017 Dean Hall.  See LICENSE for details.

This is a tool to generate a HeyMac identity configuration file.
An asymmetric cryptographic keypair is generated
such that the SHA512(SHA512(pub_key)) starts with 0xFC or 0xFD

Dependencies::

    pip install asn1
    pip install crytography

References:
    https://cryptography.io/en/latest/
    https://github.com/andrivet/python-asn1/blob/master/examples/dump.py
"""

import codecs
import hashlib
import json
import os.path
import random

import asn1 # pip install asn1
from cryptography.hazmat.backends import default_backend # pip install cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from heymac import utl


def gen_keypair():
    """Generates asymmetric keypair using elliptic curve SECP384R1
    """
    prv_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
    return (prv_key, prv_key.public_key())


def gen_personal_keypair():
    return _gen_specific_keypair("fc")

def gen_device_keypair():
    return _gen_specific_keypair("fd")

def gen_feb12b_keypair():
    """Generates a feb/12 keypair.
    Note that feb/12 is a subset of fe8/10
    the well-known link-local prefix.
    """
    return _gen_specific_keypair("feb")

def _gen_specific_keypair(prefix):
    """Generates keypairs and forgets them
    until one is made with a specific prefix (nibble, byte or bytes).
    """
    done = False
    while not done:
        prv_key, pub_key = gen_keypair()
        der_bytes = pub_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        pub_key_bytes = _get_key_from_asn1(der_bytes)
        h = hashlib.sha512()
        h.update(pub_key_bytes)
        h.update(h.digest())
        done = h.hexdigest().startswith(prefix)
    return (prv_key, pub_key)


def _get_key_from_asn1(der_bytes):
    """Returns the key bytes from a PublicKey instance
    whose DER encoding resembles:
    [U] SEQUENCE
        [U] SEQUENCE
            [U] OBJECT: 1.2.840.10045.2.1
            [U] OBJECT: 1.3.132.0.34
        [U] BIT STRING:<key bytes>
    """
    decoder = asn1.Decoder()
    decoder.start(der_bytes)
    def rdparse_asn1(decoder):
        retval = None
        while not decoder.eof():
            tag = decoder.peek()
            if tag.typ == asn1.Types.Primitive:
                tag, retval = decoder.read()
                if tag.cls == asn1.Numbers.BitString:
                    break
            elif tag.typ == asn1.Types.Constructed:
                decoder.enter()
                retval = rdparse_asn1(decoder)
                decoder.leave()
        return retval
    return rdparse_asn1(decoder)


if __name__ == "__main__":
    name = input("Full name: ")
    callsign = input("Callsign: ")
    passphrase = input("Private key encryption passphrase: ")  # sketchy
    passphrase = passphrase.encode()

    prv_key, pub_key = gen_personal_keypair()
    der_bytes = pub_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo)
    key_bytes = _get_key_from_asn1(der_bytes)

    # Save private key to a file
    heymac_path = utl.get_app_data_path("HeyMac")
    fn = os.path.join(heymac_path, "prv_key.pem")
    with open(fn, "wb") as f:
        f.write(prv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(passphrase)))
    print("Wrote: %s" % fn)

    # Save DER to a file
    fn = os.path.join(heymac_path, "pub_key.der")
    with open(fn, "wb") as f:
        f.write(der_bytes)
    print("Wrote: %s" % fn)

    # Create a HeyMac identity (credential) file including the public key
    fn = os.path.join(heymac_path, "mac_identity.json")
    with open(fn, "w") as f:
        json_str = json.dumps({
            "name": name,
            "callsign": callsign,
            # "key_bytes": key_bytes.hex()}) # Python 3.5 and later
            "pub_key": codecs.encode(key_bytes, 'hex').decode() # Python 3.4
            })
        f.write(json_str)
    print("Wrote: %s" % fn)
