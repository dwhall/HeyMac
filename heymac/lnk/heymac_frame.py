"""
Copyright 2020 Dean Hall.  See LICENSE file for details.

Link-layer Heymac frame parsing, building and serializing.
"""

import enum
import struct

from heymac.lnk.heymac_cmd import HeymacCmd
from heymac.net.apv6_pkt import APv6Packet


class HeymacFrameError(Exception):
    pass


class HeymacFrameFctl(enum.IntFlag):
    """HeymacFrame frame control (Fctl) field bit flag (bitwise combos)"""
    NO_FLAGS = 0
    X = 0b10000000     # eXtended frame (none of the other bits apply)
    L = 0b01000000     # Long addressing
    N = 0b00100000     # NetId present
    D = 0b00010000     # DstAddr present
    I = 0b00001000     # IEs present
    S = 0b00000100     # SrcAddr present
    M = 0b00000010     # Multihop fields present
    P = 0b00000001     # Pending frame follows


class HeymacFramePid(enum.IntFlag):
    """The first byte of the HeymacFrame is the protocol identifier, PID."""
    pass

class HeymacFramePidIdent(HeymacFramePid):
    """The upper nibble of the PID identifies the Heymac protocol."""
    MASK = 0b11110000
    HEYMAC = 0b11100000

class HeymacFramePidType(HeymacFramePid):
    """The lower nibble of the PID identifies PHY attributes and versioning."""
    MASK = 0b00001111
    TDMA = 0b00000000
    CSMA = 0b00000100


