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
        frame.saddr = b"\x35\x16"
        frame.daddr = b"\x01\xE3"
        frame.payld = my_data
        phy_payld = bytes(frame)

    To parse a Heymac frame, call the static parse() method::

        frame = HeymacFrame.parse(phy_payld)
        # TODO: demo frame properties

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


    def __init__(self, pid, fctl):
        """Creates a HeymacFrame starting with the given PID and Fctl."""
        # Validate arguments
        if (pid & HeymacFrame._PID_IDENT_MASK) != HeymacFrame.PID_IDENT_HEYMAC:
            raise HeymacFrameError("PID field is not Heymac")
        if (pid & HeymacFrame._PID_TYPE_MASK) not in \
                (HeymacFrame.PID_TYPE_TDMA, HeymacFrame.PID_TYPE_CSMA):
            raise HeymacFrameError("Heymac protocol type not supported")

        self._pid = pid
        self._fctl = fctl
        self._netid = None
        self._daddr = None
        self._ies = None
        self._saddr = None
        self._payld = None
        self._mic = None
        self._hops = None
        self._taddr = None


    def __bytes__(self):
        """Returns the HeymacFrame serialized into a bytes object.

        Raises a HeymacFrameError if some bits and fields
        are not set properly.
        """
        self._validate_fctl_and_fields()

        frame = bytearray()
        frame.append(self._pid)
        frame.append(self._fctl)

        if self.is_extended():
            if self._payld:
                frame.extend(self._payld)
        else:
            if self.is_netid_present():
                frame.extend(self._netid)
            if self.is_daddr_present():
                frame.extend(self._daddr)
            # TODO: add IEs
            if self.is_saddr_present():
                frame.extend(self._saddr)
            if self._payld:
                frame.extend(self._payld)
            # TODO: add MICs
            if self.is_mhop():
                frame.append(self._hops)
                frame.extend(self._taddr)

        if len(frame) > 256:
            raise HeymacFrameError("Serialized frame is too large.")
        return bytes(frame)


    @staticmethod
    def parse(frame_bytes):
        """Parses the given frame_bytes and returns a HeymacFrame.

        Raises a HeymacFrameError if some bits and fields
        are not set properly.
        """
        if max(frame_bytes) > 255 or min(frame_bytes) < 0:
            raise HeymacFrameError("frame_bytes must be a sequence of bytes")

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
            frame.payld = frame_bytes[offset:]
            offset = len(frame_bytes)

        # Parse a regular Heymac frame
        else:
            if frame.is_netid_present():
                frame.netid = frame_bytes[offset:offset + 2]
                offset += 2

            if frame.is_daddr_present():
                frame.daddr = frame_bytes[offset:offset + addr_sz]
                offset += addr_sz

            # TODO: parse IEs

            if frame.is_saddr_present():
                frame.saddr = frame_bytes[offset:offset + addr_sz]
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
            if payld_sz > 0:
                frame.payld = frame_bytes[offset:offset + payld_sz]
                offset += payld_sz
            elif payld_sz < 0:
                raise HeymacFrameError("Insufficient bytes")

            # TODO: parse MIC

            if frame.is_mhop():
                frame.hops = frame_bytes[offset]
                offset += 1
                frame.taddr = frame_bytes[offset:offset + addr_sz]
                offset += addr_sz

        # Expected the amount parsed to match the frame size
        if offset != len(frame_bytes):
            raise HeymacFrameError("Incorrect byte length")

        frame._validate_fctl_and_fields()
        return frame


    def get_sender(self):
        """Returns the sender of the frame (source or re-transmitter)."""
        if self.is_mhop():
            sender = self._taddr
        else:
            sender = self._saddr
        return sender


    def is_heymac(self):
        """Returns True if the PID Ident subfield indicates Heymac protocol.
        Note, this only checks the first four bits and does not check
        the rest of the frame for validity.
        """
        return (self._pid & HeymacFrame._PID_IDENT_MASK
                == HeymacFrame.PID_IDENT_HEYMAC)

    def is_extended(self):
        return 0 != (self._fctl & HeymacFrame.FCTL_X)

    def is_long_addrs(self):
        return 0 == (self._fctl & HeymacFrame.FCTL_X) \
            and 0 != (self._fctl & HeymacFrame.FCTL_L)

    def is_netid_present(self):
        return 0 == (self._fctl & HeymacFrame.FCTL_X) \
            and 0 != (self._fctl & HeymacFrame.FCTL_N)

    def is_daddr_present(self):
        return 0 == (self._fctl & HeymacFrame.FCTL_X) \
            and 0 != (self._fctl & HeymacFrame.FCTL_D)

    def is_ies_present(self):
        return 0 == (self._fctl & HeymacFrame.FCTL_X) \
            and 0 != (self._fctl & HeymacFrame.FCTL_I)

    def is_saddr_present(self):
        return 0 == (self._fctl & HeymacFrame.FCTL_X) \
            and 0 != (self._fctl & HeymacFrame.FCTL_S)

    def is_mhop(self):
        return 0 == (self._fctl & HeymacFrame.FCTL_X) \
            and 0 != (self._fctl & HeymacFrame.FCTL_M)

    def is_pending_set(self):
        return 0 == (self._fctl & HeymacFrame.FCTL_X) \
            and 0 != (self._fctl & HeymacFrame.FCTL_P)

    @property
    def pid(self):
        return self._pid

    @property
    def fctl(self):
        return self._fctl

    @property
    def netid(self):
        return self._netid

    @netid.setter
    def netid(self, val):
        self._netid = val

    @property
    def daddr(self):
        return self._daddr

    @daddr.setter
    def daddr(self, val):
        assert len(val) == self._get_addr_sz()
        self._daddr = val

    @property
    def saddr(self):
        return self._saddr

    @saddr.setter
    def saddr(self, val):
        assert len(val) == self._get_addr_sz()
        self._saddr = val

    @property
    def payld(self):
        return self._payld

    @payld.setter
    def payld(self, val):
        self._payld = val

    @property
    def hops(self):
        return self._hops

    @hops.setter
    def hops(self, val):
        assert self.is_mhop()
        self._hops = val

    @property
    def taddr(self):
        return self._taddr

    @taddr.setter
    def taddr(self, val):
        assert len(val) == self._get_addr_sz()
        assert self.is_mhop()
        self._taddr = val


