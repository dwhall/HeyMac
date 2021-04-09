"""
Copyright 2017 Dean Hall.  See LICENSE for details.

This module contains the HamIdent class which has methods to generate
a self-signed X.509 certificate and asymmetric keypairs which are
used to create various kinds of personal and device credential files.
All keypairs and certificates are stored in an application-specific location.

First, a special keypair is made.  Elleptic Curve Cryptography
is used to repeatedly generate asymmetric key pairs until
a public key is found whose hash starts with 0xFC, the personal prefix.
A self-signed X.509 certificate is created from this key pair.
The keypair may be used for cryptographic authentication.
The hash of the public key (that begins with 0xFC) may
be used to construct sufficiently unique network address
such as a mobile, `unique-local`_ IPv6 address.

.. _unique-local: https://en.wikipedia.org/wiki/Unique_local_address

Similarly, credential files may be created for individual devices.
Such credentials have a unique asymmetric key pair,
but this time the hash of the public key starts with 0xFD,
the device prefix.  X.509 certificates are NOT created for devices.

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

import datetime
import fnmatch
import hashlib
import json
import os.path

import asn1 # pip install asn1
from cryptography import x509 # pip install cryptography
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from . import app_data


TWO_YEARS = 2 * 365  # X.509 certificate duration in days


class HamIdent(object):
    def __init__(self, app_name="HamIdent", cert_duration=TWO_YEARS):
        self.app_path = app_data.get_app_data_path(app_name)
        self.cert_duration = cert_duration


    @staticmethod
    def cert_file_exists():
        try:
            cert_fn = HamIdent._get_cert_fn()
            return os.path.exists(cert_fn)
        except AssertionError:
            return False


    @staticmethod
    def get_info_from_cert():
        person_info = {}
        fn = HamIdent._get_cert_fn()
        with open(fn, "rb") as f:
            pem_data = f.read()
            cert = x509.load_pem_x509_certificate(pem_data, default_backend())
            person_info["cmn_name"] = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            person_info["callsign"] = cert.subject.get_attributes_for_oid(NameOID.PSEUDONYM)[0].value
            person_info["email"] = cert.subject.get_attributes_for_oid(NameOID.EMAIL_ADDRESS)[0].value
            person_info["country"] = cert.subject.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value
            person_info["province"] = cert.subject.get_attributes_for_oid(NameOID.STATE_OR_PROVINCE_NAME)[0].value
            person_info["postalcode"] = cert.subject.get_attributes_for_oid(NameOID.POSTAL_CODE)[0].value
        return person_info

    @staticmethod
    def _get_cert_fn(app_name="HamIdent"):
        app_path = app_data.get_app_data_path(app_name)
        result = []
        for root, _, files in os.walk(app_path):
            for fn in files:
                if fnmatch.fnmatch(fn, "*cert.pem"):
                    result.append(os.path.join(root, fn))
        assert len(result) == 1, "Expected one cert file"
        return result[0]


    @staticmethod
    def get_info_from_json_cred(app_name):
        fn = HamIdent._get_cred_fn(app_name)
        with open(fn) as f:
            json_info = json.load(f)
        return json_info

    @staticmethod
    def _get_cred_fn(app_name):
        app_path = app_data.get_app_data_path(app_name)
        result = []
        for root, _, files in os.walk(app_path):
            for fn in files:
                if fnmatch.fnmatch(fn, "*_cred.json"):
                    result.append(os.path.join(root, fn))
        assert len(result) == 1, "Expected one cred file"
        return result[0]


    @staticmethod
    def get_long_addr(app_name):
        """Returns a long address that is computed from
        the public key found in the app's pre-made JSON file.
        The callsign_ssid may or may not have the SSID.
        """
        pub_key = HamIdent._get_key_from_json(app_name)
        saddr = HamIdent._get_addr_from_key(pub_key)
        assert saddr[0] in (0xfc, 0xfd), "Credential not valid"
        return saddr

    @staticmethod
    def _get_key_from_json(app_name):
        json_info = HamIdent.get_info_from_json_cred(app_name)
        return bytearray.fromhex(json_info['pub_key'])

    @staticmethod
    def _get_addr_from_key(pub_key):
        h = hashlib.sha512()
        h.update(pub_key)
        h.update(h.digest())
        return h.digest()[:8]


    @staticmethod
    def gen_personal_keypair():
        """Generates a fc/8 keypair (fc/7 is the unique local prefix)."""
        return HamIdent._gen_keypair_with_prefix("fc")

    @staticmethod
    def gen_device_keypair():
        """Generates a fd/8 keypair (fc/7 is the unique local prefix)."""
        return HamIdent._gen_keypair_with_prefix("fd")

    @staticmethod
    def gen_linklocal_keypair():
        """Generates a feb/12 keypair
        (feb/12 is a subset of fe8/10
        the well-known link-local prefix).
        """
        return HamIdent._gen_keypair_with_prefix("feb")

    @staticmethod
    def _gen_keypair_with_prefix(prefix):
        """Repeatedly generates a keypair and forgets it
        until one is made where its hash has the given prefix.
        """
        done = False
        while not done:
            prv_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
            pub_key = prv_key.public_key()
            der_bytes = pub_key.public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo)
            pub_key_bytes = HamIdent._get_key_from_asn1(der_bytes)
            h = hashlib.sha512()
            h.update(pub_key_bytes)
            h.update(h.digest())
            done = h.hexdigest().startswith(prefix)
        return (prv_key, pub_key)

    @staticmethod
    def _get_key_from_asn1(der_bytes):
        """Returns the key bytes from a PublicKey instance
        whose DER encoding resembles:
        [U] SEQUENCE
            [U] SEQUENCE
                [U] OBJECT: 1.2.840.10045.2.1
                [U] OBJECT: 1.3.132.0.34
            [U] BIT STRING:<key bytes>
        """
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

        decoder = asn1.Decoder()
        decoder.start(der_bytes)
        pub_key_bytes = rdparse_asn1(decoder)
        # FIXME: pub_key_bytes is 98 bytes and always begins with "\x00\x04".
        #        So I remove those two leading bytes and use the remaining 96 bytes.
        #        Size agreement: 96 bytes == 768 bits == two 384 bit numbers (SECP384R1)
        pub_key_bytes = pub_key_bytes[2:]
        return pub_key_bytes


    def gen_device_credentials(self, ssid, passphrase):
        """Generates a set of device credential files.
        Opens the personal certificate to get the callsign and common name.
        Generates a new keypair and asks for a passphrase
        to protect the private key.
        Writes a private key .pem file a public key .der file
        and an application specific credential .json file
        """
        person_info = HamIdent.get_info_from_cert()
        dev_info = {}
        dev_info["callsign"] = person_info["callsign"] + '-' + ssid
        dev_info["cmn_name"] = person_info["cmn_name"]

        prv_key, pub_key = HamIdent.gen_device_keypair()
        self._write_prv_key_to_pem(prv_key, dev_info, passphrase)
        self._write_pub_key_to_der(pub_key, dev_info)
        self._write_cred_to_json(pub_key, dev_info)


    def gen_personal_credentials(self, person_info, passphrase):
        """Generates a set of personal credential files.
        Generates a new keypair, asks for a passphrase
        to protect the private key and writes
        an X.509 self-signed certificate, a private key .pem file
        a public key .der file and an application specific credential .json file
        """
        prv_key, pub_key = HamIdent.gen_personal_keypair()
        self._write_cert_to_x509(pub_key, prv_key, person_info)
        self._write_prv_key_to_pem(prv_key, person_info, passphrase)
        self._write_pub_key_to_der(pub_key, person_info)
        self._write_cred_to_json(pub_key, person_info)


    def _write_prv_key_to_pem(self, prv_key, field_info, passphrase):
        """Writes the private key to a .pem file.
        field_info is a dict with an entry for "callsign"
        passphrase is used to encrypt the private key.
        """
        fn = os.path.join(self.app_path, field_info["callsign"] + "_prv.pem")
        with open(fn, "wb") as f:
            f.write(prv_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.BestAvailableEncryption(passphrase)))
        return fn


    def _write_pub_key_to_der(self, pub_key, field_info):
        """Writes the public key to a .der file.
        field_info is a dict with an entry for "callsign"
        that is either a callsign or a tactical-id (callsign-###).
        """
        fn = os.path.join(self.app_path, field_info["callsign"] + "_pub.der")
        with open(fn, "wb") as f:
            f.write(pub_key.public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo))
        return fn


    def _write_cert_to_x509(self, pub_key, prv_key, person_info):
        """Writes a self-signed X.509 certificate to a file
        using info from the given person_info dict
        """
        # Generate a self-signed certificate (subject and issuer are the same)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, person_info["cmn_name"]),
            x509.NameAttribute(NameOID.PSEUDONYM, person_info["callsign"]),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, person_info["email"]),
            x509.NameAttribute(NameOID.COUNTRY_NAME, person_info["country"]),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, person_info["province"]),
            x509.NameAttribute(NameOID.POSTAL_CODE, person_info["postalcode"]),])
        now = datetime.datetime.utcnow()
        cert = x509.CertificateBuilder().subject_name( subject
            ).issuer_name( issuer
            ).public_key( pub_key
            ).serial_number( x509.random_serial_number()
            ).not_valid_before( now
            ).not_valid_after( now + datetime.timedelta(days=self.cert_duration)
            ).add_extension( x509.SubjectAlternativeName([x509.DNSName(u"localhost")]), critical=False,
            # Sign the certificate with the private key
            ).sign(prv_key, hashes.SHA256(), default_backend())
        # Save the certificate to a file.
        fn = os.path.join(self.app_path, person_info["callsign"] + "_cert.pem")
        with open(fn, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return fn


    def _write_cred_to_json(self, pub_key, field_info):
        """Writes a JSON credential file including
        the fields: common name, callsign and public key.
        field_info is a dict with entries for "cmn_name" and "callsign"
        """
        der_bytes = pub_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        pub_key_bytes = HamIdent._get_key_from_asn1(der_bytes)
        cred = {"cmn_name": field_info["cmn_name"],
                "callsign": field_info["callsign"],
                "pub_key": pub_key_bytes.hex()}

        fn = os.path.join(self.app_path, field_info["callsign"] + "_cred.json")
        with open(fn, "w") as f:
            json.dump(cred, f)
        return fn
