#!/usr/bin/env python3
"""
Copyright 2021 Dean Hall.  See LICENSE for details.
"""

import os
import shelve
import sys


def get_app_data_path(app_name):
    """Returns the OS-specific path to Application Data for the given App.
    Creates the path if it doesn't already exist.

    NOTE: Darwin: https://developer.apple.com/reference/foundation/1414224-nssearchpathfordirectoriesindoma?language=objc
    """
    assert type(app_name) == str

    if sys.platform.startswith('darwin'):
        from AppKit import \
            NSSearchPathForDirectoriesInDomains, \
            NSApplicationSupportDirectory, \
            NSUserDomainMask    # pip install pyobjc
        app_data_path = os.path.join(
            NSSearchPathForDirectoriesInDomains(
                NSApplicationSupportDirectory,
                NSUserDomainMask,
                True)[0], app_name)

    elif sys.platform.startswith('win32'):
        app_data_path = os.path.join(os.environ['APPDATA'], app_name)

    elif sys.platform.startswith('linux') \
            or sys.platform.startswith('freebsd'):  # freebsd is untested
        app_data_path = os.path.expanduser(os.path.join("~", "." + app_name))

    else:
        raise NotImplementedError("The platform, {}, is not supported."
                                  .format(sys.platform))

    if not os.path.exists(app_data_path):
        os.mkdir(app_data_path)

    return app_data_path


def open_app_data_shelve(app_name):
    """Opens and returns a Python shelve object backed by a file
    in the app data path.  The caller MUST close the shelve object.
    """
    fn = app_name + ".shelve"
    file_path = os.path.join(get_app_data_path(app_name), fn)
    return shelve.open(file_path, flag='c', writeback=True)
