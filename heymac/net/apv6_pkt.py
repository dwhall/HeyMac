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


class APv6Packet(object):
    """APv6 frame definition

    [Hdr,Hops,SrcAddr,DstAddr,NxtHdr,Payld]

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
        1: Src Addr is elided; computed from MAC layer

    D:
        0: Dest Addr is carried in-line
        1: Dest Addr is elided; computed from MAC layer
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
    IPHC_SAM_OMIT = 0b10        # address is elided

    IPHC_DAM_MASK = 0b1         # Dst addr omit
    IPHC_DAM_INLINE = 0b0       # full 128-bit address is in-line
    IPHC_DAM_OMIT = 0b1         # address is elided

    # Default values for the header of a new packet
    DEFAULT_PREFIX = IPHC_PREFIX
    DEFAULT_NHC = IPHC_NHC_COMPRESSED
    DEFAULT_HLIM = IPHC_HLIM_1
    DEFAULT_SAM = IPHC_SAM_OMIT
    DEFAULT_DAM = IPHC_DAM_OMIT

    FIELD_NAMES = ("hdr", "hops", "saddr", "daddr", "nhc", "payld")

    def __init__(self, **kwargs):
        """Creates an APv6 packet with the given fields"""
        self._hdr = (
            APv6Packet.DEFAULT_PREFIX
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
        """Returns the APv6Packet serialized into a bytes object"""
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

        # TODO: parse payld
        pkt.payld = pkt_bytes[offset:]

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
            h = {
                APv6Packet.IPHC_HLIM_1 : 1,
                APv6Packet.IPHC_HLIM_64 : 64,
                APv6Packet.IPHC_HLIM_255 : 255}[hops_idx]
        return struct.pack("B", h)

    @hops.setter
    def hops(self, val):
        if type(val) is bytes:
            val = val[0]
        hlim = {
            1: APv6Packet.IPHC_HLIM_1,
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


class UdpDatagram(object):
    """UDP Datagram with header compression per RFC 6282.
    Always omits the checksum because the Physical layer has FEC and CRC"""

    UDPHC_PREFIX_MASK = 0b11111000
    UDPHC_PREFIX = 0b11110000

    UDPHC_CS_OMIT = 0b00000100

    _UDPHC_PORT_MODE_SHORT = 1
    _UDPHC_PORT_MODE_BYTE = 2
    _UDPHC_PORT_MODE_NIBBLE = 3

    _UDPHC_PORTS_MODE_INLINE_INLINE = 0b00
    _UDPHC_PORTS_MODE_INLINE_BYTE = 0b01
    _UDPHC_PORTS_MODE_BYTE_INLINE = 0b10
    _UDPHC_PORTS_MODE_NIBBLE_NIBBLE = 0b11

    def __init__(self, **kwargs):
        """Creates a UDP datagram with the given fields"""
        port = kwargs.get("src_port", b"")
        if type(port) is int:
            port = struct.pack("!H", port)
        self._src_port = port
        port = kwargs.get("dst_port", b"")
        if type(port) is int:
            port = struct.pack("!H", port)
        self._dst_port = port
        self._data = kwargs.get("data", b"")
        self._hdr = kwargs.get("hdr", self._build_hdr())

    def _build_hdr(self):
        mode_bits = self._get_ports_mode()
        return UdpDatagram.UDPHC_PREFIX | UdpDatagram.UDPHC_CS_OMIT | mode_bits

    def _get_ports_mode(self):
        try:
            src_int = struct.unpack("!H", self._src_port)[0]
            dst_int = struct.unpack("!H", self._dst_port)[0]
        except struct.error:
            raise UdpDatagramError("Insufficient data")

        src_mode = self._eval_port_addr(src_int)
        dst_mode = self._eval_port_addr(dst_int)

        if src_mode == UdpDatagram._UDPHC_PORT_MODE_NIBBLE \
                and dst_mode == UdpDatagram._UDPHC_PORT_MODE_NIBBLE:
            mode_bits = UdpDatagram._UDPHC_PORTS_MODE_NIBBLE_NIBBLE
        elif src_mode == UdpDatagram._UDPHC_PORT_MODE_BYTE or \
                src_mode == UdpDatagram._UDPHC_PORT_MODE_NIBBLE:
            mode_bits = UdpDatagram._UDPHC_PORTS_MODE_BYTE_INLINE
        elif dst_mode == UdpDatagram._UDPHC_PORT_MODE_BYTE or \
                dst_mode == UdpDatagram._UDPHC_PORT_MODE_NIBBLE:
            mode_bits = UdpDatagram._UDPHC_PORTS_MODE_INLINE_BYTE
        else:
            mode_bits = UdpDatagram._UDPHC_PORTS_MODE_INLINE_INLINE
        return mode_bits

    def __bytes__(self):
        """Returns the UDP Datagram serialized into a bytes object."""
        dgram = bytearray()
        dgram.append(self._hdr)
        self._compress_ports(dgram)
        dgram.extend(self._data)
        return bytes(dgram)

    def _compress_ports(self, dgram):
        mode_bits = self._get_ports_mode()

        src_int = struct.unpack("!H", self._src_port)[0]
        dst_int = struct.unpack("!H", self._dst_port)[0]

        if mode_bits == UdpDatagram._UDPHC_PORTS_MODE_NIBBLE_NIBBLE:
            dgram.append((src_int & 0x0F) << 4 | (dst_int & 0x0F))
        elif mode_bits == UdpDatagram._UDPHC_PORTS_MODE_BYTE_INLINE:
            dgram.append(src_int & 0xFF)
            dgram.extend(self._dst_port)
        elif mode_bits == UdpDatagram._UDPHC_PORTS_MODE_INLINE_BYTE:
            dgram.extend(self._src_port)
            dgram.append(dst_int & 0xFF)
        else:
            dgram.extend(self._src_port)
            dgram.extend(self._dst_port)
        dgram[0] |= mode_bits

    @classmethod
    def _eval_port_addr(cls, addr):
        if addr & 0xFFF0 == 0xF0B0:
            mode = cls._UDPHC_PORT_MODE_NIBBLE
        elif addr & 0xFF00 == 0xF000:
            mode = cls._UDPHC_PORT_MODE_BYTE
        else:
            mode = cls._UDPHC_PORT_MODE_SHORT
        return mode

    @staticmethod
    def parse(dgram_bytes):
        """Parses the given dgram_bytes and returns a UdpDatagram."""
        if len(dgram_bytes) < 1:
            raise UdpDatagramError("Insufficient bytes for header")
        hdr = dgram_bytes[0:1]
        hdr_int = dgram_bytes[0]
        offset = 1

        if hdr_int & UdpDatagram.UDPHC_PREFIX_MASK != UdpDatagram.UDPHC_PREFIX:
            raise UdpDatagramError("Header prefix mismatch")
        if hdr_int & UdpDatagram.UDPHC_CS_OMIT != UdpDatagram.UDPHC_CS_OMIT:
            raise UdpDatagramError("Header CS-omit mismatch")
        port_mode = hdr_int & 0b11
        if port_mode == UdpDatagram._UDPHC_PORTS_MODE_NIBBLE_NIBBLE:
            if len(dgram_bytes) < 2:
                raise UdpDatagramError("Insufficient bytes for ports")
            ports = dgram_bytes[offset]
            offset + 1
            src_port = 0xF0B0 | ((ports >> 4) & 0x0F)
            dst_port = 0xF0B0 | (ports & 0x0F)
        elif port_mode == UdpDatagram._UDPHC_PORTS_MODE_BYTE_INLINE:
            if len(dgram_bytes) < 4:
                raise UdpDatagramError("Insufficient bytes for ports")
            src_port = struct.pack("!H", 0xF000 | dgram_bytes[offset])
            offset += 1
            dst_port = dgram_bytes[offset:offset + 2]
            offset += 2
        elif port_mode == UdpDatagram._UDPHC_PORTS_MODE_INLINE_BYTE:
            if len(dgram_bytes) < 4:
                raise UdpDatagramError("Insufficient bytes for ports")
            src_port = dgram_bytes[offset:offset + 2]
            offset += 2
            dst_port = struct.pack("!H", 0xF000 | dgram_bytes[offset])
            offset += 1
        else:
            if len(dgram_bytes) < 5:
                raise UdpDatagramError("Insufficient bytes for ports")
            src_port = dgram_bytes[offset:offset + 2]
            offset += 2
            dst_port = dgram_bytes[offset:offset + 2]
            offset += 2
        data = dgram_bytes[offset:]

        return UdpDatagram(
            hdr=hdr,
            src_port=src_port,
            dst_port=dst_port,
            data=data)

    @property
    def hdr(self):
        return self._hdr

    @property
    def src_port(self):
        return self._src_port

    @property
    def dst_port(self):
        return self._dst_port

    @property
    def data(self):
        return self._data
