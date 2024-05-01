"""
Copyright 2020 Dean Hall.  See LICENSE for details.
"""

from enum import IntFlag    # Python 3.6


class NodeCaps(IntFlag):
    """Radio node capabilities used in the Heymac beacon"""
    NONE = 0
    ALWAYS_RX = 1 << 0      # Leaves radio receiver on by default
    ROOT_ABLE = 1 << 1      # Has resources to be a Root
    INET_BRIDGE = 1 << 2    # Can bridge traffic to the public internet
    GPS_PPS_SOURCE = 1 << 3 # Has GPS/PPS signal


class NodeStatus(IntFlag):
    """Radio node status used in the Heymac beacon"""
    NONE = 0
    CHILD_SLOTS_FULL = 1 << 0   # Has no child slots remaining
    TRANSITORY = 1 << 1         # Is transitory (will not accept parent requests)