# Private


    # PID masks
    _PID_IDENT_MASK = 0b11110000
    _PID_TYPE_MASK = 0b00001111

    # TODO: verify CSMA version
    # _SUPPORTED_CSMA_VRSNS = (0,)


    def _get_addr_sz(self):
        return (2, 8)[self.is_long_addrs()]

    def _validate_fctl_and_fields(self):
        """Validates this HeymacFrame

        Always returns None.  Raises a HeymacFrameError if
        Fctl bits indicate a field is needed, but it's not present;
        or a field is present, but the Fctl bit is not set.
        """
        FIELD_INFO = (
            (HeymacFrame.FCTL_N, self._netid, "netid"),
            (HeymacFrame.FCTL_D, self._daddr, "daddr"),
            (HeymacFrame.FCTL_I, self._ies, "ies"),
            (HeymacFrame.FCTL_S, self._saddr, "saddr"),
            (HeymacFrame.FCTL_M, self._hops, "hops"),
            (HeymacFrame.FCTL_M, self._taddr, "taddr"),
        )

        err_msg = None
        if not err_msg and self._pid is None:
            err_msg = "PID value is missing"
        if not err_msg and self._fctl is None:
            err_msg = "Fctl value is missing"

        # Check that if the bit is set in Fctl,
        # the data field exists and vice versa
        if not err_msg:
            fctl = self._fctl
            for bit, field, field_nm in FIELD_INFO:
                if (bit & fctl and not field) or ((bit & fctl) == 0 and field):
                    err_msg = "Fctl bit/value missing for Fctl bit 0x{:x} " \
                              "and field '{}'".format(bit, field_nm)
                    break

        # If FCTL_L is set, at least one address field must exist
        if not err_msg and (
                HeymacFrame.FCTL_L & fctl
                and not self._daddr
                and not self._saddr
                and not self._taddr):
            err_msg = "Long address selected, but no address field is present"

        # If FCTL_X is set, only the payload should exist
        if not err_msg and HeymacFrame.FCTL_X & fctl:
            for _, field, field_nm in FIELD_INFO:
                if field:
                    err_msg = "Extended frame has field other than {}" \
                              .format(field_nm)
                    break

        if err_msg:
            raise HeymacFrameError(err_msg)
