#
# HeyMacCmdProtocol: [cmd, pid, mid, data... ]
#   cmd = 5 (HeyMacCmdId.PROTO)
#   Protocol ID
#   Message ID
#
"""
==========  ======  ======  ==========
pid         mid     dir     data
----------  ------  ------  ----------
NetJoin     Rqst    >       NetID
            Accpt   <       AddrShort
            Ntfy    >       AddrLong, AddrShort
            Rjct    <       RjctCode

NetLeave    Ntfy    <>      AddrLong, AddrShort

Link        Lost    <
            Status  <       data?   // belongs in bcn?

Mauth?      1,2,3
==========  ======  ======  ==========

Where:
    Dir     <   Toward leaves
            >   Toward root
"""

class DllMgr(object):
    """
    """
    def __init__(self,):
        self._protocol_convos = {}  # {key:ngbrAddr, val:protocolInstance}


    def proc_mac_cmd(self, mac_cmd):
        """Process the HeyMac command if it is
        of a type that applies to the DLL.
        """
        pass


    def proc_mac_cmd_proto(self, mac_cmd):
        """Process the mac_cmd as a HeyMacCmdProtocol
        """
        pass
