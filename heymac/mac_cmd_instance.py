"""
Copyright 2020 Dean Hall.  See LICENSE file for details.
"""

from .mac_cmds import \
    HeyMacCmd, \
    HeyMacCmdInvalid, \
    HeyMacCmdSbcn, \
    HeyMacCmdEbcn, \
    HeyMacCmdTxt, \
    HeyMacCmdCbcn
from .mac_cmd_join import HeyMacCmdJoin


# The order of this LUT must match HeyMacCmd.CID*
_CMD_CLASS_LUT = (
    HeyMacCmdInvalid,   # INVALID = 0
    HeyMacCmdSbcn,
    HeyMacCmdEbcn,
    HeyMacCmdTxt,
    HeyMacCmdCbcn,
    HeyMacCmdJoin,  # JOIN = 5
)


def HeyMacCmdInstance(mac_payld):
    """Returns an instance of one of the HeyMacCmd classes
    based on the command id (within the first byte of mac_payld).
    """
    cmd_id = mac_payld[0] & HeyMacCmd.CMD_MASK
    return _CMD_CLASS_LUT[cmd_id](mac_payld)
