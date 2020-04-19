#!/usr/bin/env python3

"""
Copyright 2017 Dean Hall.  See LICENSE for details.

This module contains procedures to generate
a self-signed X.509 certificate
and asymmetric keypairs used by HeyMac.

First, a special keypair is made.  Elleptic Curve Cryptography
is used to generate an asymmetric key pair repeatedly
until the hash of the public key starts with 0xFC,
the personal prefix. The public key from this keypair is used
in the self-signed X.509 certificate which a Heymac operator
uses to identify himself and authenticate his messages.

For each device a Heymac operator employs, he creates another
asymmetric key pair, but this time the hash of the public key
starts with 0xFD, the device prefix.  A certificate is made
from the public key and signed wth the operator's personal credentials.

All keypairs and certificates are stored in an application-specific location,
The paths of all generated files are printed to the console as they are written.
The device keypairs and certificates must be copied to their respective devices;
that process is specific to the device/software being used.

WARNING: This tool does not protect the private key!
You should not use this keypair for meaningful cryptography!
In this project, we are using the keypair to authenticate
messages for recreational/amateur radio communication.

Dependencies::

    pip install asn1
    pip install cryptography

References:
    https://cryptography.io/en/latest/
    https://github.com/andrivet/python-asn1/blob/master/examples/dump.py
    https://en.wikipedia.org/wiki/Unique_local_address
"""

import argparse
import codecs
import datetime
import fnmatch
import getpass
import hashlib
import json
import os
import os.path
import random

import asn1 # pip install asn1
from cryptography import x509 # pip install cryptography
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from heymac import utl


WARNING = """WARNING: This tool does not protect the private key!
You should not use this keypair for meaningful cryptography!
In this project, we are using the keypair to authenticate
messages for recreational/amateur radio communication.
"""

CERT_DURATION_DAYS = 2 * 365  # X.509 certificate duration in days


def gen_personal_keypair():
    """Generates a fc/8 keypair.
    Note that fc/7 is the unique local prefix.
    """
    return _gen_specific_keypair("fc")

def gen_device_keypair():
    """Generates a fd/8 keypair.
    Note that fc/7 is the unique local prefix.
    """
    return _gen_specific_keypair("fd")

def gen_linklocal_keypair():
    """Generates a feb/12 keypair.
    Note that feb/12 is a subset of fe8/10
    the well-known link-local prefix.
    """
    return _gen_specific_keypair("feb")

def _gen_keypair():
    """Generates asymmetric keypair using elliptic curve SECP384R1.
    Returns (private key, public key)
    """
    prv_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
    return (prv_key, prv_key.public_key())

def _gen_specific_keypair(prefix):
    """Generates keypairs and forgets them
    until one is made where its hash has a specific prefix.
    """
    done = False
    while not done:
        prv_key, pub_key = _gen_keypair()
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
    pub_key_bytes = rdparse_asn1(decoder)
    # FIXME: pub_key_bytes is 98 bytes and always begins with "\x00\x04".
    #        So I remove those two leading bytes and use the remaining 96 bytes.
    #        Size agreement: 96 bytes == 768 bits == two 384 bit numbers (SECP384R1)
    pub_key_bytes = pub_key_bytes[2:]
    return pub_key_bytes


def _write_cred_to_json(pub_key, field_info):
    """Writes a HeyMac credential file including
    the common name, callsign and public key.
    field_info is a dict with entries for "cmn_name" and "callsign"
    """
    der_bytes = pub_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo)
    pub_key_bytes = _get_key_from_asn1(der_bytes)
    heymac_path = utl.get_app_data_path("HeyMac")
    fn = os.path.join(heymac_path, field_info["callsign"] + "_cred.json")
    with open(fn, "w") as f:
        json_str = json.dumps({
            "name": field_info["cmn_name"],
            "tac_id": field_info["callsign"],
            # "key_bytes": key_bytes.hex()}) # Python 3.5 and later
            "pub_key": codecs.encode(pub_key_bytes, 'hex').decode() # Python 3.4
            })
        f.write(json_str)
    print("Wrote: %s" % fn)


def _write_prv_key_to_pem(prv_key, field_info, passphrase):
    """Writes the private key to a .pem file.
    field_info is a dict with an entry for "callsign"
    passphrase is used to encrypt the private key.
    """
    heymac_path = utl.get_app_data_path("HeyMac")
    fn = os.path.join(heymac_path, field_info["callsign"] + "_prv.pem")
    with open(fn, "wb") as f:
        f.write(prv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(passphrase)))
    print("Wrote: %s" % fn)


def _write_pub_key_to_der(pub_key, field_info):
    """Writes the public key to a .der file.
    field_info is a dict with an entry for "callsign"
    that is either a callsign or a tactical-id (callsign-###).
    """
    heymac_path = utl.get_app_data_path("HeyMac")
    fn = os.path.join(heymac_path, field_info["callsign"] + "_pub.der")
    with open(fn, "wb") as f:
        f.write(pub_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo))
    print("Wrote: %s" % fn)


