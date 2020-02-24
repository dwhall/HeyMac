"""
Copyright 2020 Dean Hall.  See LICENSE file for details.
"""

from .mac_cmds import HeyMacCmd, HeyMacCmdJoin


class HeyMacCmdJoinRequest(HeyMacCmdJoin):
    MID = HeyMacCmdJoin.MID_RQST
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties: .cmd, instead.
        ('_cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmd.CID_JOIN),
        ('mid', 'B', HeyMacCmdJoin.MID_RQST),
        ('net_id', 'H', 0),
    )

class HeyMacCmdJoinRespond(HeyMacCmdJoin):
    MID = HeyMacCmdJoin.MID_RSPD
    __hdr__ = (
        ('_cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmd.CID_JOIN),
        ('mid', 'B', HeyMacCmdJoin.MID_RSPD),
        ('short_addr', 'H', 0),
    )

class HeyMacCmdJoinConfirm(HeyMacCmdJoin):
    MID = HeyMacCmdJoin.MID_CNFM
    __hdr__ = (
        ('_cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmd.CID_JOIN),
        ('mid', 'B', HeyMacCmdJoin.MID_CNFM),
        ('short_addr', 'H', 0),
    )

class HeyMacCmdJoinReject(HeyMacCmdJoin):
    MID = HeyMacCmdJoin.MID_RJCT
    __hdr__ = (
        ('_cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmd.CID_JOIN),
        ('mid', 'B', HeyMacCmdJoin.MID_RJCT),
    )

class HeyMacCmdJoinLeave(HeyMacCmdJoin):
    MID = HeyMacCmdJoin.MID_LEAV
    __hdr__ = (
        ('_cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmd.CID_JOIN),
        ('mid', 'B', HeyMacCmdJoin.MID_LEAV),
    )

class HeyMacCmdJoinDrop(HeyMacCmdJoin):
    MID = HeyMacCmdJoin.MID_DROP
    __hdr__ = (
        ('_cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmd.CID_JOIN),
        ('mid', 'B', HeyMacCmdJoin.MID_DROP),
    )


for cls in HeyMacCmdJoin.__subclasses__():
    HeyMacCmdJoin.set_subclass(cls.MID, cls)
