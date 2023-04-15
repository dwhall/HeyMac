"""
Copyright 2020 Dean Hall.  See LICENSE for details.

Data Link Layer (LNK) Heymac protocol command messages.

Heymac Commands are MAC and link-layer management
messages that convey command and data to a neighbor node.
All commands are designed to fit within one Heymac frame.

The first octet of the message defines the command ID.
Some commands use a sub-ID to distinguish related commands.

Commands may have either a fixed size or be of a variable length.
However, due to this author being lazy, Heymac command messages
have two restrictions on their format.
(1) A command of fixed size must be able to define its
serialization using Python's struct format. (2) A command of
variable length must only be composed of an arbitrary number
of identical entries.  The number of entries is specified after
the command ID (and optional sub-ID) and before the entries.
A maximum of 255 entries are allowed, but practically
that number must be lower for the command to fit within
one Heymac frame.
"""

from collections import namedtuple
import struct


class HeymacCmdError(Exception):
    pass


class HeymacCmd():
    """Heymac Command message parsing and serialization."""
    # Heymac segments (hdr, body, etc) have a small, unique bit pattern
    # at the start of the segment called a prefix.
    # The Command's prefix is two bits: '10'
    PREFIX = 0b10000000
    PREFIX_MASK = 0b11000000
    CMD_MASK = 0b00111111

    _SUB_ID = None
    _FLDS_CLS = None

    def __init__(self, *args, **kwargs):
        if self._FLDS_CLS:
            try:
                if kwargs:
                    self._fields = self._FLDS_CLS(**kwargs)
                else:
                    self._fields = self._FLDS_CLS(*args)
            except TypeError:
                raise HeymacCmdError()
        else:
            self._fields = None

    def __getattr__(self, attr):
        return getattr(self._fields, attr)

    def __bytes__(self):
        """Serializes the command into bytes to send over the air."""
        b = bytearray()
        b.append(HeymacCmd.PREFIX | self._CMD_ID)
        b.extend(struct.pack(self._FMT_STR, *self._fields))
        return bytes(b)

    @staticmethod
    def parse(cmd_bytes):
        """Parses the serialized cmd_bytes into a HeymacCommand subclass."""
        if len(cmd_bytes) < 1:
            raise HeymacCmdError("Insufficient data")

        cmd_cls = HeymacCmd._get_cmd_class(cmd_bytes)

        if issubclass(cmd_cls, HeymacCmdUnknown):
            cmd = HeymacCmdUnknown(cmd_bytes)
        else:
            if cmd_cls._SUB_ID:
                offset = 2
            else:
                offset = 1

            if issubclass(cmd_cls, HeymacCmdVarLen):
                n_entries = cmd_bytes[offset]
                offset += 1
                entries = list(struct.iter_unpack(cmd_cls._FMT_STR, cmd_bytes[offset:]))
                assert n_entries == len(entries)
                cmd = cmd_cls(entries)
            else:
                n_entries = 1
                cmd = cmd_cls(*struct.unpack(cmd_cls._FMT_STR, cmd_bytes[offset:]))
        return cmd

    @staticmethod
    def _get_cmd_class(cmd_bytes):
        all_cmd_classes = HeymacCmd.__subclasses__()
        all_cmd_classes.extend(HeymacCmdVarLen.__subclasses__())
        for cmd_cls in all_cmd_classes:
            if cmd_cls._CMD_ID > HeymacCmd.CMD_MASK:
                raise HeymacCmdError("Invalid _CMD_ID")
            if (HeymacCmd.PREFIX | cmd_cls._CMD_ID) == cmd_bytes[0]:
                if cmd_cls._SUB_ID:
                    if cmd_bytes[1] == cmd_cls._SUB_ID:
                        break
                else:
                    break
        else:
            cmd_cls = HeymacCmdUnknown
        return cmd_cls


