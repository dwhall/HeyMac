#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

APv6 (network layer) packet structure definition

This module defines the structure of the APv6 network layer packet.
An APv6 packet is created through an instance of APv6Packet()
with field_name=value as arguments to the constructor.
"""

import struct


class APv6PacketError(Exception):
    pass


class APv6Packet():
    """APv6 frame definition

    [Hdr, [Hops,] [SrcAddr,] [DstAddr,] [NxtHdr,] Payld]

    Hdr := Header

    =========   ======================================
    Bitfield    Description
    =========   ======================================
    110. ....   Prefix
    ...N ....   Next Header compressed?
    .... HL..   Hop Limit
    .... ..S.   Src Addr omit?
    .... ...D   Dst Addr omit?
    =========   ======================================

    N:
        0: Next Header is carried in-line
        1: Next Header is encoded via LOWPAN_NHC

    HL:
        0: Hop Limit is carried in-line
        1: Hop Limit is 1
        2: Hop Limit is 64
        3: Hop Limit is 255

    S:
        0: Src Addr is carried in-line
        1: Src Addr is omitted; computed from MAC layer

    D:
        0: Dest Addr is carried in-line
        1: Dest Addr is omitted; computed from MAC layer
    """

    IPHC_PREFIX_MASK = 0b11100000   # Packet prefix mask
    IPHC_PREFIX = 0b11000000        # Packet prefix value

    IPHC_NHC_MASK = 0b00010000          # Next Header Compressed mask
    IPHC_NHC_COMPRESSED = 0b00010000    # Next Header Compressed value

    IPHC_HLIM_MASK = 0b1100     # Hop limit
    IPHC_HLIM_INLINE = 0b0000   # HopLimit (1 Byte) follows IPHC
    IPHC_HLIM_1 = 0b0100
    IPHC_HLIM_64 = 0b1000
    IPHC_HLIM_255 = 0b1100

    IPHC_SAM_MASK = 0b10        # Src addr omit
    IPHC_SAM_INLINE = 0b00      # full 128-bit address is in-line
    IPHC_SAM_OMIT = 0b10        # address is omitted

    IPHC_DAM_MASK = 0b1         # Dst addr omit
    IPHC_DAM_INLINE = 0b0       # full 128-bit address is in-line
    IPHC_DAM_OMIT = 0b1         # address is omitted

    # Default values for the header of a new packet
    DEFAULT_PREFIX = IPHC_PREFIX
    DEFAULT_NHC = IPHC_NHC_COMPRESSED
    DEFAULT_HLIM = IPHC_HLIM_1
    DEFAULT_SAM = IPHC_SAM_OMIT
    DEFAULT_DAM = IPHC_DAM_OMIT

    FIELD_NAMES = ("hdr", "hops", "saddr", "daddr", "nhc", "payld")

    def __init__(self, **kwargs):
        """Creates an APv6 packet with the given fields"""
        self._hdr = (APv6Packet.DEFAULT_PREFIX
                     | APv6Packet.DEFAULT_NHC
                     | APv6Packet.DEFAULT_HLIM
                     | APv6Packet.DEFAULT_SAM
                     | APv6Packet.DEFAULT_DAM)
        self._hops = None
        self._saddr = None
        self._daddr = None
        self._nhc = None
        self._payld = None

        for k, v in kwargs.items():
            if k not in APv6Packet.FIELD_NAMES:
                raise APv6PacketError("Invalid field, {}".format(k))
            setattr(self, k, v)

    def __bytes__(self):
        """Returns the APv6Packet serialized into a bytes object."""
        # TODO: self._validate_hdr_and_fields()
        pkt = bytearray()
        pkt.append(self._hdr)
        if self._hops:
            pkt.append(self._hops)
        if self._saddr:
            pkt.extend(self._saddr)
        if self._daddr:
            pkt.extend(self._daddr)
        if self._payld:
            if type(self._payld) is not bytes:
                b = bytes(self._payld)
            else:
                b = self._payld
            pkt.extend(b)
        return bytes(pkt)

    @staticmethod
    def parse(pkt_bytes):
        """Parses the given pkt_bytes and returns an APv6Packet.

        Raises an APv6PacketError if some bits or fields
        are not set properly.
        """
        if max(pkt_bytes) > 255 or min(pkt_bytes) < 0:
            raise APv6PacketError("pkt_bytes must be a sequence of bytes")
        if len(pkt_bytes) < 1:
            raise APv6PacketError("pkt_bytes must have at least one byte")

        pkt = APv6Packet(hdr=pkt_bytes[0])
        offset = 1

        if pkt._is_hops_inline():
            pkt.hops = pkt_bytes[offset]
            offset += 1

        if pkt._is_src_inline():
            pkt.saddr = pkt_bytes[offset:offset + 16]
            offset += 16

        if pkt._is_dst_inline():
            pkt.daddr = pkt_bytes[offset:offset + 16]
            offset += 16

        payld = pkt_bytes[offset:]
        if len(payld) > 0:
            if ((payld[0] & UdpDatagram.UDPHC_PREFIX_MASK)
                    == UdpDatagram.UDPHC_PREFIX):
                pkt._payld = UdpDatagram.parse(payld)
            else:
                pkt._payld = payld

        return pkt

    @property
    def hdr(self):
        return struct.pack("B", self._hdr)

    @hdr.setter
    def hdr(self, val):
        # TODO validate
        self._hdr = val

    @property
    def hops(self):
        hops_idx = self._hdr & APv6Packet.IPHC_HLIM_MASK
        if hops_idx == APv6Packet.IPHC_HLIM_INLINE:
            h = self._hops
        else:
            h = {APv6Packet.IPHC_HLIM_1: 1,
                 APv6Packet.IPHC_HLIM_64: 64,
                 APv6Packet.IPHC_HLIM_255: 255}[hops_idx]
        return struct.pack("B", h)

    @hops.setter
    def hops(self, val):
        if type(val) is bytes:
            val = val[0]
        hlim = {1: APv6Packet.IPHC_HLIM_1,
                64: APv6Packet.IPHC_HLIM_64,
                255: APv6Packet.IPHC_HLIM_255}
        self._hdr &= ~APv6Packet.IPHC_HLIM_MASK
        if val in hlim.keys():
            self._hops = None
            self._hdr |= hlim[val]
        else:
            if val > 255:
                raise APv6PacketError("Hops value out of range")
            self._hops = val
            self._hdr |= APv6Packet.IPHC_HLIM_INLINE

    @property
    def saddr(self):
        return self._saddr

    @saddr.setter
    def saddr(self, val):
        assert len(val) == 16
        self._saddr = val
        self._hdr &= ~APv6Packet.IPHC_SAM_OMIT

    @property
    def daddr(self):
        return self._daddr

    @daddr.setter
    def daddr(self, val):
        assert len(val) == 16
        self._daddr = val
        self._hdr &= ~APv6Packet.IPHC_DAM_OMIT

    @property
    def payld(self):
        return self._payld

    @payld.setter
    def payld(self, val):
        self._payld = val

    def _is_hops_inline(self):
        return ((self._hdr & APv6Packet.IPHC_HLIM_MASK)
                == APv6Packet.IPHC_HLIM_INLINE)

    def _is_src_inline(self):
        return ((self._hdr & APv6Packet.IPHC_SAM_MASK)
                == APv6Packet.IPHC_SAM_INLINE)

    def _is_dst_inline(self):
        return ((self._hdr & APv6Packet.IPHC_DAM_MASK)
                == APv6Packet.IPHC_DAM_INLINE)


class UdpDatagramError(Exception):
    pass


class UdpDatagram():
    """UDP Datagram with header compression per RFC 6282.
    Always omits the checksum because the Physical layer has FEC and CRC"""

    UDPHC_PREFIX_MASK = 0b11111000
    UDPHC_PREFIX = 0b11110000

    _UDPHC_CS_OMIT = 0b00000100
    _UDPHC_PORTS_MASK = 0b00000011

    _UDPHC_PORT_MODE_SHORT = 1
    _UDPHC_PORT_MODE_BYTE = 2
    _UDPHC_PORT_MODE_NIBBLE = 3

    _UDPHC_PORTS_MODE_INLINE_INLINE = 0b00
    _UDPHC_PORTS_MODE_INLINE_BYTE = 0b01
    _UDPHC_PORTS_MODE_BYTE_INLINE = 0b10
    _UDPHC_PORTS_MODE_NIBBLE_NIBBLE = 0b11

    DEFAULT_PREFIX = UDPHC_PREFIX
    DEFAULT_CS_OMIT = _UDPHC_CS_OMIT
    DEFAULT_PORTS = 0

    _FIELD_NAMES = ("hdr", "src_port", "dst_port", "payld")

    def __init__(self, **kwargs):
        """Creates a UDP datagram with the given fields"""
        self._hdr = (UdpDatagram.DEFAULT_PREFIX
                     | UdpDatagram.DEFAULT_CS_OMIT
                     | UdpDatagram.DEFAULT_PORTS)
        self._src_port = None
        self._dst_port = None
        self._payld = None

        for k, v in kwargs.items():
            if k not in UdpDatagram._FIELD_NAMES:
                raise UdpDatagramError("Invalid field, {}".format(k))
            setattr(self, k, v)

    def __bytes__(self):
        """Returns the UDP Datagram serialized into a bytes object."""
        # port values may have changed, so must compress the ports
        # which update the port mode, before we serialize the hdr
        ports = self._compress_ports()
        dgram = bytearray()
        dgram.append(self._hdr)
        dgram.extend(ports)
        if self._payld:
            dgram.extend(self._payld)
        return bytes(dgram)

    def _compress_ports(self):
        """Returns serialized representation of compressed ports"""
        if self._src_port is None:
            raise UdpDatagramError("Source port not given")
        if self._dst_port is None:
            raise UdpDatagramError("Destination port not given")

        ports = bytearray()
        src_mode = self._get_port_mode(self._src_port)
        dst_mode = self._get_port_mode(self._dst_port)
        if (src_mode == UdpDatagram._UDPHC_PORT_MODE_NIBBLE
                and dst_mode == UdpDatagram._UDPHC_PORT_MODE_NIBBLE):
            mode_bits = UdpDatagram._UDPHC_PORTS_MODE_NIBBLE_NIBBLE
            ports.append((self._src_port & 0x0F) << 4
                         | (self._dst_port & 0x0F))
        elif (src_mode == UdpDatagram._UDPHC_PORT_MODE_BYTE
                or src_mode == UdpDatagram._UDPHC_PORT_MODE_NIBBLE):
            mode_bits = UdpDatagram._UDPHC_PORTS_MODE_BYTE_INLINE
            ports.append(self._src_port & 0xFF)
            ports.extend(self.dst_port)
        elif (dst_mode == UdpDatagram._UDPHC_PORT_MODE_BYTE
                or dst_mode == UdpDatagram._UDPHC_PORT_MODE_NIBBLE):
            mode_bits = UdpDatagram._UDPHC_PORTS_MODE_INLINE_BYTE
            ports.extend(self.src_port)
            ports.append(self._dst_port & 0xFF)
        else:
            mode_bits = UdpDatagram._UDPHC_PORTS_MODE_INLINE_INLINE
            ports.extend(self.src_port)
            ports.extend(self.dst_port)

        self._hdr &= ~UdpDatagram._UDPHC_PORTS_MASK
        self._hdr |= mode_bits

        return bytes(ports)

    @classmethod
    def _get_port_mode(cls, port):
        if port & 0xFFF0 == 0xF0B0:
            mode = cls._UDPHC_PORT_MODE_NIBBLE
        elif port & 0xFF00 == 0xF000:
            mode = cls._UDPHC_PORT_MODE_BYTE
        else:
            mode = cls._UDPHC_PORT_MODE_SHORT
        return mode

    @staticmethod
    def parse(dgram_bytes):
        """Parses the given dgram_bytes and returns a UdpDatagram."""
        if len(dgram_bytes) < 1:
            raise UdpDatagramError("Insufficient bytes for header")

        dgram = UdpDatagram()
        dgram._hdr = dgram_bytes[0]
        offset = 1

        if ((dgram._hdr & UdpDatagram.UDPHC_PREFIX_MASK)
                != UdpDatagram.DEFAULT_PREFIX):
            raise UdpDatagramError("Header prefix mismatch")
        if ((dgram._hdr & UdpDatagram._UDPHC_CS_OMIT)
                != UdpDatagram.DEFAULT_CS_OMIT):
            raise UdpDatagramError("Header CS-omit mismatch")

        port_mode = dgram._hdr & UdpDatagram._UDPHC_PORTS_MASK
        if port_mode == UdpDatagram._UDPHC_PORTS_MODE_NIBBLE_NIBBLE:
            if len(dgram_bytes) < 2:
                raise UdpDatagramError("Insufficient bytes for ports")
            ports = dgram_bytes[offset]
            offset += 1
            dgram._src_port = 0xF0B0 | ((ports >> 4) & 0x0F)
            dgram._dst_port = 0xF0B0 | (ports & 0x0F)
        elif port_mode == UdpDatagram._UDPHC_PORTS_MODE_BYTE_INLINE:
            if len(dgram_bytes) < 4:
                raise UdpDatagramError("Insufficient bytes for ports")
            dgram._src_port = 0xF000 | dgram_bytes[offset]
            offset += 1
            dgram.dst_port = dgram_bytes[offset:offset + 2]
            offset += 2
        elif port_mode == UdpDatagram._UDPHC_PORTS_MODE_INLINE_BYTE:
            if len(dgram_bytes) < 4:
                raise UdpDatagramError("Insufficient bytes for ports")
            dgram.src_port = dgram_bytes[offset:offset + 2]
            offset += 2
            dgram._dst_port = 0xF000 | dgram_bytes[offset]
            offset += 1
        else:
            if len(dgram_bytes) < 5:
                raise UdpDatagramError("Insufficient bytes for ports")
            dgram.src_port = dgram_bytes[offset:offset + 2]
            offset += 2
            dgram.dst_port = dgram_bytes[offset:offset + 2]
            offset += 2
        dgram.payld = dgram_bytes[offset:]

        return dgram

    # Getters should return external representation type, bytes
    # Setters should accept int or bytes and save internal working type, int
    @property
    def hdr(self):
        return struct.pack("B", self._hdr)

    @property
    def src_port(self):
        return struct.pack("!H", self._src_port)

    @src_port.setter
    def src_port(self, val):
        if type(val) is bytes:
            self._src_port = struct.unpack("!H", val)[0]
        else:
            self._src_port = val

    @property
    def dst_port(self):
        return struct.pack("!H", self._dst_port)

    @dst_port.setter
    def dst_port(self, val):
        if type(val) is bytes:
            self._dst_port = struct.unpack("!H", val)[0]
        else:
            self._dst_port = val

    @property
    def payld(self):
        return self._payld

    @payld.setter
    def payld(self, val):
        self._payld = val
