"""
Copyright 2020 Dean Hall.  See LICENSE for details.

Data Link Layer (LNK) Heymac protocol command messages
"""

import struct


class HeymacCmdError(Exception):
    pass


class HeymacCmd(object):
    """A Heymac Command message

    Offers methods to serialize and parse Heymac Command bytes.
    """
    # Heymac segments (hdr, body, etc) have a small, unique bit pattern
    # at the start of the segment called a prefix.
    # The Command's prefix is two bits: '10'
    PREFIX = 0b10000000
    PREFIX_MASK = 0b11000000
    CMD_MASK = 0b00111111

    # Field names are used to index into each
    # Heymac commands' self.field dict.
    FLD_CAPS = "FLD_CAPS"       # int (0..65535)
    FLD_MSG = "FLD_MSG"         # bytes
    FLD_NETS = "FLD_NETS"       # sequence of bytes
    FLD_NGBRS = "FLD_NGBRS"     # sequence of bytes
    FLD_STATUS = "FLD_STATUS"   # int (0..65535)
    FLD_NET_ID = "FLD_NET_ID"   # int (0..65535)
    FLD_NET_ADDR = "FLD_NET_ADDR"   # int (0..65535)


    def __init__(self, *args, **kwargs):
        """Instantiates a subclass of HeymacCmd

        Expects either one positional arg that is the
        serialized bytes for a HeymacCmd subclass,
        or expects one positional arg and one or more keyword args.
        In the latter case, the positional arg is the command ID
        and the keyword args are the field names and values.
        (see the code comments for FLD_* (above) to know the data type)
        """
        if len(args) != 1:
            raise TypeError("Expecting one positional argument")

        if kwargs:
            assert type(args[0]) is int, "Expecting Command ID int"
            # If keyword arguments, expect certain field names
            for key in kwargs.keys():
                if key not in self._FLD_LIST:
                    raise HeymacCmdError("Unknown field: %s" % key)
            # kwargs become the command's fields
            self.field = kwargs
        else:
            if type(args[0]) is bytes:
                cmd_bytes = args[0]
            elif type(args[0]) is int:
                self.field = {}
            else:
                raise TypeError()


    @staticmethod
    def parse(cmd_bytes):
        """Parses the serialized cmd_bytes into a HeymacCommand subclass.

        Uses the subclass 's parse() method to perform specific parsing.
        """
        assert type(cmd_bytes) is bytes
        if len(cmd_bytes) < 1:
            raise HeymacCmdError("Insufficient data")
        cmd = None
        for cmd_cls in HeymacCmd.__subclasses__():
            if (HeymacCmd.PREFIX | cmd_cls.CMD_ID) == cmd_bytes[0]:
                cmd = cmd_cls.parse(cmd_bytes)
                break
        if not cmd:
            raise HeymacCmdError("Unknown CMD_ID: %d"
                                 % (cmd_bytes[0] & HeymacCmd.CMD_MASK))
        return cmd


    def get_field(self, fld_name):
        """Returns the value of the field."""
        return self.field[fld_name]


class HeymacCmdTxt(HeymacCmd):
    """Heymac Text message: {3, data }"""
    CMD_ID = 3
    _FLD_LIST = (HeymacCmd.FLD_MSG,)

    def __init__(self, *args, **kwargs):
        super().__init__(self.CMD_ID, **kwargs)

    def __bytes__(self,):
        b = bytearray()
        b.append(HeymacCmd.PREFIX | HeymacCmdTxt.CMD_ID)
        b.extend(self.field[HeymacCmd.FLD_MSG])
        return bytes(b)

    @staticmethod
    def parse(cmd_bytes):
        assert cmd_bytes[0] == HeymacCmd.PREFIX | HeymacCmdTxt.CMD_ID
        field = {}
        field[HeymacCmd.FLD_MSG] = cmd_bytes[1:]
        return HeymacCmdTxt(HeymacCmdTxt.CMD_ID, **field)


class HeymacCmdCsmaBcn(HeymacCmd):
    """Heymac CSMA Beacon: { 4, caps, status, nets[], ngbrs[] }"""
    # NOTE: form not finalized
    CMD_ID = 4
    _FLD_LIST = (
        HeymacCmd.FLD_CAPS,
        HeymacCmd.FLD_STATUS,
        HeymacCmd.FLD_NETS,
        HeymacCmd.FLD_NGBRS)

    def __init__(self, *args, **kwargs):
        super().__init__(self.CMD_ID, **kwargs)

    def __bytes__(self,):
        """Serializes the beacon into bytes to send over the air."""
        b = bytearray()
        b.append(HeymacCmd.PREFIX | HeymacCmdCsmaBcn.CMD_ID)
        b.extend(struct.pack("!H", self.field[HeymacCmd.FLD_CAPS]))
        b.extend(struct.pack("!H", self.field[HeymacCmd.FLD_STATUS]))
        # Nets
        b.append(len(self.field[HeymacCmd.FLD_NETS]))
        for net in self.field[HeymacCmd.FLD_NETS]:
            b.extend(struct.pack("!H", net[0]))
            b.extend(struct.pack("8s", net[1]))
        # Ngbrs
        b.append(len(self.field[HeymacCmd.FLD_NGBRS]))
        for lnk_addr in self.field[HeymacCmd.FLD_NGBRS]:
            b.extend(lnk_addr)
        return bytes(b)

    @staticmethod
    def parse(cmd_bytes):
        """Parses the bytes into a beacon object."""
        SIZEOF_NET = 2 + 8
        assert cmd_bytes[0] == HeymacCmd.PREFIX | HeymacCmdCsmaBcn.CMD_ID
        field = {}
        field[HeymacCmd.FLD_CAPS] = struct.unpack("!H", cmd_bytes[1:3])[0]
        field[HeymacCmd.FLD_STATUS] = struct.unpack("!H", cmd_bytes[3:5])[0]
        # Nets
        nets_cnt = cmd_bytes[5]
        fmt = "!" + "H8s" * nets_cnt
        nets_sz = struct.calcsize(fmt)
        field[HeymacCmd.FLD_NETS] = struct.unpack(fmt, cmd_bytes[6:6 + nets_sz])
        offset = 6 + nets_sz
        # Ngbrs
        ngbrs_cnt = cmd_bytes[offset]
        fmt = "!" + "8s" * ngbrs_cnt
        field[HeymacCmd.FLD_NGBRS] = struct.unpack(fmt, cmd_bytes[offset + 1:])
        return HeymacCmdCsmaBcn(HeymacCmdCsmaBcn.CMD_ID, **field)


