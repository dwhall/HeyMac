#!/usr/bin/env python
"""
Copyright 2020 Dean Hall.  See LICENSE file for details.

Link-layer Heymac frame parsing, building and serializing.
"""

class HeymacFrame(object):
    """Heymac frame definition
    [PID,Fctl,NetId,DstAddr,IEs,SrcAddr,Payld,MIC,Hops,TxAddr]

    PID := Protocol ID

    =========   ======================================
    Bitfield    Description
    =========   ======================================
    XXXX ....   PID ident
    .... XXXX   PID type
    ---------   --------------------------------------
    1110 00vv   Heymac TDMA, (vv)ersion
    1110 01vv   Heymac CSMA, (vv)ersion
    1110 1xxx   Heymac (RFU: Flood, Extended, etc.)
    =========   ======================================

    Fctl := Frame Control

    =========   ======================================
    Bitfield    Description
    =========   ======================================
    10000000    X: eXtended frame
    01000000    L: Long addressing
    00100000    N: NetId present
    00010000    D: DstAddr present
    00001000    I: IEs present
    00000100    S: SrcAddr present
    00000010    M: Multihop fields present
    00000001    P: Pending frame follows
    =========   ======================================

    There are two ways to use this class:
    to build a HeymacFrame object by setting fields
    and to parse a sequence of bytes yielding HeymacFrame object.

    To build a Heymac frame, create an instance and then set fields.
    Here is an example::

        frame = HeymacFrame(
            HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
            HeymacFrame.FCTL_D | HeymacFrame.FCTL_S)
        frame.set_field(HeymacFrame.FLD_SADDR) = b"\x35\x16"
        frame.set_field(HeymacFrame.FLD_DADDR) = b"\x01\xE3"
        frame.set_field(HeymacFrame.FLD_PAYLD) = my_data
        phy_payld = bytes(frame)

    To parse a Heymac frame, call the static parse() method::

        frame = HeymacFrame.parse(phy_payld)
        # TODO: show use of frame.get_field()

    When working with field values, the data type is
    either a number 0..255 for single-byte fields
    or a bytearray() or bytes() object for multi-byte fields.
    Multi-byte fields MUST be in Network Order (big-endian).
    """
    # PID masks
    PID_IDENT_MASK = 0b11110000
    PID_TYPE_MASK = 0b00001111
    # PID values
    PID_IDENT_HEYMAC = 0b11100000
    PID_TYPE_TDMA = 0b00000000
    PID_TYPE_CSMA = 0b00000100

    SUPPORTED_CSMA_VRSNS = (0,)

    # Frame Control (Fctl) subfields
    FCTL_X = 0b10000000 # eXtended frame (none of the other bits apply)
    FCTL_L = 0b01000000 # Long addressing
    FCTL_N = 0b00100000 # NetId present
    FCTL_D = 0b00010000 # DstAddr present
    FCTL_I = 0b00001000 # IEs present
    FCTL_S = 0b00000100 # SrcAddr present
    FCTL_M = 0b00000010 # Multihop fields present
    FCTL_P = 0b00000001 # Pending frame follows

    # Frame field names
    FLD_PID = "pid"     # Protocol ID
    FLD_FCTL = "fctl"   # Frame Control
    FLD_NETID = "netid" # Net ID
    FLD_DADDR = "daddr" # Destination adddress
    FLD_IES = "ies"     # Information Elements
    FLD_SADDR = "saddr" # Source address
    FLD_PAYLD = "payld" # Payload (link layer)
    FLD_MIC = "mic"     # Message Integrity Code
    FLD_HOPS = "hops"   # Hops remaining
    FLD_TADDR = "taddr" # (re)Transmitter address


    def __init__(self, pid, fctl):
        """Creates a HeymacFrame starting from
        the given pid and fctl fields
        """
        # Validate arguments
        assert (pid & HeymacFrame.PID_IDENT_MASK) == HeymacFrame.PID_IDENT_HEYMAC, "PID field is not Heymac"
        assert (pid & HeymacFrame.PID_TYPE_MASK) in (HeymacFrame.PID_TYPE_TDMA, HeymacFrame.PID_TYPE_CSMA), "Heymac protocol type not supported"
        self.field = {}
        self.field["pid"] = pid
        self.field["fctl"] = fctl


