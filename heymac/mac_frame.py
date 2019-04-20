"""
Copyright 2018 Dean Hall.  See LICENSE file for details.

HeyMac Frame structure definition
and methods to get/set frame fields.

This file requires the excellent third-party module 'dpkt'
which may be installed via::

    pip3 install dpkt

or::

    pip install dpkt
"""


import logging

import dpkt # pip install dpkt

from .mac_cmds import *
from .net_frame import APv6Frame


# HeyMac protocol version
HEYMAC_VERSION = 2


class HeyMacFrame(dpkt.Packet):
    """HeyMac frame definition
    """
    # HeyMac Protocol IDs
    PV_PID_HEYMAC = 0b1110
    PV_PID_HEYMAC_FLOOD = 0b1111
    PV_PID_MASK = 0b11110000
    PV_PID_SHIFT = 4
    PV_VER_HEYMAC2 = HEYMAC_VERSION
    PV_VER_MASK = 0b00001111
    PV_VER_SHIFT = 0

    # Frame Control Field (Fctl) subfield values
    FCTL_TYPE_MIN = 0b00
    FCTL_TYPE_MAC = 0b01
    FCTL_TYPE_NET = 0b10
    FCTL_TYPE_EXT = 0b11
    FCTL_TYPE_MASK = 0b11000000
    FCTL_TYPE_SHIFT = 6
    FCTL_L_SHIFT = 5
    FCTL_P_SHIFT = 4
    FCTL_N_SHIFT = 3
    FCTL_D_SHIFT = 2
    FCTL_I_SHIFT = 1
    FCTL_S_SHIFT = 0

    __byte_order__ = '!' # Network order
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .pv_pid, .pv_ver instead.
        ('_pv', 'B',
            PV_PID_HEYMAC << PV_PID_SHIFT |
            PV_VER_HEYMAC2 << PV_VER_SHIFT),
        # Access properties .fctl, .fctl_type, .fctl_l, etc. instead.
        ('_fctl', 'B', FCTL_TYPE_MAC << FCTL_TYPE_SHIFT),
        # The fields above are guaranteed to be present.
        # Below this are optional fields as indicated by '0s'.
        ('exttype', '0s', b''),
        ('netid', '0s', b''),
        ('daddr', '0s', b''),
        ('hie', '0s', b''),
        ('bie', '0s', b''),
        ('saddr', '0s', b''),
    )

    # Functions to help determine which fields are present
    def _has_exttype_field(self,): # ExtType exists when Fctl type is Extended
        return self.fctl_type == HeyMacFrame.FCTL_TYPE_EXT
    def _has_netid_field(self,):
        return self.fctl_n != 0
    def _has_daddr_field(self,):
        return self.fctl_d != 0
    def _has_ie_field(self,):
        return self.fctl_i != 0
    def _has_saddr_field(self,):
        return self.fctl_s != 0

    # Functions to determine size of variable-size fields
    def _sizeof_saddr_field(self,):
        if self._has_saddr_field():
            if self.fctl_l != 0:
                sz = 8
            else:
                sz = 2
        else:
            sz = 0
        return sz

    def _sizeof_daddr_field(self,):
        if self._has_daddr_field():
            if self.fctl_l != 0:
                sz = 8
            else:
                sz = 2
        else:
            sz = 0
        return sz

    def _sizeof_ie_fields(self,):
        """Returns the sizes of the hIE and bIE fields
        as a tuple (size_of_hIE, size_of_bIE).
        These sizes are variable from one packet to another
        but are fixed for a given packet and are calculated by
        parsing the contents of the hIE and bIE fields.
        """
        # FIXME
        return (0,0)


    # Getters for the _pv field
    @property
    def pv(self,):
        """Gets the full value (all bits) from the PID-Ver field.
        """
        return self._pv

    @property
    def pv_pid(self,):
        """Gets the Protocol ID value from the PID-Ver field.
        """
        return ((self._pv & HeyMacFrame.PV_PID_MASK) >> HeyMacFrame.PV_PID_SHIFT)

    @property
    def pv_ver(self,):
        """Gets the Protocol version value from the PID-Ver field.
        """
        return ((self._pv & HeyMacFrame.PV_VER_MASK) >> HeyMacFrame.PV_VER_SHIFT)

    # Setters for the _pv field
    @pv.setter
    def pv(self, val):
        """Sets the full value (all bits) in the PID-Ver field.
        """
        self._pv = val

    @pv_pid.setter
    def pv_pid(self, val):
        """Sets the Protocol ID value in the PID-Ver field.
        """
        assert val in (HeyMacFrame.PV_PID_HEYMAC, HeyMacFrame.PV_PID_HEYMAC_FLOOD)
        self._pv = (self._pv & ~HeyMacFrame.PV_PID_MASK) | (val << HeyMacFrame.PV_PID_SHIFT)

    @pv_ver.setter
    def pv_ver(self, val):
        """Sets the Protocol Version value in the PID-Ver field.
        """
        assert val <= (HeyMacFrame.PV_VER_MASK >> HeyMacFrame.PV_VER_SHIFT)
        self._pv = (self._pv & ~HeyMacFrame.PV_VER_MASK) | (val << HeyMacFrame.PV_VER_SHIFT)

    # Getters for the _fctl field
    @property
    def fctl(self,):
        """Gets the full value (all bits) from the Fctl field.
        """
        return self._fctl

    @property
    def fctl_type(self,):
        """Gets the frame type value from the Fctl field.
        """
        return ((self._fctl & HeyMacFrame.FCTL_TYPE_MASK) >> HeyMacFrame.FCTL_TYPE_SHIFT)

    @property
    def fctl_l(self,):
        """Gets the Long address flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_L_SHIFT)

    @property
    def fctl_p(self,):
        """Gets the Pending frames flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_P_SHIFT)

    @property
    def fctl_n(self,):
        """Gets the NetID present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_N_SHIFT)

    @property
    def fctl_d(self,):
        """Gets the Dest address present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_D_SHIFT)

    @property
    def fctl_i(self,):
        """Gets the IE present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_I_SHIFT)

    @property
    def fctl_s(self,):
        """Gets the Src address present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_S_SHIFT)


    # Setters for the _fctl field
    @fctl.setter
    def fctl(self, val):
        """Sets the full value (all bits) in the Fctl field.
        """
        self._fctl = val

    @fctl_type.setter
    def fctl_type(self, val):
        """Sets the frame type value in the Fctl field.
        """
        assert val <= 3, "Invalid frame type"
        self._fctl = (self._fctl & ~HeyMacFrame.FCTL_TYPE_MASK) | (val << HeyMacFrame.FCTL_TYPE_SHIFT)

    def _fctl_setter_for_bit(self, val, bit_idx):
        """Sets or clears one of the L,R,N,D,I,S bits
        without modifying the Type bits.
        """
        assert 0 <= val <= 1
        assert 0 <= bit_idx <= 7
        self._fctl &= (HeyMacFrame.FCTL_TYPE_MASK | ~(1 << bit_idx))
        self._fctl |= (val << bit_idx)

    @fctl_l.setter
    def fctl_l(self, val):
        """Sets the Long address flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_L_SHIFT)

    @fctl_p.setter
    def fctl_p(self, val):
        """Sets the Pending frames flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_P_SHIFT)

    @fctl_n.setter
    def fctl_n(self, val):
        """Sets the NetID present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_N_SHIFT)

    @fctl_d.setter
    def fctl_d(self, val):
        """Sets the Dest address present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_D_SHIFT)

    @fctl_i.setter
    def fctl_i(self, val):
        """Sets the IEs present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_I_SHIFT)

    @fctl_s.setter
    def fctl_s(self, val):
        """Sets the Source address present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_S_SHIFT)


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        super().unpack(buf)

        # validate the PID-Ver
        if self.pv_pid not in (HeyMacFrame.PV_PID_HEYMAC, HeyMacFrame.PV_PID_HEYMAC_FLOOD):
            raise dpkt.UnpackError()
        if self.pv_ver != HeyMacFrame.PV_VER_HEYMAC2:
            raise dpkt.UnpackError()

        # the Fctl field can be every bit-combination
        # so there's no illegal value; no way to validate

        # all fields after Fctl are optional (defined as '0s')
        # so we conditionally pull them from the .data bytearray

        if self._has_exttype_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for exttype")
            self.exttype = self.data[0]
            self.data = self.data[1:]

        if self._has_netid_field():
            if len(self.data) < 2:
                raise dpkt.NeedData("for netid")
            self.netid = self.data[0:2]
            self.data = self.data[2:]

        if self._has_daddr_field():
            sz = self._sizeof_daddr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for daddr")
            self.daddr = self.data[0:sz]
            self.data = self.data[sz:]

        if self._has_ie_field():
            sz_hie, sz_bie = self._sizeof_ie_fields()
            if len(self.data) < sz_hie + sz_bie:
                raise dpkt.NeedData("for IEs")
            self.hie = self.data[0:sz_hie]
            self.bie = self.data[sz_hie:sz_hie + sz_bie]
            self.data = self.data[sz_hie + sz_bie:]

        if self._has_saddr_field():
            sz = self._sizeof_saddr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for saddr")
            self.saddr = self.data[0:sz]
            self.data = self.data[sz:]

        # Unpack the payload for known frame types
        if self.fctl_type == HeyMacFrame.FCTL_TYPE_MAC:
            if self.data:
                if self.data[0] == HeyMacCmdId.SBCN.value:
                    self.data = HeyMacCmdSbcn(self.data)
                elif self.data[0] == HeyMacCmdId.EBCN.value:
                    self.data = HeyMacCmdEbcn(self.data)
                elif self.data[0] == HeyMacCmdId.TXT.value:
                    self.data = HeyMacCmdTxt(self.data)
                else:
                    logging.info("unsupported MAC cmd %f", self.data[0])
            # else:
            #     raise dpkt.NeedData("for MAC payld")
        elif self.fctl_type == HeyMacFrame.FCTL_TYPE_NET:
            if self.data:
                self.data = APv6Frame(self.data)
            # else:
            #     raise dpkt.NeedData("expected APv6 data")


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of HeyMacFrame.
        """
        d = bytearray()

        # Skip PID-Ver and Fctl fields for now,
        # insert them at the end of this function

        if self._has_exttype_field() and not self.exttype:
            self.exttype = b'\x00'
        if self.exttype or self._has_exttype_field():
            self.fctl_type = HeyMacFrame.FCTL_TYPE_EXT
            if type(self.exttype) is bytes:
                v = self.exttype[0]
            else:
                v = self.exttype
                self.exttype = struct.pack("B", v)
            d.append(v)

        if self.netid:
            self.fctl_n = 1
            if type(self.netid) is int:
                self.netid = struct.pack("!H", self.netid)
            assert len(self.netid) == 2
            d.extend(self.netid)

        if self.daddr:
            if type(self.daddr) is int:
                self.daddr = struct.pack("!H", self.daddr)
            len_daddr = len(self.daddr)
            if len_daddr == 8:
                self.fctl_l = 1
                self.fctl_d = 1
            elif len_daddr == 2:
                self.fctl_d = 1
            d.extend(self.daddr)

        # TODO: add IEs

        if self.saddr:
            if type(self.saddr) is int:
                self.saddr = struct.pack("!H", self.saddr)
            len_saddr = len(self.saddr)
            if len_saddr == 8:
                self.fctl_l = 1
                self.fctl_s = 1
            elif len_saddr == 2:
                self.fctl_s = 1
            d.extend(self.saddr)

        # Inserts PID-Ver and Fctl,
        # returns the combined bytes object
        return super().pack_hdr() + bytes(d)


class HeyMacFloodFrame(HeyMacFrame):
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .pv_pid, .pv_ver instead.
        ('_pv', 'B',
            HeyMacFrame.PV_PID_HEYMAC_FLOOD << HeyMacFrame.PV_PID_SHIFT |
            HeyMacFrame.PV_VER_HEYMAC2 << HeyMacFrame.PV_VER_SHIFT),
        # Access properties .fctl, .fctl_type, .fctl_l, etc. instead.
        ('_fctl', 'B', HeyMacFrame.FCTL_TYPE_MAC << HeyMacFrame.FCTL_TYPE_SHIFT),
        # The fields above are guaranteed to be present.
        # Below this are optional fields as indicated by '0s'.
        ('exttype', '0s', b''),
        ('netid', '0s', b''),
        ('daddr', '0s', b''),
        ('hie', '0s', b''),
        ('bie', '0s', b''),
        ('saddr', '0s', b''),
    )