class HeymacCmdJoin(HeymacCmd):
    """Heymac Join: {5, sub_id, ...}

    This class should not be instantiated outside this module.
    This class serves as a base class for a range of join sub-commands.
    """
    CMD_ID = 5

    def __init__(self, *args, **kwargs):
        super().__init__(self.CMD_ID, **kwargs)

    def __bytes__(self,):
        """Serializes the join-command into bytes."""
        b = bytearray()
        b.append(HeymacCmd.PREFIX | self.CMD_ID)
        b.append(self.SUB_ID)
        if HeymacCmd.FLD_NET_ID in self.field:
            b.extend(struct.pack("!H", self.field[HeymacCmd.FLD_NET_ID]))
        if HeymacCmd.FLD_NET_ADDR in self.field:
            b.extend(struct.pack("!H", self.field[HeymacCmd.FLD_NET_ADDR]))
        return bytes(b)

    @staticmethod
    def parse(cmd_bytes):
        """Parses the bytes into a join-command object."""
        assert type(cmd_bytes) is bytes
        if len(cmd_bytes) < 2:
            raise HeymacCmdError("Insufficient data")
        if cmd_bytes[0] != (HeymacCmd.PREFIX | HeymacCmdJoin.CMD_ID):
            raise HeymacCmdError("Incorrect CMD_ID: %d"
                                 % (cmd_bytes[0] & HeymacCmd.CMD_MASK))
        cmd = None
        for joincmd_cls in HeymacCmdJoin.__subclasses__():
            if joincmd_cls.SUB_ID == cmd_bytes[1]:
                try:
                    if joincmd_cls.SUB_ID in (HeymacCmdJoinRqst.SUB_ID,):
                        field = {}
                        net_id = struct.unpack("!H", cmd_bytes[2:])[0]
                        field[HeymacCmd.FLD_NET_ID] = net_id
                        cmd = joincmd_cls(HeymacCmdTxt.CMD_ID, **field)
                        break
                    elif joincmd_cls.SUB_ID in (HeymacCmdJoinAcpt.SUB_ID,
                                                HeymacCmdJoinCnfm.SUB_ID):
                        field = {}
                        net_id, net_addr = struct.unpack("!HH", cmd_bytes[2:])
                        field[HeymacCmd.FLD_NET_ID] = net_id
                        field[HeymacCmd.FLD_NET_ADDR] = net_addr
                        cmd = joincmd_cls(HeymacCmdTxt.CMD_ID, **field)
                        break
                    else:
                        assert len(cmd_bytes) == 2
                        cmd = joincmd_cls()
                        break
                except struct.error:
                    raise HeymacCmdError("Incorrect data size")
                except AssertionError:
                    raise HeymacCmdError("Incorrect data size")
        if not cmd:
            raise HeymacCmdError("Unknown SUB_ID: %d" % cmd_bytes[1])
        return cmd


class HeymacCmdJoinRqst(HeymacCmdJoin):
    """Heymac Join-Request: {5, 1, net_id}"""
    SUB_ID = 1
    _FLD_LIST = (HeymacCmd.FLD_NET_ID,)


class HeymacCmdJoinAcpt(HeymacCmdJoin):
    """Heymac Join-Accept: {5, 2, net_id, net_addr}"""
    SUB_ID = 2
    _FLD_LIST = (HeymacCmd.FLD_NET_ID, HeymacCmd.FLD_NET_ADDR)


class HeymacCmdJoinCnfm(HeymacCmdJoin):
    """Heymac Join-Confirm: {5, 3, net_id, net_addr}"""
    SUB_ID = 3
    _FLD_LIST = (HeymacCmd.FLD_NET_ID, HeymacCmd.FLD_NET_ADDR)


class HeymacCmdJoinRjct(HeymacCmdJoin):
    """Heymac Join-Reject: {5, 4}"""
    SUB_ID = 4
    _FLD_LIST = ()


class HeymacCmdJoinLeav(HeymacCmdJoin):
    """Heymac Join-Leave: {5, 5}"""
    SUB_ID = 5
    _FLD_LIST = ()