def _write_cert_to_x509(pub_key, prv_key, person_info):
    """Writes a self-signed X.509 certificate to a file
    using info from the given person_info dict
    """
    # Generate a self-signed certificate (subject and issuer are the same)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, person_info["cmn_name"]),
        x509.NameAttribute(NameOID.PSEUDONYM, person_info["callsign"]),
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, person_info["email"]),
        x509.NameAttribute(NameOID.COUNTRY_NAME, person_info["country_name"]),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, person_info["prov_name"]),
        x509.NameAttribute(NameOID.POSTAL_CODE, person_info["zipcode"]),])
    now = datetime.datetime.utcnow()
    cert = x509.CertificateBuilder().subject_name( subject
        ).issuer_name( issuer
        ).public_key( pub_key
        ).serial_number( x509.random_serial_number()
        ).not_valid_before( now
        ).not_valid_after( now + datetime.timedelta(days=CERT_DURATION_DAYS)
        ).add_extension( x509.SubjectAlternativeName([x509.DNSName(u"localhost")]), critical=False,
        # Sign the certificate with the private key
        ).sign(prv_key, hashes.SHA256(), default_backend())
    # Save the certificate to a file.
    heymac_path = utl.get_app_data_path("HeyMac")
    fn = os.path.join(heymac_path, person_info["callsign"] + "_cert.pem")
    with open(fn, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print("Wrote: %s" % fn)


def gen_device_credentials():
    """Generates a set of device credential files.
    Opens the personal certificate to get the callsign and common name.
    Generates a new keypair and asks for a passphrase
    to protect the private key.
    Writes a private key .pem file a public key .der file
    and an application specific credential .json file
    """
    heymac_path = utl.get_app_data_path("HeyMac")

    # Find the personal certificate
    result = []
    for root, dirs, files in os.walk(heymac_path):
        for fn in files:
            if fnmatch.fnmatch(fn, "*cert.pem"):
                result.append(os.path.join(root, fn))
    cert_file_cnt = len(result)
    assert cert_file_cnt == 1, "Aborting.  Expected one cert file, but found %d." % cert_file_cnt
    cert_fn = result[0]

    # Read the personal certificate
    with open(cert_fn, "rb") as f:
        pem_data = f.read()
    cert = x509.load_pem_x509_certificate(pem_data, default_backend())
    name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    callsign = cert.subject.get_attributes_for_oid(NameOID.PSEUDONYM)[0].value
    print("Using info from personal certificate of %s (%s)" % (name, callsign))

    # Get input for the private key passphrase
    print(WARNING)

    passphrase = getpass.getpass("Private key encryption passphrase: ")
    passphrase = passphrase.encode()

    # Use input and certificate data to build the device info
    dev_info = {}
    dev_id = input("Tactical ID (callsign-###): %s-" % callsign)
    dev_info["callsign"] = callsign + '-' + dev_id
    dev_info["cmn_name"] = name

    # Generate a keypair and write the credential files
    prv_key, pub_key = gen_device_keypair()
    _write_prv_key_to_pem(prv_key, dev_info, passphrase)
    _write_pub_key_to_der(pub_key, dev_info)
    _write_cred_to_json(pub_key, dev_info)


def gen_personal_credentials():
    """Generates a set of personal credential files.
    Generates a new keypair, asks for a passphrase
    to protect the private key and writes
    an X.509 self-signed certificate, a private key .pem file
    a public key .der file and an application specific credential .json file
    """
    print(WARNING)

    # Generate a special keypair
    prv_key, pub_key = gen_personal_keypair()

    # Get a passphrase to encrypt the private key for local storage
    passphrase = getpass.getpass("Private key encryption passphrase: ")
    passphrase = passphrase.encode()

    # Get input for the certificate
    print("Enter data for an X.509 certificate.")
    person_info = {}
    person_info["cmn_name"] = input("Common name: ")
    person_info["callsign"] = input("Callsign: ")
    person_info["email"] = input("Email: ")
    person_info["country_name"] = input("Country name: ")
    person_info["prov_name"] = input("State or province name: ")
    person_info["zipcode"] = input("Postal/zip code: ")

    # Write the credential files
    _write_cert_to_x509(pub_key, prv_key, person_info)
    _write_prv_key_to_pem(prv_key, person_info, passphrase)
    _write_pub_key_to_der(pub_key, person_info)
    _write_cred_to_json(pub_key, person_info)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", default=False, help='Generate device credential files')
    #parser.add_argument("-d", "--device", default=True, help='Generate device credential files')
    args = parser.parse_args()

    if bool(args.device):
        gen_device_credentials()
    else:
        gen_personal_credentials()
