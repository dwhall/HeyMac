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

    IPHC_PREFIX_MASK = 0b11100000
    IPHC_NHC_MASK = 0b00010000
    IPHC_HLIM_MASK = 0b00001100
    IPHC_SAM_MASK = 0b00000010
    IPHC_DAM_MASK = 0b00000001

    IPHC_PREFIX_SHIFT = 5
    IPHC_NHC_SHIFT = 4
    IPHC_HLIM_SHIFT = 2
    IPHC_SAM_SHIFT = 1
    IPHC_DAM_SHIFT = 0

    IPHC_PREFIX = 0b110

    IPHC_HLIM_INLINE = 0b00     # HopLimit (1 Byte) follows IPHC
    IPHC_HLIM_1 = 0b01
    IPHC_HLIM_64 = 0b10
    IPHC_HLIM_255 = 0b11

    IPHC_ADDR_MODE_128 = 0  # full 128-bit address is in-line
    IPHC_ADDR_MODE_0 = 1    # address is elided

    APV6_PREFIX = IPHC_PREFIX << IPHC_PREFIX_SHIFT

    DEFAULT_NHC = 0b1   # next-header is compressed
    DEFAULT_HLIM = IPHC_HLIM_1  # 1 hop
    DEFAULT_SAM = IPHC_ADDR_MODE_0  # address compressed/elided
    DEFAULT_DAM = IPHC_ADDR_MODE_0  # address compressed/elided

    # Packet field names
    FLD_HDR = "hdr"         # Header
    FLD_HOPS = "hops"       # Hop count
    FLD_SADDR = "saddr"     # Source address
    FLD_DADDR = "daddr"     # Destination address
    FLD_NHC = "nhc"         # Next Header Compressed
    FLD_PAYLD = "payld"     # Payload (net layer)


    def __init__(self, **kwargs):
        """Creates an APv6 packet with the given fields"""
        built_hdr = self._build_hdr(kwargs)
        self._validate_args(kwargs, built_hdr)
        self._hdr = built_hdr
        self._hops = kwargs.get("hops", b"")
        self._saddr = kwargs.get("saddr", b"")
        self._daddr = kwargs.get("daddr", b"")
        self._nhc = kwargs.get("nhc", b"")
        self._hops = kwargs.get("hops", b"")
        self._payld = kwargs.get("payld", b"")

    def _validate_args(self, kwargs, built_hdr):
        pkt_field_names = (
            APv6Packet.FLD_HDR,
            APv6Packet.FLD_HOPS,
            APv6Packet.FLD_SADDR,
            APv6Packet.FLD_DADDR,
            APv6Packet.FLD_NHC,
            APv6Packet.FLD_PAYLD)
        for field_name in kwargs:
            if field_name not in pkt_field_names:
                raise APv6PacketError(f"Invalid field: {field_name}")
        if APv6Packet.FLD_HDR in kwargs:
            if kwargs["hdr"] != built_hdr[0]:
                raise APv6PacketError("Header doesn't match given fields")

    def _build_hdr(self, kwargs):
        built_hdr = kwargs.get(
            APv6Packet.FLD_HDR,
            APv6Packet.IPHC_PREFIX << APv6Packet.IPHC_PREFIX_SHIFT)
        if APv6Packet.FLD_HOPS not in kwargs:
            built_hdr |= APv6Packet.DEFAULT_HLIM << APv6Packet.IPHC_HLIM_SHIFT
        if APv6Packet.FLD_SADDR not in kwargs:
            built_hdr |= APv6Packet.DEFAULT_SAM << APv6Packet.IPHC_SAM_SHIFT
        if APv6Packet.FLD_DADDR not in kwargs:
            built_hdr |= APv6Packet.DEFAULT_DAM << APv6Packet.IPHC_DAM_SHIFT
        if APv6Packet.FLD_NHC not in kwargs:
            built_hdr |= APv6Packet.DEFAULT_NHC << APv6Packet.IPHC_NHC_SHIFT
        return bytes([built_hdr])


    def __bytes__(self):
        """Returns the APv6Packet serialized into a bytes object

        Raises an APv6PacketError if some bits or fields
        are not set properly.
        """
