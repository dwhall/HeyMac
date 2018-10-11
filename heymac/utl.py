#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.
"""

import json
import os
import sys


def get_app_data_path(app_name):
    """Returns the OS-specific path to Application Data for the given App

    NOTE: Darwin: https://developer.apple.com/reference/foundation/1414224-nssearchpathfordirectoriesindoma?language=objc
    """
    assert type(app_name) == str

    if sys.platform == 'darwin':
        from AppKit import NSSearchPathForDirectoriesInDomains, NSApplicationSupportDirectory, NSUserDomainMask
        app_data_path = os.path.join(NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, True)[0], app_name)
    elif sys.platform == 'win32':
        app_data_path = os.path.join(os.environ['APPDATA'], app_name)
    else:
        app_data_path = os.path.expanduser(os.path.join("~", "." + app_name))

    if not os.path.exists(app_data_path):
        os.mkdir(app_data_path)

    return app_data_path


def get_from_json(app_name, fn):
    """Returns a Python dict built from reading the given file as a JSON object.
    """
    file_path = os.path.join(get_app_data_path(app_name), fn)
    with open(file_path) as f:
        data = json.load(f)
    return data
