#!/usr/bin/env python3


import collections
import time


class ValueValid(object):
    def __init__(self, value, valid=False):
        self._value = value
        self._valid = valid

    def __str__(self,):
        return str((self._value, self._valid))

    @property
    def value(self,):
        return self._value

    @property
    def valid(self,):
        return self._valid


class ValidatedDict(collections.UserDict):
    """A dictionary for data items whose values and validity must be tracked.
    When an item from an instance of this class is requested, v[k],
    the returned item is a tuple of (value, validity:boolean).

    If you give an expiration delta via v.set_expiration(key, deltasecs:float),
    then the returned value will also be invalidated if it is stale (in time).
    """
    def __init__(self, initialdata={}):
        super().__init__(initialdata)
        self._valid = {}
        self._timestamp = {}
        self._default_expdelta = None
        self._expdelta = {}
        now = time.time()
        for k in initialdata:
            self.data[k] = initialdata[k]
            self._valid[k] = False
            self._timestamp[k] = now
            self._expdelta[k] = None

    def __getitem__(self, key):
        """Returns an item from the dict wrapped in a ValueValid obj (.value, .valid).
        """
        # Item-specific expiration overrides default expiration
        exp = self._default_expdelta
        if self._expdelta[key] is not None:
            exp = self._expdelta[key]

        # If there is an expiration, invalidate if stale
        if exp:
            if time.time() > self._timestamp[key] + exp:
                self._valid[key] = False

        return ValueValid(self.data[key], self._valid[key])

    def __setitem__(self, key, value, valid=True):
        """Sets a key,value in the dictionary.
        Also updates the item's validity and timestamp.
        """
        self.data[key] = value
        self._timestamp[key] = time.time()
        self._valid[key] = valid
        self._expdelta[key] = self._default_expdelta

    def set_default_expiration(self, delta):
        """Sets the default expiration delta [float] for all items
        """
        self._default_expdelta = delta

    def set_expiration(self, key, delta):
        """Sets the expiration delta [float] for a specific item
        """
        self._expdelta[key] = delta
