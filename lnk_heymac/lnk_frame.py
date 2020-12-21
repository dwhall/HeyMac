"""
Copyright 2020 Dean Hall.  See LICENSE file for details.

Link-layer Heymac frame parsing, building and serializing.
"""


class HeymacFrameError(Exception):
    pass


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
    # PID values (combine bit-wise)
    PID_IDENT_HEYMAC = 0b11100000
    PID_TYPE_TDMA = 0b00000000
    PID_TYPE_CSMA = 0b00000100

    # Frame Control (Fctl) subfields
    FCTL_X = 0b10000000     # eXtended frame (none of the other bits apply)
    FCTL_L = 0b01000000     # Long addressing
    FCTL_N = 0b00100000     # NetId present
    FCTL_D = 0b00010000     # DstAddr present
    FCTL_I = 0b00001000     # IEs present
    FCTL_S = 0b00000100     # SrcAddr present
    FCTL_M = 0b00000010     # Multihop fields present
    FCTL_P = 0b00000001     # Pending frame follows

    # Frame field names
    FLD_PID = "pid"         # Protocol ID
    FLD_FCTL = "fctl"       # Frame Control
    FLD_NETID = "netid"     # Net ID
    FLD_DADDR = "daddr"     # Destination adddress
    FLD_IES = "ies"         # Information Elements
    FLD_SADDR = "saddr"     # Source address
    FLD_PAYLD = "payld"     # Payload (link layer)
    FLD_MIC = "mic"         # Message Integrity Code
    FLD_HOPS = "hops"       # Hops remaining
    FLD_TADDR = "taddr"     # (re)Transmitter address


    def __init__(self, pid, fctl):
        """Creates a HeymacFrame starting with the given PID and Fctl."""
        # Validate arguments
        if (pid & HeymacFrame._PID_IDENT_MASK) != HeymacFrame.PID_IDENT_HEYMAC:
            raise HeymacFrameError("PID field is not Heymac")
        if (pid & HeymacFrame._PID_TYPE_MASK) not in \
                (HeymacFrame.PID_TYPE_TDMA, HeymacFrame.PID_TYPE_CSMA):
            raise HeymacFrameError("Heymac protocol type not supported")

        self.field = {}
        self.field[HeymacFrame.FLD_PID] = pid
        self.field[HeymacFrame.FLD_FCTL] = fctl


    def __bytes__(self,):
        """Returns the HeymacFrame serialized into a bytes object.

        Raises a HeymacFrameError if some bits and fields
        are not set properly.
        """
        self._validate_fctl_and_fields()

        frame = bytearray()
        frame.append(self.field[HeymacFrame.FLD_PID])
        frame.append(self.field[HeymacFrame.FLD_FCTL])

        if self.is_extended():
            if HeymacFrame.FLD_PAYLD in self.field:
                frame.extend(self.field[HeymacFrame.FLD_PAYLD])
        else:
            if self.is_netid_present():
                frame.extend(self.field[HeymacFrame.FLD_NETID])
            if self.is_daddr_present():
                frame.extend(self.field[HeymacFrame.FLD_DADDR])
            # TODO: add IEs
            if self.is_saddr_present():
                frame.extend(self.field[HeymacFrame.FLD_SADDR])
            if HeymacFrame.FLD_PAYLD in self.field:
                frame.extend(self.field[HeymacFrame.FLD_PAYLD])
            # TODO: add MICs
            if self.is_mhop():
                frame.append(self.field[HeymacFrame.FLD_HOPS])
                frame.extend(self.field[HeymacFrame.FLD_TADDR])

        if len(frame) > 256:
            raise HeymacFrameError("Serialized frame is too large.")
        return bytes(frame)


    @staticmethod
    def parse(frame_bytes):
        """Parses the given frame_bytes and returns a HeymacFrame.

        Raises a HeymacFrameError if some bits and fields
        are not set properly.
        """
        assert 0 <= max(frame_bytes) <= 255, \
            "frame_bytes must be a sequence of bytes"

        if len(frame_bytes) < 2:
            raise HeymacFrameError("Frame must be 2 or more bytes in length")
        pid = frame_bytes[0]
        fctl = frame_bytes[1]
        frame = HeymacFrame(pid, fctl)
        addr_sz = frame._get_addr_sz()
        offset = 2

        # Format of Extended frame is not defined by Heymac
        # so everything after PID, Fctl is payload
        if frame.is_extended():
            frame.set_field(HeymacFrame.FLD_PAYLD, frame_bytes[offset:])
            offset = len(frame_bytes)

        # Parse a regular Heymac frame
        else:
            if frame.is_netid_present():
                frame.set_field(
                    HeymacFrame.FLD_NETID,
                    frame_bytes[offset:offset + 2])
                offset += 2

            if frame.is_daddr_present():
                frame.set_field(
                    HeymacFrame.FLD_DADDR,
                    frame_bytes[offset:offset + addr_sz])
                offset += addr_sz

            # TODO: parse IEs

            if frame.is_saddr_present():
                frame.set_field(
                    HeymacFrame.FLD_SADDR,
                    frame_bytes[offset:offset + addr_sz])
                offset += addr_sz

            # Determine the size of the items at the tail
            # of the frame in order to parse the payload
            # TODO: determine MIC size from IEs
            mic_sz = 0

            if frame.is_mhop():
                mhop_sz = 1 + addr_sz
            else:
                mhop_sz = 0

            payld_sz = len(frame_bytes) - offset - mic_sz - mhop_sz
            assert payld_sz >= 0
            if payld_sz > 0:
                frame.set_field(
                    HeymacFrame.FLD_PAYLD,
                    frame_bytes[offset:offset + payld_sz])
                offset += payld_sz

            # TODO: parse MIC

            if frame.is_mhop():
                frame.set_field(HeymacFrame.FLD_HOPS, frame_bytes[offset])
                offset += 1
                frame.set_field(
                    HeymacFrame.FLD_PAYLD,
                    frame_bytes[offset:offset + addr_sz])
                offset += addr_sz

        # Expected the amount parsed to match the frame size
        assert offset == len(frame_bytes)

        frame._validate_fctl_and_fields()
        return frame


    def get_field(self, fld_nm):
        """Returns the field value if it is present.
        Returns None if the field is not present.
        """
        assert fld_nm in (
            HeymacFrame.FLD_PID,
            HeymacFrame.FLD_FCTL,
            HeymacFrame.FLD_NETID,
            HeymacFrame.FLD_DADDR,
            # HeymacFrame.FLD_IES,   # IEs are not yet supported
            HeymacFrame.FLD_SADDR,
            HeymacFrame.FLD_PAYLD,
            # HeymacFrame.FLD_MIC,   # MICs are not yet supported
            HeymacFrame.FLD_HOPS,
            HeymacFrame.FLD_TADDR,
        )
        return self.field.get(fld_nm, None)


    def is_heymac(self,):
        """Returns True if the PID Ident subfield indicates Heymac protocol.
        Note, this only checks the first four bits and does not check
        the rest of the frame for validity.
        """
        return (self.field[HeymacFrame.FLD_PID] & HeymacFrame._PID_IDENT_MASK
                == HeymacFrame.PID_IDENT_HEYMAC)

    def is_extended(self,):
        return 0 != (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_X)

    def is_long_addrs(self,):
        return (0 == (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_X)
            and 0 != (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_L))

    def is_netid_present(self,):
        return (0 == (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_X)
            and 0 != (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_N))

    def is_daddr_present(self,):
        return (0 == (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_X)
            and 0 != (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_D))

    def is_ies_present(self,):
        return (0 == (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_X)
            and 0 != (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_I))

    def is_saddr_present(self,):
        return (0 == (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_X)
            and 0 != (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_S))

    def is_mhop(self,):
        return (0 == (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_X)
            and 0 != (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_M))

    def is_pending_set(self,):
        return (0 == (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_X)
            and 0 != (self.field[HeymacFrame.FLD_FCTL] & HeymacFrame.FCTL_P))


    def set_field(self, fld_nm, value):
        """Stores the field value
        """
        assert fld_nm in (
            # HeymacFrame.FLD_PID,   # Can only set this in the constructor
            # HeymacFrame.FLD_FCTL,  # Can only set this in the constructor
            HeymacFrame.FLD_NETID,
            HeymacFrame.FLD_DADDR,
            # HeymacFrame.FLD_IES,   # IEs are not yet supported
            HeymacFrame.FLD_SADDR,
            HeymacFrame.FLD_PAYLD,
            # HeymacFrame.FLD_MIC,   # MICs are not yet supported
            HeymacFrame.FLD_HOPS,
            HeymacFrame.FLD_TADDR,
        ), "Field '{}' cannot be set by set_field()".format(fld_nm)

        # Validate address field is of the correct size
        if fld_nm in (
            HeymacFrame.FLD_DADDR,
            HeymacFrame.FLD_SADDR,
            HeymacFrame.FLD_TADDR,
        ):
            assert len(value) == self._get_addr_sz()

        # Validate the Fctl bit is set for the given field
        if fld_nm == HeymacFrame.FLD_NETID:
            assert self.is_netid_present()
        elif fld_nm == HeymacFrame.FLD_DADDR:
            assert self.is_daddr_present()
        elif fld_nm == HeymacFrame.FLD_IES:
            assert self.is_ies_present()
        elif fld_nm == HeymacFrame.FLD_SADDR:
            assert self.is_saddr_present()
        elif fld_nm == HeymacFrame.FLD_HOPS:
            assert self.is_mhop()
        elif fld_nm == HeymacFrame.FLD_TADDR:
            assert self.is_mhop()

        # Store the field
        self.field[fld_nm] = value