class HeymacCmdUnknown():
    """An unknown Heymac Command."""
    _CMD_ID = 0

    def __init__(self, cmd_bytes):
        self.cmd_bytes = cmd_bytes


# TODO: create unit tests
class HeymacCmdVarLen(HeymacCmd):
    """A Heymac Command whose payload is variable-length, a sequence of entries."""
    _CMD_ID = -1

    def __init__(self, *args, **kwargs):
        if self._FLDS_CLS and (args or kwargs):
            try:
                if kwargs:
                    self._fields = [self._FLDS_CLS(**kwargs)]
                else:
                    self._fields = list(map(self._FLDS_CLS, *args))
            except TypeError:
                raise HeymacCmdError()
        else:
            self._fields = []

    def __bytes__(self):
        """Serializes the command into bytes to send over the air."""
        b = bytearray()
        b.append(HeymacCmd.PREFIX | self._CMD_ID)
        b.append(len(self._fields))
        [b.extend(struct.pack(self._FMT_STR, *f)) for f in self._fields]
        return bytes(b)

    def __getitem__(self, idx):
        return self._fields[idx]

    def __iter__(self):
        return iter(self._fields)

    def __len__(self):
        return len(self._fields)

    def append(self, **flds):
        # Keyword args are required in order to match the namedtuple() names
        named_flds = self._FLDS_CLS(**flds)
        self._fields.append(named_flds)


class HeymacCmdTxt(HeymacCmdVarLen):
    """Heymac command text message: {1, msg_len, msg}"""
    _CMD_ID = 1
    _FMT_STR = "!c"
    _FLDS_CLS = namedtuple("CmdTxt", ["msg"])

    def __bytes__(self):
        """Serializes the command into bytes to send over the air."""
        b = bytearray()
        b.append(HeymacCmd.PREFIX | self._CMD_ID)
        b.append(len(self.msg))
        b.extend(self.msg)
        return bytes(b)


class HeymacCmdBcn(HeymacCmd):
    """Heymac command beacon: {2, caps, status, callsign_ssid, pub_key}"""
    _CMD_ID = 2
    _FMT_STR = "!HH16s96s"
    _FLDS_CLS = namedtuple("CmdBcn", ["caps", "status", "callsign_ssid", "pub_key"])

    # Fix callsign_ssid: remove null padding and convert to a string
    def __getattr__(self, attr):
        retval = getattr(self._fields, attr)
        if attr == "callsign_ssid":
            retval = retval.rstrip(b"\x00")
        return retval


class HeymacCmdNgbrData(HeymacCmdVarLen):
    """Heymac neighbor data: {4, ngbr_cnt, (ngbr_lnk_addr)..}"""
    _CMD_ID = 4
    _FMT_STR = "!8s"
    _FLDS_CLS = namedtuple("CmdNgbrData", ["ngbr_lnk_addr"])


class HeymacCmdJoinRqst(HeymacCmd):
    """Heymac join-request: {5, 1, net_id}"""
    _CMD_ID = 5
    _SUB_ID = 1
    _FMT_STR = "!H"
    _FLDS_CLS = namedtuple("CmdJoinRqst", ["net_id"])


class HeymacCmdJoinAcpt(HeymacCmd):
    """Heymac join-accept: {5, 2, net_id, net_addr}"""
    _CMD_ID = 5
    _SUB_ID = 2
    _FMT_STR = "!HH"
    _FLDS_CLS = namedtuple("CmdJoinAcpt", ["net_id", "net_addr"])


class HeymacCmdJoinCnfm(HeymacCmd):
    """Heymac join-confirm: {5, 3, net_id, net_addr}"""
    _CMD_ID = 5
    _SUB_ID = 3
    _FMT_STR = "!HH"
    _FLDS_CLS = namedtuple("CmdJoinCnfm", ["net_id", "net_addr"])


class HeymacCmdJoinRjct(HeymacCmd):
    """Heymac join-reject: {5, 4}"""
    _CMD_ID = 5
    _SUB_ID = 4