class HeymacFrame(object):
    """Heymac frame definition
    [PID,Fctl,NetId,DstAddr,IEs,SrcAddr,Payld,MIC,Hops,TxAddr]

    PID := Protocol ID

    =========   ======================================
    Bitfield    Description
    =========   ======================================
    1110 ....   PID ident
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

        frame = HeymacFrame(HeymacFramePidType.CSMA)
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

    MAX_LEN = 256       # Maximum frame length
    MIN_LEN = 2         # Minimum frame length

    FIELD_NAMES = (
        "netid", "daddr", "ies", "saddr", "payld", "mic", "hops", "taddr")

    def __init__(self, pid_type, **kwargs):
        """Creates a HeymacFrame starting with the given PID and Fctl."""
        if (pid_type & ~HeymacFramePidType.MASK) != 0:
            raise HeymacFrameError("invalid pid_type value")

        self._pid = HeymacFramePidIdent.HEYMAC | pid_type
        self._fctl = HeymacFrameFctl.NO_FLAGS
        self._netid = None
        self._daddr = None
        self._ie_sqnc = None
        self._saddr = None
        self._payld = None
        self._mic = None
        self._hops = None
        self._taddr = None

        for k, v in kwargs.items():
            if k not in HeymacFrame.FIELD_NAMES:
                raise HeymacFrameError("Invalid field, {}".format(k))
            setattr(self, k, v)

        # TODO: find a way to set the Fctl.P bit

    def __bytes__(self):
        """Returns the HeymacFrame serialized into a bytes object.

        Raises a HeymacFrameError if some bits or fields
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
            if self.is_ies_present():
                frame.extend(self.ies)
            if self.is_saddr_present():
                frame.extend(self._saddr)
            if self._payld:
                if type(self._payld) is not bytes:
                    b = bytes(self._payld)
                else:
                    b = self._payld
                frame.extend(b)
            # TODO: add MICs
            if self.is_mhop():
                frame.append(self._hops)
                frame.extend(self._taddr)

        if len(frame) > HeymacFrame.MAX_LEN:
            raise HeymacFrameError("Serialized frame is too large.")
        return bytes(frame)

    @staticmethod
    def parse(frame_bytes):
        """Parses the given frame_bytes and returns a HeymacFrame.

        Raises a HeymacFrameError if some bits or fields
        are not set properly.
        """
        if max(frame_bytes) > 255 or min(frame_bytes) < 0:
            raise HeymacFrameError("frame_bytes must be a sequence of bytes")
        if len(frame_bytes) < HeymacFrame.MIN_LEN:
            raise HeymacFrameError("Frame must be 2 or more bytes in length")

        pid_ident = frame_bytes[0] & HeymacFramePidIdent.MASK
        if pid_ident != HeymacFramePidIdent.HEYMAC:
            raise HeymacFrameError("Invalid PID ident")

        pid_type = frame_bytes[0] & HeymacFramePidType.MASK
        frame = HeymacFrame(pid_type)

        fctl = frame_bytes[1]
        addr_sz = (2, 8)[(fctl & HeymacFrameFctl.L) != 0]
        offset = 2

        # The format of Extended frame is not defined by Heymac
        # so everything after PID, Fctl is payload
        if fctl & HeymacFrameFctl.X:
            frame.payld = frame_bytes[offset:]
            offset = len(frame_bytes)

        # Parse a regular Heymac frame
        else:
            if fctl & HeymacFrameFctl.N:
                frame.netid = frame_bytes[offset:offset + 2]
                offset += 2

            if fctl & HeymacFrameFctl.D:
                frame.daddr = frame_bytes[offset:offset + addr_sz]
                offset += addr_sz

            if fctl & HeymacFrameFctl.I:
                ies = HeymacIeSequence.parse(frame_bytes, offset)
                frame.ies = ies
                offset += len(ies)

            if fctl & HeymacFrameFctl.S:
                frame.saddr = frame_bytes[offset:offset + addr_sz]
                offset += addr_sz

            # Determine the size of the items at the tail
            # of the frame in order to parse the payload
            # TODO: determine MIC size from IEs
            mic_sz = 0

            if fctl & HeymacFrameFctl.M:
                mhop_sz = 1 + addr_sz
            else:
                mhop_sz = 0

            payld_sz = len(frame_bytes) - offset - mic_sz - mhop_sz
            frame.payld = HeymacFrame._parse_payld(frame_bytes,
                                                   offset,
                                                   payld_sz)
            offset += payld_sz

            # TODO: parse MIC

            if fctl & HeymacFrameFctl.M:
                frame.hops = frame_bytes[offset]
                offset += 1
                frame.taddr = frame_bytes[offset:offset + addr_sz]
                offset += addr_sz

        if offset != len(frame_bytes):
            raise HeymacFrameError("frame_bytes does not make an exact frame")

        frame._validate_fctl_and_fields()
        return frame


    def available_payld_sz(self):
        byte_cnt = 2   # PID + Fctl
        if not self.is_extended():
            if self.is_netid_present():
                byte_cnt += 2
            if self.is_long_addrs():
                addr_len = 8
            else:
                addr_len = 2
            if self.is_daddr_present():
                byte_cnt += addr_len
            if self.is_ies_present():
                byte_cnt += len(self._ie_sqnc)
            if self.is_saddr_present():
                byte_cnt += addr_len
            # TODO: add MICs
            if self.is_mhop():
                byte_cnt += addr_len + 1
        return 255 - byte_cnt


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
        return (self._pid & HeymacFramePidIdent.MASK
                == HeymacFramePidIdent.HEYMAC)

    def is_extended(self):
        return 0 != (self._fctl & HeymacFrameFctl.X)

    def is_long_addrs(self):
        return not self.is_extended() and 0 != (self._fctl & HeymacFrameFctl.L)

    def is_netid_present(self):
        return not self.is_extended() and 0 != (self._fctl & HeymacFrameFctl.N)

    def is_daddr_present(self):
        return not self.is_extended() and 0 != (self._fctl & HeymacFrameFctl.D)

    def is_ies_present(self):
        return not self.is_extended() and 0 != (self._fctl & HeymacFrameFctl.I)

    def is_saddr_present(self):
        return not self.is_extended() and 0 != (self._fctl & HeymacFrameFctl.S)

    def is_mhop(self):
        return not self.is_extended() and 0 != (self._fctl & HeymacFrameFctl.M)

    def is_pending_set(self):
        return not self.is_extended() and 0 != (self._fctl & HeymacFrameFctl.P)

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
        self._fctl |= HeymacFrameFctl.N

    @property
    def daddr(self):
        return self._daddr

    @daddr.setter
    def daddr(self, val):
        self._daddr = val
        self._fctl |= HeymacFrameFctl.D
        if len(val) != 2:
            self._fctl |= HeymacFrameFctl.L

    @property
    def ies(self):
        return bytes(self._ie_sqnc)

    @ies.setter
    def ies(self, val):
        self._ie_sqnc = val
        self._fctl |= HeymacFrameFctl.I

    @property
    def saddr(self):
        return self._saddr

    @saddr.setter
    def saddr(self, val):
        self._saddr = val
        self._fctl |= HeymacFrameFctl.S
        if len(val) != 2:
            self._fctl |= HeymacFrameFctl.L

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
        self._hops = val
        if self._taddr is not None:
            self._fctl |= HeymacFrameFctl.M

    @property
    def taddr(self):
        return self._taddr

    @taddr.setter
    def taddr(self, val):
        self._taddr = val
        if self._hops is not None:
            self._fctl |= HeymacFrameFctl.M