#        self._validate_hdr_and_fields()

        pkt = bytearray()
        pkt.extend(self._hdr)
        if self._has_hops_field():
            pkt.extend(self._hops)
        if self._has_src_field():
            pkt.extend(self._saddr)
        if self._has_dst_field():
            pkt.extend(self._daddr)
        pkt.extend(self._payld)
        return bytes(pkt)

    def _has_hops_field(self):
        return ((self._hdr[0] & APv6Packet.IPHC_HLIM_MASK)
                >> APv6Packet.IPHC_HLIM_SHIFT) == APv6Packet.IPHC_HLIM_INLINE

    def _has_src_field(self):
        return ((self._hdr[0] & APv6Packet.IPHC_SAM_MASK)
                >> APv6Packet.IPHC_SAM_SHIFT) == APv6Packet.IPHC_ADDR_MODE_128

    def _has_dst_field(self):
        return ((self._hdr[0] & APv6Packet.IPHC_DAM_MASK)
                >> APv6Packet.IPHC_DAM_SHIFT) == APv6Packet.IPHC_ADDR_MODE_128

    @staticmethod
    def parse(pkt_bytes):
        """Parses the given pkt_bytes and returns an APv6Packet

        Raises an APv6PacketError if some bits or fields
        are not set properly.
        """
        try:
            if max(pkt_bytes) > 255 or min(pkt_bytes) < 0:
                raise APv6PacketError("pkt_bytes must be a sequence of bytes")
        except ValueError:
            raise APv6PacketError("pkt_bytes must have at least one byte")

        hdr = pkt_bytes[0]
        offset = 1
        hdr_prefix = (hdr & APv6Packet.IPHC_PREFIX_MASK) \
            >> APv6Packet.IPHC_PREFIX_SHIFT
        hdr_nhc = (hdr & APv6Packet.IPHC_NHC_MASK) \
            >> APv6Packet.IPHC_NHC_SHIFT
        hdr_hlim = (hdr & APv6Packet.IPHC_HLIM_MASK) \
            >> APv6Packet.IPHC_HLIM_SHIFT
        hdr_sam = (hdr & APv6Packet.IPHC_SAM_MASK) \
            >> APv6Packet.IPHC_SAM_SHIFT
        hdr_dam = (hdr & APv6Packet.IPHC_DAM_MASK) \
            >> APv6Packet.IPHC_DAM_SHIFT

        if hdr_prefix != APv6Packet.IPHC_PREFIX:
            raise APv6PacketError("Incorrect header prefix")

        if hdr_hlim == APv6Packet.IPHC_HLIM_INLINE:
            if len(pkt_bytes) < 2:
                raise APv6PacketError("Insufficient bytes for Hops")
            hops = pkt_bytes[offset]
            offset += 1
        else:
            hops = (None, 1, 64, 255)[hdr_hlim]

        if hdr_sam == APv6Packet.IPHC_ADDR_MODE_128:
            if len(pkt_bytes) < offset + 16:
                raise APv6PacketError("Insufficient bytes for Saddr")
            saddr = pkt_bytes[offset:offset + 16]
            offset += 16
        else:
            saddr = b""

        if hdr_dam == APv6Packet.IPHC_ADDR_MODE_128:
            if len(pkt_bytes) < offset + 16:
                raise APv6PacketError("Insufficient bytes for Daddr")
            daddr = pkt_bytes[offset:offset + 16]
            offset += 16
        else:
            daddr = b""

        # FIXME: NxtHdr
        if hdr_nhc:
            nhc = b""
        else:
            nhc = b""

        payld = pkt_bytes[offset:]

        return APv6Packet(
            hdr=hdr,
            hops=hops,
            saddr=saddr,
            daddr=daddr,
            nhc=nhc,
            payld=payld)

    @property
    def hdr(self):
        return self._hdr

    @property
    def hops(self):
        return self._hops

    @property
    def saddr(self):
        return self._saddr

    @property
    def daddr(self):
        return self._daddr

    @property
    def payld(self):
        return self._payld


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
