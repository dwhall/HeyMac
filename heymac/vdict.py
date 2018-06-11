#!/usr/bin/env python3


import collections, time

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
        self.valid = {}
        self.timestamp = {}
        self.default_expdelta = None
        self.expdelta = {}
        now = time.time()
        for k in initialdata:
            self.data[k] = initialdata[k]
            self.valid[k] = False
            self.timestamp[k] = now
            self.expdelta[k] = None

    def __getitem__(self, key):
        """Returns an item from the dict in a tuple (value, validity).
        """
        # Item-specific expiration overrides default expiration
        exp = self.default_expdelta
        if self.expdelta[key] is not None:
            exp = self.expdelta[key]

        # If there is an expiration, invalidate if stale
        if exp:
            if time.time() > self.timestamp[key] + exp:
                self.valid[key] = False

        return ValueValid(self.data[key], self.valid[key])

    def __setitem__(self, key, value, valid=True):
        """Sets a key,value in the dictionary.
        Also updates the item's validity and timestamp.
        """
        self.data[key] = value
        self.timestamp[key] = time.time()
        self.valid[key] = valid
        self.expdelta[key] = self.default_expdelta

    def set_default_expiration(self, delta):
        """Sets the default expiration delta [float] for all items
        """
        self.default_expdelta = delta

    def set_expiration(self, key, delta):
        """Sets the expiration delta [float] for a specific item
        """
        self.expdelta[key] = delta