#### Public interface

    def __bytes__(self,):
        """Returns the HeymacFrame serialized into a bytes object
        """
        # Convert Fctl bits to friendly names
        fctl = self.field["fctl"]
        is_extended = (fctl & HeymacFrame.FCTL_X) != 0
        netid_present = (fctl & HeymacFrame.FCTL_N) != 0
        daddr_present = (fctl & HeymacFrame.FCTL_D) != 0
        ies_present = (fctl & HeymacFrame.FCTL_I) != 0
        saddr_present = (fctl & HeymacFrame.FCTL_S) != 0
        is_mhop = (fctl & HeymacFrame.FCTL_M) != 0
        has_pending = (fctl & HeymacFrame.FCTL_P) != 0

        frame = bytearray()
        frame.append(self.field["pid"])
        frame.append(self.field["fctl"])

        if is_extended:
            if "payld" in self.field: frame.extend(self.field["payld"])
        else:
            if netid_present: frame.extend(self.field["netid"])
            if daddr_present: frame.extend(self.field["daddr"])
            # TODO: add IEs
            if saddr_present: frame.extend(self.field["saddr"])
            if "payld" in self.field: frame.extend(self.field["payld"])
            # TODO: add MICs
            if is_mhop:
                frame.append(self.field["hops"])
                frame.extend(self.field["taddr"])

        assert len(frame) <= 256
        return bytes(frame)


    @staticmethod
    def parse(frame_bytes):
        """Parses the given frame_bytes and returns a HeymacFrame
        """
        assert 0 <= max(frame_bytes) <= 255, "frame_bytes must be a sequence of bytes"
        pid = frame_bytes[0]
        fctl = frame_bytes[1]
        frame = HeymacFrame(pid, fctl)
        offset = 2

        # Convert Fctl bits to friendly names
        is_extended = (fctl & HeymacFrame.FCTL_X) != 0
        long_addrs = (fctl & HeymacFrame.FCTL_L) != 0
        netid_present = (fctl & HeymacFrame.FCTL_N) != 0
        daddr_present = (fctl & HeymacFrame.FCTL_D) != 0
        ies_present = (fctl & HeymacFrame.FCTL_I) != 0
        saddr_present = (fctl & HeymacFrame.FCTL_S) != 0
        is_mhop = (fctl & HeymacFrame.FCTL_M) != 0
        has_pending = (fctl & HeymacFrame.FCTL_P) != 0
        if long_addrs:
            addr_sz = 8
        else:
            addr_sz = 2

        # Format of Extended frame is not defined by Heymac
        # so everything after PID, Fctl is payload
        if is_extended:
            frame.set_field(HeymacFrame.FLD_PAYLD, frame_bytes[offset:])
            offset = len(frame)

        # Parse a regular Heymac frame
        else:
            if netid_present:
                frame.set_field(HeymacFrame.FLD_NETID, frame_bytes[offset:offset + 2])
                offset += 2

            if daddr_present:
                frame.set_field(HeymacFrame.FLD_DADDR, frame_bytes[offset:offset + addr_sz])
                offset += addr_sz

            # TODO: parse IEs

            if saddr_present:
                frame.set_field(HeymacFrame.FLD_SADDR, frame_bytes[offset:offset + addr_sz])
                offset += addr_sz

            # Determine the size of the items at the tail
            # of the frame in order to parse the payload
            # TODO: determine MIC size from IEs
            mic_sz = 0

            if is_mhop:
                mhop_sz = 1 + addr_sz
            else:
                mhop_sz = 0

            paylod_sz = len(frame_bytes) - offset - mic_sz - mhop_sz
            frame.set_field(HeymacFrame.FLD_PAYLD, frame_bytes[offset:offset + paylod_sz])
            offset += paylod_sz

            # TODO: parse MIC

            if is_mhop:
                frame.set_field(HeymacFrame.FLD_HOPS, frame_bytes[offset])
                offset += 1
                frame.set_field(HeymacFrame.FLD_PAYLD, frame_bytes[offset:offset + addr_sz])
                offset += addr_sz

        # Amount parsed must match the frame size
        assert offset == len(frame_bytes)
        return frame


    def get_field(self, fld_nm):
        """Returns the field value.
        If the field is not present,
        returns b"" for single-byte fields
        and b"" for multi-byte fields
        """
        assert fld_nm in (
            HeymacFrame.FLD_PID,
            HeymacFrame.FLD_FCTL,
            HeymacFrame.FLD_NETID,
            HeymacFrame.FLD_DADDR,
            #HeymacFrame.FLD_IES,   # IEs are not yet supported
            HeymacFrame.FLD_SADDR,
            HeymacFrame.FLD_PAYLD,
            #HeymacFrame.FLD_MIC,   # MICs are not yet supported
            HeymacFrame.FLD_HOPS,
            HeymacFrame.FLD_TADDR,
        )
        return self.field.get(fld_nm, b"")


    def is_heymac(self,):
        """Returns True if the PID Ident subfield indicates Heymac protocol.
        Note, this only checks the first four bytes and does not check
        the rest of the frame for validity.
        """
        return self.field[HeymacFrame.FLD_PID] & HeymacFrame.PID_IDENT_MASK == HeymacFrame.PID_IDENT_HEYMAC


    def set_field(self, fld_nm, value):
        """Stores the field value
        """
        assert fld_nm in (
            #HeymacFrame.FLD_PID,   # Can only set this in the constructor
            #HeymacFrame.FLD_FCTL,  # Can only set this in the constructor
            HeymacFrame.FLD_NETID,
            HeymacFrame.FLD_DADDR,
            #HeymacFrame.FLD_IES,   # IEs are not yet supported
            HeymacFrame.FLD_SADDR,
            HeymacFrame.FLD_PAYLD,
            #HeymacFrame.FLD_MIC,   # MICs are not yet supported
            HeymacFrame.FLD_HOPS,
            HeymacFrame.FLD_TADDR,
        )

        # Convert Fctl bits to friendly names
        fctl = self.field["fctl"]
        is_extended = (fctl & HeymacFrame.FCTL_X) != 0
        long_addrs = (fctl & HeymacFrame.FCTL_L) != 0
        netid_present = (fctl & HeymacFrame.FCTL_N) != 0
        daddr_present = (fctl & HeymacFrame.FCTL_D) != 0
        ies_present = (fctl & HeymacFrame.FCTL_I) != 0
        saddr_present = (fctl & HeymacFrame.FCTL_S) != 0
        is_mhop = (fctl & HeymacFrame.FCTL_M) != 0
        has_pending = (fctl & HeymacFrame.FCTL_P) != 0
        if long_addrs:
            addr_sz = 8
        else:
            addr_sz = 2

        # Validate address field is of the correct size
        if fld_nm in (
            HeymacFrame.FLD_DADDR,
            HeymacFrame.FLD_SADDR,
            HeymacFrame.FLD_TADDR,
        ):
            assert len(value) == addr_sz

        # Validate the Fctl bit is set for the given field
        if fld_nm == HeymacFrame.FLD_NETID: assert netid_present
        elif fld_nm == HeymacFrame.FLD_DADDR: assert daddr_present
        elif fld_nm == HeymacFrame.FLD_IES: assert ies_present
        elif fld_nm == HeymacFrame.FLD_SADDR: assert saddr_present
        elif fld_nm == HeymacFrame.FLD_HOPS: assert is_mhop
        elif fld_nm == HeymacFrame.FLD_TADDR: assert is_mhop

        # Store the field
        self.field[fld_nm] = value
