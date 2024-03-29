#!/usr/bin/env python3

"""
Copyright 2017 Dean Hall.  See LICENSE for details.

A command-line tool to drive ham_ident
to generate personal and device credential files
used by the `HeyMac network stack <https://github.com/dwhall/heymac>`.

Personal files go in the HamIdent application folder,
while device files go in the HeyMac application folder.

References
----------

ISO 3166 Alpha-2 Country codes:
    https://www.nationsonline.org/oneworld/country_code_list.htm
"""

import argparse
import getpass

from heymac.utl import HamIdent


WARNING = """WARNING: This tool does not protect the private key!
You should not use this keypair for meaningful cryptography!
In this project, we are using the keypair to authenticate
messages for recreational/amateur radio communication.
"""


def main(args):
    print(WARNING)
    if bool(args.device):
        assert HamIdent.cert_file_exists(), \
            "A personal credential MUST exist " \
            "in order to create a device credential"
        _gen_device_credentials()
    else:
        assert not HamIdent.cert_file_exists(), \
            "Exiting to prevent overwriting existing credentials."
        _gen_personal_credentials()


def _gen_device_credentials():
    person_info = HamIdent.get_info_from_cert()
    ssid = input("SSID (callsign-###): %s-" % person_info["callsign"])
    passphrase = _input_passphrase()
    ident = HamIdent("HeyMac")
    ident.gen_device_credentials(ssid, passphrase)


def _gen_personal_credentials():
    person_info = _input_person_info()
    passphrase = _input_passphrase()
    ident = HamIdent()
    ident.gen_personal_credentials(person_info, passphrase)


def _input_passphrase():
    passphrase = getpass.getpass("Private key encryption passphrase: ")
    return passphrase.encode()


def _input_person_info():
    print("Enter data for an X.509 certificate.")
    person_info = {}
    person_info["cmn_name"] = input("Common name: ")
    person_info["callsign"] = input("Callsign: ")
    person_info["email"] = input("Email: ")
    person_info["country"] = input("Country code (ISO Alpha-2): ")
    person_info["province"] = input("State or province name: ")
    person_info["postalcode"] = input("Postal/zip code: ")
    return person_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", default=False, help='Generate device credential files')
    args = parser.parse_args()
    main(args)