# Private

    # TODO: verify CSMA version
    # _SUPPORTED_CSMA_VRSNS = (0,)


    @staticmethod
    def _parse_payld(frame_bytes, offset, sz):
        """Parses sz number of frame_bytes at the offset as the payload.

        Returns a HeymacCmd object, an APv6Packet object or None
        """
        if sz < 0:
            raise HeymacFrameError("Insufficient bytes")
        payld = None
        if sz > 0:
            first_byte = frame_bytes[offset]
            if ((first_byte & APv6Packet.IPHC_PREFIX_MASK)
                    == APv6Packet.IPHC_PREFIX):
                payld = APv6Packet.parse(frame_bytes[offset:offset + sz])
            elif ((first_byte & HeymacCmd.PREFIX_MASK)
                    == HeymacCmd.PREFIX):
                payld = HeymacCmd.parse(frame_bytes[offset:offset + sz])
            else:
                raise HeymacFrameError("Unknown payload prefix")
        return payld


    def _validate_fctl_and_fields(self):
        """Validates this HeymacFrame

        Always returns None.  Raises a HeymacFrameError if
        Fctl bits indicate a field is needed, but it's not present;
        or a field is present, but the Fctl bit is not set.
        """
        FIELD_INFO = ((HeymacFrameFctl.N, self._netid, "netid"),
                      (HeymacFrameFctl.D, self._daddr, "daddr"),
                      (HeymacFrameFctl.I, self._ie_sqnc, "ies"),
                      (HeymacFrameFctl.S, self._saddr, "saddr"),
                      (HeymacFrameFctl.M, self._hops, "hops"),
                      (HeymacFrameFctl.M, self._taddr, "taddr"))

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
        if not err_msg and (HeymacFrameFctl.L & fctl
                            and not self._daddr
                            and not self._saddr
                            and not self._taddr):
            err_msg = "Long address selected, but no address field is present"

        # If FCTL_X is set, only the payload should exist
        if not err_msg and HeymacFrameFctl.X & fctl:
            for _, field, field_nm in FIELD_INFO:
                if field:
                    err_msg = "Extended frame has field other than {}" \
                              .format(field_nm)
                    break

        if err_msg:
            raise HeymacFrameError(err_msg)


class HeymacIeError(HeymacFrameError):
    pass


