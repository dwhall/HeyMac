"""
Copyright 2020 Dean Hall.  See LICENSE for details.

Data Link Layer (LNK) Heymac protocol command messages
"""


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


    def __init__(self, cmd_id):
        if cmd_id & ~HeymacCmd.CMD_MASK:
            raise HeymacCmdError("Command ID exceeds allowed bitfield")
        self.cmd_id = cmd_id


    @staticmethod
    def parse(cmd_bytes):
        if len(cmd_bytes) < 1:
            raise HeymacCmdError("HeymacCmd must be at least 1 byte")
        cmd = None
        for cmd_cls in HeymacCmd.__subclasses__():
            if (HeymacCmd.PREFIX | cmd_cls.CMD_ID) == cmd_bytes[0]:
                cmd = cmd_cls.parse(cmd_bytes)
                break
        if not cmd:
            raise HeymacCmdError("Unknown Command ID")
        return cmd


    def __bytes__(self,):
        b = bytearray()
        b.append(HeymacCmd.PREFIX | self.CMD_ID)
        if self.data:
            b.extend(self.data)
        if len(b) > 255:
            raise HeymacCmdError("")
        return bytes(b)


class HeymacCmdTxt(HeymacCmd):
    """Heymac Text message: {3, data }"""
    CMD_ID = 3

    def __init__(self, msg):
        super().__init__(HeymacCmdTxt.CMD_ID)
        assert type(msg) is bytes
        self.data = msg

    @staticmethod
    def parse(cmd_bytes):
        assert cmd_bytes[0] == HeymacCmd.PREFIX | HeymacCmdTxt.CMD_ID
        return HeymacCmdTxt(cmd_bytes[1:])


class HeymacCmdCsmaBcn(HeymacCmd):
    """Heymac CSMA Beacon: { 4, caps, status, nets[], ngbrs[] }"""
    # NOTE: form not finalized
    CMD_ID = 4

    def __init__(self, caps, status, nets, ngbrs):
        super().__init__(HeymacCmdCsmaBcn.CMD_ID)
        assert type(caps) is bytes and len(caps) == 2
        assert type(status) is bytes and len(status) == 2
        assert type(nets) is bytes
        assert type(ngbrs) is bytes
        self.data = caps + status + nets + ngbrs

    @staticmethod
    def parse(cmd_bytes):
        SIZEOF_NGBR = 1 # FIXME
        assert cmd_bytes[0] == HeymacCmd.PREFIX | HeymacCmdCsmaBcn.CMD_ID
        caps = cmd_bytes[1:3]
        status = cmd_bytes[3:5]
        nets_sz = 1 + cmd_bytes[5] * 2
        nets = cmd_bytes[5:5 + nets_sz]
        ngbrs_sz = 1 + cmd_bytes[5 + nets_sz] * SIZEOF_NGBR
        ngbrs = cmd_bytes[5 + nets_sz:5 + nets_sz + ngbrs_sz]
        return HeymacCmdCsmaBcn(caps, status, nets, ngbrs)


class HeymacCmdJoin(HeymacCmd):
    """Heymac Join: {5, sub_id}"""
    CMD_ID = 5


class HeymacCmdJoinRqst(HeymacCmdJoin):
    """Heymac Join-Request: {5, 1}"""
    SUB_ID = 1

    def __init__(self,):
        super().__init__(HeymacCmdJoin.CMD_ID, HeymacCmdJoinRqst.SUB_ID)


class HeymacCmdJoinRspd(HeymacCmdJoin):
    """Heymac Join-Respond: {5, 2}"""
    SUB_ID = 2

    def __init__(self,):
        super().__init__(HeymacCmdJoin.CMD_ID, HeymacCmdJoinRspd.SUB_ID)


class HeymacCmdJoinCnfm(HeymacCmdJoin):
    """Heymac Join-Confirm: {5, 3}"""
    SUB_ID = 3

    def __init__(self,):
        super().__init__(HeymacCmdJoin.CMD_ID, HeymacCmdJoinCnfm.SUB_ID)


class HeymacCmdJoinRjct(HeymacCmdJoin):
    """Heymac Join-Respond: {5, 4}"""
    SUB_ID = 4

    def __init__(self,):
        super().__init__(HeymacCmdJoin.CMD_ID, HeymacCmdJoinRjct.SUB_ID)


class HeymacCmdJoinLeav(HeymacCmdJoin):
    """Heymac Join-Leave: {5, 5}"""
    SUB_ID = 5

    def __init__(self,):
        super().__init__(HeymacCmdJoin.CMD_ID, HeymacCmdJoinLeav.SUB_ID)