# Private


    # PID masks
    _PID_IDENT_MASK = 0b11110000
    _PID_TYPE_MASK = 0b00001111

    # TODO: verify CSMA version
    # _SUPPORTED_CSMA_VRSNS = (0,)


    def _get_addr_sz(self,):
        return (2, 8)[self.is_long_addrs()]

    def _validate_fctl_and_fields(self,):
        """Validates this HeymacFrame

        Always returns None.  Raises a HeymacFrameError if
        Fctl bits indicate a field is needed, but it's not present;
        or a field is present, but the Fctl bit is not set.
        """
        err_msg = None
        if not err_msg and HeymacFrame.FLD_PID not in self.field:
            err_msg = "PID value is missing"
        if not err_msg and HeymacFrame.FLD_FCTL not in self.field:
            err_msg = "Fctl value is missing"

        # Check that if the bit is set in Fctl,
        # the data field exists and vice versa
        if not err_msg:
            fctl = self.field[HeymacFrame.FLD_FCTL]
            for bit, field_nm in (
                    (HeymacFrame.FCTL_N, HeymacFrame.FLD_NETID),
                    (HeymacFrame.FCTL_D, HeymacFrame.FLD_DADDR),
                    # (HeymacFrame.FCTL_I, HeymacFrame.FLD_IES), # TODO: IEs
                    (HeymacFrame.FCTL_S, HeymacFrame.FLD_SADDR),
                    (HeymacFrame.FCTL_M, HeymacFrame.FLD_HOPS),
                    (HeymacFrame.FCTL_M, HeymacFrame.FLD_TADDR),):
                if (bit & fctl and field_nm not in self.field) or \
                   ((bit & fctl) == 0 and field_nm in self.field):
                    err_msg = "Fctl bit/value missing for Fctl bit 0x{:x} " \
                              "and field '{}'".format(bit, field_nm)
                    break

        # Special cases
        # If FCTL_L is set, at least one address field must exist
        if not err_msg and (HeymacFrame.FCTL_L & fctl
                and HeymacFrame.FLD_DADDR not in self.field
                and HeymacFrame.FLD_SADDR not in self.field
                and HeymacFrame.FLD_TADDR not in self.field):
            err_msg = "Long address selected, but no address field is present"

        # If FCTL_X is set, only the payload should exist
        if not err_msg and HeymacFrame.FCTL_X & fctl:
            for field_nm in (HeymacFrame.FLD_NETID,
                             HeymacFrame.FLD_DADDR,
                             HeymacFrame.FLD_IES,
                             HeymacFrame.FLD_SADDR,
                             HeymacFrame.FLD_MIC,
                             HeymacFrame.FLD_HOPS,
                             HeymacFrame.FLD_TADDR,):
                if field_nm in self.field:
                    err_msg = "Extended frame has field other than {}" \
                              .format(HeymacFrame.FLD_PAYLD)
                    break
        if err_msg:
            raise HeymacFrameError(err_msg)