class HeymacIe(object):
    """Information Elements contain auxiliary frame data.

    The IE field of the Heymac frame contains:
    optionally zero or more Header IEs (hIE) and the hIE terminator
    followed by zero or more Payload IEs (pIE) and the pIE terminator.
    The hIE terminator is only REQUIRED if there are hIEs,
    but the pIE terminator is REQUIRED if there is at least one
    of any kind of IE.

    If MIC is enabled, both hIEs and pIEs are included in MIC calculations.
    If enciphering is enabled, enciphering does NOT include hIEs or
    the hIE terminator.  Enciphering begins at the first pIE if present.
    """
    SZ_MASK = 0b11_000000
    SZ_BIT0 = 0b00_000000
    SZ_BIT1 = 0b01_000000
    SZ_2B = 0b10_000000
    SZ_N = 0b11_000000  # the byte following IEctl contains the length

    TYPE_MASK = 0b00_111111
    TYPE_PIE = 0b00_100000  # Payload IE indicator

    # Header IEs (MSb of Type field is 0)
    TYPE_TERM_HIE = 0b00_000000
    TYPE_SQNC = 0b10_000001
    TYPE_CIPHER = 0b10_000010

    # Payload IEs (MSb of Type field is 1)
    TYPE_TERM_PIE = 0b00_000000
    TYPE_FRAG0 = 0b00_000001
    TYPE_FRAGN = 0b00_000010
    TYPE_MIC = 0b00_000011

    def __init__(self, ie_ctl, **kwargs):
        self._iectl = ie_ctl
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __bytes__(self):
        # This only works for SZ_BIT*.  Other sizes will need to override this.
        return struct.pack("B", self._iectl)

    def __len__(self):
        # FIXME: this doesn't handle IEs of SZ_N
        return 1 + self._get_sz(self._iectl)

    def _get_sz(self, ie_ctl):
        SZ = {HeymacIe.SZ_BIT0: 0,
              HeymacIe.SZ_BIT1: 0,
              HeymacIe.SZ_2B: 2,
              HeymacIe.SZ_N: -1}
        sz = SZ[ie_ctl & HeymacIe.SZ_MASK]
        if sz == -1:
            raise HeymacIeError("Sz byte absent")
        return sz

    @classmethod
    def parse(cls, ie_bytes):
        subcls = HeymacIeUnknown
        subclasses = list(HeymacHIe.__subclasses__())
        subclasses.extend(HeymacPIe.__subclasses__())
        for ie_cls in subclasses:
            if ie_cls._IECTL_VAL == ie_bytes[0]:
                subcls = ie_cls
                break
        return subcls.parse(ie_bytes)


class HeymacIeUnknown(HeymacIe):
    _IECTL_VAL = None


class HeymacHIe(HeymacIe):
    pass


class HeymacPIe(HeymacIe):
    pass


class HeymacHIeTerm(HeymacHIe):
    _IECTL_VAL = HeymacIe.SZ_BIT0 | HeymacIe.TYPE_TERM_HIE

    def __init__(self):
        super().__init__(self._IECTL_VAL)

    @staticmethod
    def parse(ie_bytes):
        return HeymacHIeTerm()


class HeymacHIeSqncNmbr(HeymacHIe):
    _IECTL_VAL = HeymacIe.SZ_2B | HeymacIe.TYPE_SQNC

    def __init__(self, sqnc_nmbr):
        super().__init__(self._IECTL_VAL, _sqnc_nmbr=sqnc_nmbr)

    def __bytes__(self):
        return struct.pack("!BH", self._iectl, self._sqnc_nmbr)

    @staticmethod
    def parse(ie_bytes):
        if len(ie_bytes) < 2:
            raise HeymacIeError("insufficient bytes for Sequence Number")
        return HeymacHIeSqncNmbr(struct.unpack("!H", ie_bytes[1:3])[0])


class HeymacHIeCipher(HeymacHIe):
    _IECTL_VAL = HeymacIe.SZ_2B | HeymacIe.TYPE_CIPHER

    def __init__(self, cipher_info):
        super().__init__(self._IECTL_VAL, _cipher_info=cipher_info)

    def __bytes__(self):
        return struct.pack("!BH", self._iectl, self._cipher_info)

    @staticmethod
    def parse(ie_bytes):
        return HeymacHIeCipher(struct.unpack("!H", ie_bytes[1:3])[0])


class HeymacPIeTerm(HeymacPIe):
    _IECTL_VAL = HeymacIe.SZ_BIT0 | HeymacIe.TYPE_TERM_PIE | HeymacIe.TYPE_PIE

    def __init__(self):
        super().__init__(self._IECTL_VAL)

    @staticmethod
    def parse(ie_bytes):
        return HeymacPIeTerm()


class HeymacPIeFrag0(HeymacPIe):
    _IECTL_VAL = HeymacIe.SZ_2B | HeymacIe.TYPE_FRAG0 | HeymacIe.TYPE_PIE

    def __init__(self, dgram_sz, dgram_tag):
        super().__init__(self._IECTL_VAL,
                         _dgram_sz=dgram_sz,
                         _dgram_tag=dgram_tag)

    def __bytes__(self):
        return struct.pack("!BH",
                           self._iectl,
                           (self._dgram_sz << 5) | self._dgram_tag)

    @staticmethod
    def parse(ie_bytes):
        data = struct.unpack("!H", ie_bytes[1:3])[0]
        dgram_sz = data >> 5
        dgram_tag = data & 0x1F
        return HeymacPIeFrag0(dgram_sz, dgram_tag)


class HeymacPIeFragN(HeymacPIe):
    _IECTL_VAL = HeymacIe.SZ_2B | HeymacIe.TYPE_FRAGN | HeymacIe.TYPE_PIE

    def __init__(self, dgram_offset, dgram_tag):
        super().__init__(self._IECTL_VAL,
                         _dgram_offset=dgram_offset,
                         _dgram_tag=dgram_tag)

    def __bytes__(self):
        return struct.pack("!BH",
                           self._iectl,
                           (self._dgram_offset << 5) | self._dgram_tag)

    @staticmethod
    def parse(ie_bytes):
        data = struct.unpack("!H", ie_bytes[1:3])[0]
        dgram_offset = data >> 5
        dgram_tag = data & 0x1F
        return HeymacPIeFragN(dgram_offset, dgram_tag)


class HeymacPIeMic(HeymacPIe):
    _IECTL_VAL = HeymacIe.SZ_2B | HeymacIe.TYPE_MIC | HeymacIe.TYPE_PIE

    def __init__(self, mic_algo, mic_sz):
        super().__init__(self._IECTL_VAL, _mic_algo=mic_algo, _mic_sz=mic_sz)

    def __bytes__(self):
        return struct.pack("!BH",
                           self._iectl,
                           (self._mic_algo << 8) | (self._mic_sz & 0x0F))

    @staticmethod
    def parse(ie_bytes):
        data = struct.unpack("!H", ie_bytes[1:3])[0]
        mic_algo = data >> 8
        mic_sz = data & 0x0F
        return HeymacPIeMic(mic_algo, mic_sz)


class HeymacIeSequence(object):
    def __init__(self, *ies):
        self._ies = ies

    def __bytes__(self):
        return b"".join(map(bytes, self._ies))

    def __iter__(self):
        return iter(self._ies)

    def __len__(self):
        """Returns the length in bytes of all IEs in the sequence"""
        return sum(map(len, self._ies))

    @staticmethod
    def parse(frame_bytes, offset=0):
        ies = []
        while True:
            ie = HeymacIe.parse(frame_bytes[offset:])
            ies.append(ie)
            offset += len(ie)
            if type(ie) is HeymacPIeTerm:
                break
        return HeymacIeSequence(*ies)

    # TODO: validate IEs
    # - they are in order (hIEs before pIEs)
    # - terminators exist in the right spot
